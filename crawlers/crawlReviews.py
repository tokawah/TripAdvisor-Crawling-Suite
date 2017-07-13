#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
from common import TA_ROOT
import requests
import time
import math
import re
import queue
import threading
import ast
import logging
from tadb import tadb

logger = logging.getLogger()
lock = threading.Lock()


def save_reviews(web_data):
    web_soup = common.load_soup_string(web_data)
    review_soups = web_soup.find_all(
        'div', id=re.compile('review_\d+'))
    records = []
    any_rids =[]
    for x in review_soups:
        # len('review_') = 7
        any_rid = x['id'][7:]
        any_html = x.prettify()
        any_uid = re.search('[A-Z0-9]{32}', any_html)
        if any_uid is not None:
            any_uid = any_uid.group(0)
        any_rids.append(any_rid)
        records.append((any_rid, any_html, any_uid))
    with lock:
        with tadb(common.TA_DB) as db:
            db.insert_many_reviews(records)
    return any_rids


def review_result_is_valid(hotel_id):
    with tadb(common.TA_DB) as db:
        record = db.read_a_hotel(hotel_id)
    if record is None:
        return False
    rno = record[3]
    if int(rno) == 0:
        logger.info('[hotel {}] PASSED: no reviews'.format(hotel_id))
        return True
    rid_str = record[4]
    rids = ast.literal_eval(rid_str)
    if rno < len(rids):
        return False

    with tadb(common.TA_DB) as db:
        for rid in rids:
            rrecord = db.read_a_review(rid)
            if rrecord is None:
                return False
            html = rrecord[1]
            if html is None:
                logger.info('[hotel {}] FAILED: HTML is absent'.format(hotel_id))
                return False
            rec_soup = common.load_soup_string(html)
            if rec_soup.find('div', id=''.join(['review_', rid])) is None:
                print(html)
                logger.info('[hotel {}] FAILED: corrupted HTML'.format(hotel_id))
                return False
    logger.info('[hotel {}] PASSED: verified'.format(hotel_id))
    return True


def start(gid):
    def gather_reviews(title):
        def gen_review_url(rid):
            return TA_ROOT + 'OverlayWidgetAjax?' + '&'.join(
                ['Mode=EXPANDED_HOTEL_REVIEWS',
                 'metaReferer=Hotel_Review',
                 'reviews=' + rid])

        while True:
            logger.info('[worker {}] running'.format(title))
            hotel_id = que.get()
            if hotel_id is None:
                logger.info('[worker {}] shutting down'.format(title))
                break
            with tadb(common.TA_DB) as db:
                record = db.read_a_hotel(hotel_id)
            if record is None:
                continue
            rid_str = record[4]
            rids = ast.literal_eval(rid_str)
            new_rids = []
            slice_num = math.ceil(
                len(rids) / common.REVIEW_CHUNK_SIZE)
            for slicePos in range(slice_num):
                time.sleep(common.SLEEP_TIME)
                spos = slicePos * common.REVIEW_CHUNK_SIZE
                epos = (slicePos + 1) * common.REVIEW_CHUNK_SIZE \
                    if slicePos + 1 < slice_num else len(rids)
                id_string = ','.join(rids[spos: epos])
                logger.info('\t[hotel {}] from {} to {}'
                            .format(hotel_id, spos + 1, epos))
                url = gen_review_url(id_string)
                web_data = requests.get(url)
                web_text = web_data.text
                new_rids.extend(save_reviews(web_text))
            diff_flag = False
            diff_set = set(rids).difference(set(new_rids))
            for diff in diff_set:
                print('found diff')
                url = gen_review_url(diff)
                web_data = requests.get(url)
                blank = re.findall(
                    '(?<=id=\")review_\d+(?=\")',
                    web_data.text, re.IGNORECASE)
                if len(blank) > 0:
                    diff_flag = True
                    logger.info('{} is not empty'.format(diff))
                    break
            if not diff_flag:
                if diff_set:
                    with lock:
                        with tadb(common.TA_DB) as db:
                            db.update_review_list_in_hotel(
                                hotel_id, len(new_rids), str(new_rids))
                    logger.info('\t[hotel {}] review indexes updated'
                                .format(hotel_id))
            else:
                logger.info('\ttry again later')
                logger.info('\t{}'.format(diff_set))
                que.put(hotel_id)
            que.task_done()

    que = queue.Queue()

    hid_pairs = tadb.get_hotel_url_pairs(gid)

    threads = []
    thread_size = common.REVIEW_THREAD_NUM
    for j in range(thread_size):
        t = threading.Thread(
            target=gather_reviews, args=(str(j + 1))
        )
        t.start()
        threads.append(t)

    [que.put(key) for key in hid_pairs
     if not review_result_is_valid(key)]

    que.join()

    for k in range(thread_size):
        que.put(None)
    for t in threads:
        t.join()

    logger.info('all reviews are ready')
