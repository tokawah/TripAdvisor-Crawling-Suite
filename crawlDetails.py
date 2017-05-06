#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
from common import SLEEP_TIME
from common import HOTEL_FOLDER, REVIEW_FOLDER, TA_ROOT
from common import REVIEW_PER_PAGE, DETAIL_THREAD_NUM
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


def find_review_ids(url):
    def calc_max_page(soup):
        return math.ceil(find_num_review(soup) / REVIEW_PER_PAGE)

    def find_num_review(soup):
        div = soup.find('a', class_='more taLnk')
        return 0 if div is None else int(re.sub('\D', '', div.text))

    def match_review_ids(page_source):
        return re.findall('(?<=review_)\d+', page_source)

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
        reviews.insert(0, str(num_review))
    else:
        logger.info('\t{} reviews in {} pages'
              .format(num_review, num_page))
        url_pattern = '-Reviews-'
        url_pos = url.index(url_pattern) + len(url_pattern)
        for i in range(0, num_page):
            time.sleep(SLEEP_TIME)
            page_url = url if i == 0 else ''.join(
                [url[:url_pos], 'or', str(i * REVIEW_PER_PAGE),
                 '-', url[url_pos:]])
            response = session.get(page_url + '#REVIEWS')
            items = match_review_ids(response.text)
            if DETAIL_THREAD_NUM == 1:
                logger.info('[page {}] {} reviews'
                      .format(i+1, len(items)))
            if len(items) < REVIEW_PER_PAGE and i < num_page-1:
                break
            elif i == num_page-1 and \
                    len(items) < num_review % REVIEW_PER_PAGE:
                break
            else:
                reviews.extend(items)
        if len(set(reviews)) >= num_review:
            logger.info('\t{} reviews retrieved'.format(len(reviews)))
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
            num = int(rids[0])
            del rids[0]
            set_size = len(set(rids))
            if num > set_size:
                logger.info('[hotel {}] FAILED: corrupted'.format(hotel_id))
                # delete the corrupted file
                os.remove(rid_file)
                return False
            elif num < set_size:
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
            page_source, rid_list = find_review_ids(hurl)
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

    threads = []
    for j in range(DETAIL_THREAD_NUM):
        t = threading.Thread(
            target=gather_review_ids, args=(str(j + 1))
        )
        t.start()
        threads.append(t)

    # push items into the queue
    hid_pairs = ast.literal_eval(
        common.read_file(join(loc, 'hids.txt')))
    [que.put({key: hid_pairs[key]}) for key in hid_pairs
     if not review_index_is_valid(loc, key)]

    # block until all tasks are done
    que.join()

    # stop workers
    for k in range(DETAIL_THREAD_NUM):
        que.put(None)
    for t in threads:
        t.join()

    logger.info('all review ids are ready')
