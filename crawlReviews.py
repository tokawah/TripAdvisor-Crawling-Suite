#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
from common import REVIEW_FOLDER
from common import TA_ROOT, SLEEP_TIME, REVIEW_THREAD_NUM
from os.path import isfile, join
import requests
import time
import math
import re
import os
import queue
import threading
import ast


def find_reviews(web_data):
    return re.findall(
        '(?<=reviewlistingid=\")\d+(?=\")',
        web_data, re.IGNORECASE)


def gather_reviews(title):
    while True:
        print('[worker {}] running'.format(title))
        hid = que.get()
        if hid is None:
            print('[worker {}] shutting down'.format(title))
            break
        index_dir = join(REVIEW_FOLDER, hid)
        index_file = join(index_dir, 'index.txt')
        review_file = join(index_dir, 'result.txt')
        rids = common.read_binary(index_file)
        del rids[0]
        new_rids = []
        result = []
        chunk_size = 500
        slice_num = math.ceil(len(rids) / chunk_size)
        for slicePos in range(slice_num):
            time.sleep(SLEEP_TIME)
            spos = slicePos * chunk_size
            epos = (slicePos + 1) * chunk_size \
                if slicePos + 1 < slice_num else len(rids)
            id_string = ','.join(rids[spos: epos])
            print('\t[hotel {}] from {} to {}'
                  .format(hid, spos + 1, epos))
            url = TA_ROOT + 'OverlayWidgetAjax?' + '&'.join(
                ['Mode=EXPANDED_HOTEL_REVIEWS',
                 'metaReferer=Hotel_Review',
                 'reviews=' + id_string])
            web_data = requests.get(url)
            web_text = web_data.text
            result.append(web_text)
            new_rids.extend(find_reviews(web_text))
        if set(rids) == set(new_rids):
            common.write_file(review_file, '\r\n'.join(result))
        else:
            print('\ttry again later')
            print('rid={}, nrid={}, {}'.format(
                len(set(rids)), len(set(new_rids)),
                set(rids) == set(new_rids)))
            for item in rids:
                if item not in new_rids:
                    print('\t\t'+item)
            que.put(hid)
        que.task_done()


def review_result_is_valid(hotel_id):
    index_dir = join(REVIEW_FOLDER, hotel_id)
    index_file = join(index_dir, 'index.txt')
    review_file = join(index_dir, 'result.txt')
    rids = common.read_binary(index_file)
    if int(rids[0]) > 0:
        if isfile(review_file):
            del rids[0]
            new_rids = find_reviews(common.read_file(review_file))
            if set(rids) != set(new_rids):
                print('[hotel {}] FAILED: corrupted'.format(hotel_id))
                os.remove(review_file)
                return False
            else:
                print('[hotel {}] PASSED: verified'.format(hotel_id))
                return True
        else:
            return False
    else:
        print('[hotel {}] PASSED: no reviews'.format(hotel_id))
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
hid_pairs = ast.literal_eval(common.read_file('hids.txt'))
[que.put(key) for key in ast.literal_eval(
    common.read_file('hids.txt')) if not review_result_is_valid(key)]

# block until all tasks are done
que.join()

# stop workers
for k in range(REVIEW_THREAD_NUM):
    que.put(None)
for t in threads:
    t.join()

print('all reviews are ready')
