#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
from common import REVIEW_FOLDER, USER_FOLDER, TA_ROOT
from os.path import isfile, join
import re
import time
import threading
import queue
import ast
import logging

logger = logging.getLogger()


def profile_is_valid(soup):
    return soup.find('div', id='MODULES_MEMBER_CENTER') is not None


def user_index_is_valid(uid):
    uid_file = join(USER_FOLDER, uid + '.txt')
    if isfile(uid_file):
        soup = common.load_soup_local(uid_file)
        if profile_is_valid(soup):
            logger.info('[user {}] PASSED: verified'.format(uid))
            return True
        else:
            logger.info('[user {}] FAILED: corrupted'.format(uid))
            return False
    else:
        return False


def start(loc):
    def gen_uid_index():
        logger.info('retrieving user ids...\r\nthis could take several minutes.')
        hid_list = ast.literal_eval(
            common.read_file(join(loc, 'hids.txt'))).keys()
        uids = []
        for hidItem in hid_list:
            review_file = join(loc, join(
                join(REVIEW_FOLDER, hidItem), 'result.txt'))
            if isfile(review_file):
                web_data = common.read_file(review_file)
                m = re.findall('(?<=profile_)[0-9A-Z]{32}', web_data)
                uids.extend(m)
            else:
                pass
        unique_uids = list(set(uids))
        logger.info('{} out of {} unique users'
              .format(len(unique_uids), len(uids)))
        common.write_binary(join(loc, 'uids.txt'), unique_uids)
        return unique_uids

    def gather_profiles(title):
        while True:
            logger.info('[worker {}] running'.format(title))
            uid = que.get()
            if uid is None:
                logger.info('[worker {}] shutting down'.format(title))
                break
                logger.info('user {}'.format(uid))
            url = TA_ROOT + 'MemberOverlay?uid=' + uid
            simple_soup = common.load_soup_online(url).find(
                'div', class_='memberOverlay')
            nav_soup = simple_soup.find('div', class_='baseNav')
            profile_url = None if nav_soup is None else \
                [x['href'] for x in nav_soup.findAll(
                    'a') if 'profile' in x.getText()][0]
            result = []
            if profile_url is not None:
                profile_url = TA_ROOT + profile_url.strip()
                result.append(simple_soup.prettify())
                detail_soup = common.load_soup_online(profile_url)
                detail_soup = detail_soup.find(
                    'div', id='MODULES_MEMBER_CENTER')
                if detail_soup is not None:
                    result.append(detail_soup.prettify())
                    profile_file = join(loc, join(USER_FOLDER, uid + '.txt'))
                    common.write_file(profile_file, '\r\n'.join(result))
                else:
                    logger.info('\ttry again later')
                    que.put(uid)
            else:
                logger.info('\ttry again later')
                que.put(uid)

            time.sleep(SLEEP_TIME)
            que.task_done()

    uid_file = join(loc, 'uids.txt')
    uid_list = common.read_binary(uid_file) \
        if isfile(uid_file) else gen_uid_index()
    logger.info('{} users found'.format(len(uid_list)))

    que = queue.Queue()

    threads = []
    thread_size = min(common.USER_THREAD_NUM, len(uid_list))
    for j in range(thread_size):
        t = threading.Thread(
            target=gather_profiles, args=(str(j + 1))
        )
        t.start()
        threads.append(t)

    # push items into the queue
    [que.put(x) for x in uid_list if not user_index_is_valid(x)]

    # block until all tasks are done
    que.join()

    # stop workers
    for k in range(thread_size):
        que.put(None)
    for t in threads:
        t.join()

    logger.info('all user ids are ready')
