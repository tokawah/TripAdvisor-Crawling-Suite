#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
from common import REVIEW_FOLDER, TA_ROOT
from os.path import isfile, join
import requests
import time
import math
import re
import os
import queue
import threading
import ast
import logging

logger = logging.getLogger()
CHUNK_SIZE = 500


def find_reviews(web_data):
    return re.findall(
        '(?<=reviewlistingid=\")\d+(?=\")',
        web_data, re.IGNORECASE)


def review_result_is_valid(loc, hotel_id):
    index_dir = join(loc, join(REVIEW_FOLDER, hotel_id))
    index_file = join(index_dir, 'index.txt')
    review_file = join(index_dir, 'result.txt')
    rids = common.read_binary(index_file)
    if int(rids[0]) > 0:
        if isfile(review_file):
            del rids[0]
            new_rids = find_reviews(common.read_file(review_file))
            if set(rids) != set(new_rids):
                logger.info('[hotel {}] FAILED: corrupted'.format(hotel_id))
                os.remove(review_file)
                return False
            else:
                logger.info('[hotel {}] PASSED: verified'.format(hotel_id))
                return True
        else:
            return False
    else:
        logger.info('[hotel {}] PASSED: no reviews'.format(hotel_id))
        return True


def start(loc):
    def gather_reviews(title):
        def gen_review_url(rid):
            return TA_ROOT + 'OverlayWidgetAjax?' + '&'.join(
                ['Mode=EXPANDED_HOTEL_REVIEWS',
                 'metaReferer=Hotel_Review',
                 'reviews=' + rid])

        while True:
            logger.info('[worker {}] running'.format(title))
            hid = que.get()
            if hid is None:
                logger.info('[worker {}] shutting down'.format(title))
                break
            index_dir = join(loc, join(REVIEW_FOLDER, hid))
            index_file = join(index_dir, 'index.txt')
            review_file = join(index_dir, 'result.txt')
            rids = common.read_binary(index_file)
            del rids[0]
            new_rids = []
            result = []
            slice_num = math.ceil(len(rids) / CHUNK_SIZE)
            for slicePos in range(slice_num):
                time.sleep(common.SLEEP_TIME)
                spos = slicePos * CHUNK_SIZE
                epos = (slicePos + 1) * CHUNK_SIZE \
                    if slicePos + 1 < slice_num else len(rids)
                id_string = ','.join(rids[spos: epos])
                logger.info('\t[hotel {}] from {} to {}'
                      .format(hid, spos + 1, epos))
                url = gen_review_url(id_string)
                web_data = requests.get(url)
                web_text = web_data.text
                result.append(web_text)
                new_rids.extend(find_reviews(web_text))
            diff_flag = False
            diff_set = set(rids).difference(set(new_rids))
            for diff in diff_set:
                url = gen_review_url(diff)
                web_data = requests.get(url)
                if len(find_reviews(web_data.text)) > 0:
                    diff_flag = True
                    logger.info('{} is not empty'.format(diff))
                    break
            if not diff_flag:
                if diff_set:
                    new_rids.insert(0, len(new_rids))
                    common.write_binary(index_file, new_rids)
                    logger.info('\t[hotel {}] review indexes updated'.format(hid))
                common.write_file(review_file, '\r\n'.join(result))
            else:
                logger.info('\ttry again later')
                logger.info('\t{}'.format(diff_set))
                que.put(hid)
            que.task_done()

    que = queue.Queue()
    hid_pairs = ast.literal_eval(
        common.read_file(join(loc, 'hids.txt')))

    threads = []
    thread_size = min(common.REVIEW_THREAD_NUM, len(hid_pairs))
    for j in range(thread_size):
        t = threading.Thread(
            target=gather_reviews, args=(str(j + 1))
        )
        t.start()
        threads.append(t)

    # push items into the queue
    # hid_pairs = ast.literal_eval(common.read_file('hids.txt'))
    [que.put(key) for key in hid_pairs
     if not review_result_is_valid(loc, key)]

    # block until all tasks are done
    que.join()

    # stop workers
    for k in range(thread_size):
        que.put(None)
    for t in threads:
        t.join()

    logger.info('all reviews are ready')
    common.write_file(join(loc, 'ok'), '')
    print('write ok')
