#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
from common import HOTEL_ID, HOTEL_URL, SLEEP_TIME
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


def find_review_ids(url):
    session = requests.Session()
    paras = {'filterLang': 'ALL'}
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    session.post(url, data=paras, headers=headers)
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    source = soup.prettify()
    numReview = find_num_review(soup)
    numPage = calc_max_page(soup)

    reviews = []
    if numReview == 0:
        print('\tno review at all')
        reviews.insert(0, str(numReview))
    else:
        print('\t{} reviews in {} pages'
              .format(numReview, numPage))
        url_pattern = '-Reviews-'
        url_pos = url.index(url_pattern) + len(url_pattern)
        for i in range(0, numPage):
            pageURL = url if i == 0 else ''.join(
                [url[:url_pos], 'or', str(i * REVIEW_PER_PAGE),
                 '-', url[url_pos:]])
            response = session.get(pageURL + '#REVIEWS')
            items = match_review_ids(response.text)
            if DETAIL_THREAD_NUM == 1:
                print('[page {}] {} reviews'
                      .format(i+1, len(items)))
            if len(items) < REVIEW_PER_PAGE and i < numPage-1:
                break
            elif i == numPage-1 \
                    and len(items) < numReview % REVIEW_PER_PAGE:
                break
            else:
                reviews.extend(items)
        if len(set(reviews)) >= numReview:
            print('\t{} reviews retrieved'.format(len(reviews)))
            reviews.insert(0, str(numReview))
        else:
            reviews = None
            print('\t\tcorrupted')
    session.close()
    return source, reviews


def match_review_ids(pageSource):
    return re.findall('(?<=review_)\d+', pageSource)


def find_max_page(soup):
    div = soup.find('div', class_='pageNumbers')
    if div is None:
        return 1 if match_review_ids(soup) else 0
    else:
        num = div.find_all('a')[-1]
        return int(num['data-offset'])/REVIEW_PER_PAGE+1


def calc_max_page(soup):
    return math.ceil(find_num_review(soup)/REVIEW_PER_PAGE)


def find_num_review(soup):
    div = soup.find('a', class_='more taLnk')
    return 0 if div is None else int(re.sub('\D', '', div.text))


def review_index_is_valid(hotelID):
    ridFile = join(join(REVIEW_FOLDER, hotelID), 'index.txt')
    if isfile(ridFile):
        try:
            rids = common.read_binary(ridFile)
            num = int(rids[0])
            del rids[0]
            set_size = len(set(rids))
            if num > set_size:
                print('[hotel {}] FAILED: corrupted'.format(hotelID))
                # delete the corrupted file
                os.remove(ridFile)
                return False
            elif num < set_size:
                print('[hotel {}] PASSED: extra reviews'.format(hotelID))
                return True
            else:
                print('[hotel {}] PASSED: verified'.format(hotelID))
                return True
        except IndexError:
            return False
    else:
        return False


def gather_review_ids(title):
    while True:
        print('[worker {}] running'.format(title))
        curPair = que.get()
        if curPair is None:
            print('[worker {}] shutting down'.format(title))
            break
        hurl = TA_ROOT + curPair[HOTEL_URL]
        hid = curPair[HOTEL_ID]
        print('[hotel {}] {}'.format(hid, hurl))
        pageSource, ridList = find_review_ids(hurl)
        detailFile = join(HOTEL_FOLDER, hid + '.txt')
        common.write_file(detailFile, pageSource)
        time.sleep(SLEEP_TIME)
        if ridList is not None:
            indexFolder = join(REVIEW_FOLDER, hid)
            if not os.path.exists(indexFolder):
                os.makedirs(indexFolder)
            indexFile = join(indexFolder, 'index.txt')
            common.write_binary(indexFile, ridList)
        else:
            print('\ttry again later')
            que.put(curPair)
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
hidPairs = [x for x in common.read_binary('hids.txt')]
[que.put(x) for x in hidPairs if not
    review_index_is_valid(x[HOTEL_ID])]

# block until all tasks are done
que.join()

# stop workers
for k in range(DETAIL_THREAD_NUM):
    que.put(None)
for t in threads:
    t.join()

print('all review ids are ready')
