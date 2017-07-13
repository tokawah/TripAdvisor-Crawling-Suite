#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
from common import TA_ROOT
import re
import time
import threading
import queue
import logging
from tadb import tadb

logger = logging.getLogger()
lock = threading.Lock()


def start():
    def user_is_valid(uid):
        with tadb(common.TA_DB) as db:
            user_record = db.read_a_user(uid)
        if user_record is None:
            return False
        html = user_record[0]
        if html is None:
            return False
        soup = common.load_soup_string(html)
        if soup.find('div', id='MODULES_MEMBER_CENTER') is None:
            logger.info('[user {}] FAILED: corrupted'.format(uid))
            return False
        else:
            logger.info('[user {}] PASSED: verified'.format(uid))
            return True

    def gather_profiles(title):
        while True:
            logger.info('[worker {}] running'.format(title))
            uid = que.get()
            if uid is None:
                logger.info('[worker {}] shutting down'
                            .format(title))
                break
            logger.info('[user {}]'.format(uid))
            url = TA_ROOT + 'MemberOverlay?uid=' + uid
            simple_soup = common.load_soup_online(url).find(
                'div', class_='memberOverlay')
            profile_url = re.search(
                '(?<=")/members/.+(?=")', str(simple_soup))
            if profile_url is None:
                profile_url = re.search(
                    '(?<=")/MemberProfile-a_uid.[A-Z0-9]+(?=")',
                    str(simple_soup))

            result = []
            if profile_url is not None:
                profile_url = TA_ROOT + profile_url.group(0).strip()
                result.append(simple_soup.prettify())
                detail_soup = common.load_soup_online(profile_url)
                member_soup = detail_soup.find(
                    'div', id='MODULES_MEMBER_CENTER')
                if member_soup is not None:
                    result.append(member_soup.prettify())
                    record = [uid, '\r\n'.join(result)]
                    with lock:
                        with tadb(common.TA_DB) as db:
                            db.insert_a_user(record)
                else:
                    if '404' in detail_soup.find('title').string:
                        with lock:
                            with tadb(common.TA_DB) as db:
                                db.remove_user_id_in_review(uid)
                                logger.info('\tuser id removed')
                    else:
                        logger.info('\tfailed to fetch full profile')
                        que.put(uid)
            else:
                logger.info('\tno profile url')
                que.put(uid)

            time.sleep(common.SLEEP_TIME)
            que.task_done()

    # extract unique user ids from reviews
    logger.info('retrieving users...')
    with tadb(common.TA_DB) as iodb:
        iodb.generate_unique_users()
        uids = iodb.read_all_user_ids()
    logger.info('{} users found'.format(len(uids)))

    que = queue.Queue()

    threads = []
    thread_size = common.USER_THREAD_NUM
    for j in range(thread_size):
        t = threading.Thread(
            target=gather_profiles, args=(str(j + 1))
        )
        t.start()
        threads.append(t)

    [que.put(x) for x in uids
     if not user_is_valid(x)]

    que.join()

    for k in range(thread_size):
        que.put(None)
    for t in threads:
        t.join()

    logger.info('all user ids are ready')
