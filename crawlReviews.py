#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
from common import HOTEL_ID, REVIEW_FOLDER
from common import TA_ROOT, SLEEP_TIME, REVIEW_THREAD_NUM
from os.path import isfile, join
import requests
import time
import math
import re
import os
import queue
import threading


def find_reviews(webdata):
    return re.findall(
        '(?<=reviewlistingid=\")\d+(?=\")',
        webdata, re.IGNORECASE)


def gather_reviews(title):
    while True:
        print('[worker {}] running'.format(title))
        hid = que.get()
        if hid is None:
            print('[worker {}] shutting down'.format(title))
            break
        indexDir = join(REVIEW_FOLDER, hid)
        indexFile = join(indexDir, 'index.txt')
        reviewFile = join(indexDir, 'result.txt')
        rids = common.read_binary(indexFile)
        del rids[0]
        nrids = []
        result = []
        chunkSize = 500
        sliceNum = math.ceil(len(rids) / chunkSize)
        for slicePos in range(sliceNum):
            spos = slicePos * chunkSize
            epos = (slicePos + 1) * chunkSize \
                if slicePos + 1 < sliceNum else len(rids)
            id_string = ','.join(rids[spos: epos])
            print('\t[hotel {}] from {} to {}'
                  .format(hid, spos + 1, epos))
            url = TA_ROOT + 'OverlayWidgetAjax?' + '&'.join(
                ['Mode=EXPANDED_HOTEL_REVIEWS',
                 'metaReferer=Hotel_Review',
                 'reviews=' + id_string])
            webData = requests.get(url)
            webText = webData.text
            result.append(webText)
            nrids.extend(find_reviews(webText))
            time.sleep(SLEEP_TIME)
        if set(rids) == set(nrids):
            common.write_file(reviewFile, '\r\n'.join(result))
        else:
            print('\ttry again later')
            print('rid={}, nrid={}, {}'.format(
                len(set(rids)), len(set(nrids)),
                set(rids) == set(nrids)))
            for item in rids:
                if item not in nrids:
                    print('\t\t'+item)
            que.put(hid)
        que.task_done()


def review_result_is_valid(hotelID):
    indexDir = join(REVIEW_FOLDER, hotelID)
    indexFile = join(indexDir, 'index.txt')
    reviewFile = join(indexDir, 'result.txt')
    rids = common.read_binary(indexFile)
    if int(rids[0]) > 0:
        if isfile(reviewFile):
            del rids[0]
            nrids = find_reviews(common.read_file(reviewFile))
            if set(rids) != set(nrids):
                print('[hotel {}] FAILED: corrupted'.format(hotelID))
                os.remove(reviewFile)
                return False
            else:
                print('[hotel {}] PASSED: verified'.format(hotelID))
                return True
        else:
            return False
    else:
        print('[hotel {}] PASSED: no reviews'.format(hotelID))
        return True


que = queue.Queue()
threads = []
for j in range(REVIEW_THREAD_NUM):
    t = threading.Thread(
        target=gather_reviews, args=(str(j + 1))
    )
    t.start()
    threads.append(t)

# push items into the queue
[que.put(x[HOTEL_ID]) for x in common.read_binary('hids.txt')
 if not review_result_is_valid(x[HOTEL_ID])]

# block until all tasks are done
que.join()

# stop workers
for k in range(REVIEW_THREAD_NUM):
    que.put(None)
for t in threads:
    t.join()

print('all reviews are ready')
