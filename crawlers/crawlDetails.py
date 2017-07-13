#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
from common import HOTEL_FOLDER, REVIEW_FOLDER, TA_ROOT
from common import REVIEW_PER_PAGE
from os.path import isfile, join
import time
from bs4 import BeautifulSoup
import math
import os
import re
import threading
import queue
import requests
import ast
import logging

logger = logging.getLogger()


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
            reviews.insert(0, str(num_review))
        else:
            reviews = None
            logger.info('\t\tcorrupted')
    session.close()
    return source, reviews


def review_index_is_valid(loc, hotel_id):
    rid_file = join(loc, join(
        join(REVIEW_FOLDER, hotel_id), 'index.txt'))
    detail_file = join(loc, join(HOTEL_FOLDER, hotel_id + '.txt'))
    if isfile(rid_file) and isfile(detail_file):
        try:
            rids = common.read_binary(rid_file)
            should_have = int(rids[0])
            del rids[0]
            is_having = len(rids)
            if should_have > is_having or is_having != len(set(rids)):
                logger.info('[hotel {}] FAILED: corrupted'.format(hotel_id))
                # delete the corrupted file
                os.remove(rid_file)
                return False
            elif should_have < is_having:
                logger.info('[hotel {}] PASSED: extra reviews'.format(hotel_id))
                return True
            else:
                logger.info('[hotel {}] PASSED: verified'.format(hotel_id))
                return True
        except IndexError:
            return False
    else:
        return False


def start(loc):
    def gather_review_ids(title):
        while True:
            logger.info('[worker {}] running'.format(title))
            cur_pair = que.get()
            if cur_pair is None:
                logger.info('[worker {}] shutting down'.format(title))
                break
            hid, hurl = next(iter(cur_pair.items()))
            hurl = TA_ROOT + hurl
            logger.info('[hotel {}] {}'.format(hid, hurl))
            page_source, rid_list = find_review_ids(hid, hurl)
            detail_file = join(loc, join(HOTEL_FOLDER, hid + '.txt'))
            common.write_file(detail_file, page_source)
            if rid_list is not None:
                index_folder = join(loc, join(REVIEW_FOLDER, hid))
                if not os.path.exists(index_folder):
                    os.makedirs(index_folder)
                index_file = join(index_folder, 'index.txt')
                common.write_binary(index_file, rid_list)
            else:
                logger.info('\ttry again later')
                que.put(cur_pair)
            que.task_done()

    que = queue.Queue()
    hid_pairs = ast.literal_eval(
        common.read_file(join(loc, 'hids.txt')))

    threads = []
    thread_size = min(common.DETAIL_THREAD_NUM, len(hid_pairs))
    for j in range(thread_size):
        t = threading.Thread(
            target=gather_review_ids, args=(str(j + 1))
        )
        t.start()
        threads.append(t)

    # push items into the queue
    [que.put({key: hid_pairs[key]}) for key in hid_pairs
     if not review_index_is_valid(loc, key)]

    # block until all tasks are done
    que.join()

    # stop workers
    for k in range(thread_size):
        que.put(None)
    for t in threads:
        t.join()

    logger.info('all review ids are ready')
