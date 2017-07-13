#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
from common import TA_ROOT
from common import REVIEW_PER_PAGE
import time
from bs4 import BeautifulSoup
import math
import re
import threading
import queue
import requests
import ast
import logging
from tadb import taDB

logger = logging.getLogger()
lock = threading.Lock()


def find_review_ids(hid, url):
    def calc_max_page(soup):
        return math.ceil(find_num_review(soup) / REVIEW_PER_PAGE)

    def find_num_review(soup):
        div = soup.find('a', class_='more taLnk')
        return 0 if div is None else int(re.sub('\D', '', div.text))

    def match_review_ids(page_source):
        return list(set(
            re.findall('(?<=review_)\d+', page_source)
        ))

    def find_max_page(soup):
        div = soup.find('div', class_='pageNumbers')
        if div is None:
            return 1 if match_review_ids(soup) else 0
        else:
            num = div.find_all('a')[-1]
            return int(num['data-offset']) / REVIEW_PER_PAGE + 1

    session = requests.Session()
    paras = {'filterLang': 'ALL'}
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    session.post(url, data=paras, headers=headers)
    response = session.get(url)
    response_soup = BeautifulSoup(response.text, 'lxml')
    source = response_soup.prettify()
    num_review = find_num_review(response_soup)
    num_page = calc_max_page(response_soup)

    reviews = []
    if num_review == 0:
        logger.info('\tno review at all')
    else:
        logger.info('\t[hotel {}] {} reviews in {} pages'.
                    format(hid, num_review, num_page))
        url_pattern = '-Reviews-'
        url_pos = url.index(url_pattern) + len(url_pattern)
        idx_page = 0
        stuck_cnt = 0
        while idx_page < num_page or len(reviews) < num_review:
            time.sleep(common.SLEEP_TIME)
            page_url = url if idx_page == 0 else ''.join(
                [url[:url_pos], 'or', str(idx_page * REVIEW_PER_PAGE),
                 '-', url[url_pos:]])
            response = session.get(page_url + '#REVIEWS')
            items = match_review_ids(response.text)
            if idx_page < num_page-1 and len(items) < REVIEW_PER_PAGE:
                print('\tretry page {}'.format(idx_page))
                continue
            elif idx_page == num_page-1 and \
                    len(items) < num_review % REVIEW_PER_PAGE:
                print('\tretry page {}'.format(idx_page))
                # break
                continue
            else:
                len_b = len(reviews)
                [reviews.append(item) for item in items if item not in reviews]
                stuck_cnt = stuck_cnt + 1 if len_b == len(reviews) else 0
                logger.info('\t[hotel {}] [page {}] {} reviews, totaling {}'.
                            format(hid, idx_page + 1, len(items), len(reviews)))
                idx_page += 1
                if stuck_cnt > 10:
                    break
        if len(reviews) >= num_review:
            logger.info('\t[hotel {}] {} reviews retrieved'.
                        format(hid, len(reviews)))
        else:
            reviews = None
            logger.info('\t\tcorrupted')
    session.close()
    return source, num_review, reviews


def review_index_is_valid(hid):
    with taDB(common.TA_DB) as db:
        record = db.read_a_hotel(hid)
    if record is not None:
        rno = record[3]
        rid_str = record[4]

        rids = ast.literal_eval(rid_str)

        is_having = len(rids)
        if rno > is_having or is_having != len(set(rids)):
            print('should_have {}, is_having {}'.format(rno, is_having))
            logger.info('[hotel {}] FAILED: corrupted'.format(hid))
            return False
        elif rno < is_having:
            logger.info('[hotel {}] PASSED: extra reviews'.format(hid))
            return True
        else:
            logger.info('[hotel {}] PASSED: verified'.format(hid))
            return True
    else:
        return False


def start(gid):
    def gather_review_ids(title):
        while True:
            # logger.info('[worker {}] running'.format(title))
            cur_pair = que.get()
            if cur_pair is None:
                logger.info('[worker {}] shutting down'.format(title))
                break
            hid, hurl = next(iter(cur_pair.items()))
            hurl = TA_ROOT + hurl
            logger.info('[hotel {}] {}'.format(hid, hurl))
            html, rno, rid_list = find_review_ids(hid, hurl)
            if rid_list is not None:
                record = [hid, html, gid, rno, str(rid_list)]
                with lock:
                    with taDB(common.TA_DB) as idb:
                        idb.insert_a_hotel(record)
            else:
                logger.info('\ttry again later')
                que.put(cur_pair)
            que.task_done()

    que = queue.Queue()

    with taDB(common.TA_DB) as iodb:
        hid_pairs = iodb.get_hotel_url_pairs(gid)

    threads = []
    thread_size = common.DETAIL_THREAD_NUM
    for j in range(thread_size):
        t = threading.Thread(
            target=gather_review_ids, args=(str(j + 1))
        )
        t.start()
        threads.append(t)

    [que.put({key: hid_pairs[key]}) for key in hid_pairs
     if not review_index_is_valid(key)]

    que.join()

    for k in range(thread_size):
        que.put(None)
    for t in threads:
        t.join()

    logger.info('all review ids are ready')
