#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
from common import REVIEW_FOLDER, USER_FOLDER
from common import TA_ROOT, SLEEP_TIME, USER_THREAD_NUM
from os.path import isfile, join
import re
import time
import threading
import queue
import ast


def gen_uid_index():
    print('retrieving user ids...\r\nthis could take several minutes.')
    hid_list = ast.literal_eval(common.read_file('hids.txt')).keys()
    uids = []
    for hidItem in hid_list:
        review_file = join(join(REVIEW_FOLDER, hidItem), 'result.txt')
        if isfile(review_file):
            web_data = common.read_file(review_file)
            m = re.findall('(?<=profile_)[0-9A-Z]{32}', web_data)
            uids.extend(m)
        else:
            pass
    unique_uids = list(set(uids))
    print('{} out of {} unique users'
          .format(len(unique_uids), len(uids)))
    common.write_binary('uids.txt', unique_uids)
    return unique_uids


def gather_profiles(title):
    while True:
        print('[worker {}] running'.format(title))
        uid = que.get()
        if uid is None:
            print('[worker {}] shutting down'.format(title))
            break
        print('user {}'.format(uid))
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
                uid_file = join(USER_FOLDER, uid + '.txt')
                common.write_file(uid_file, '\r\n'.join(result))
            else:
                print('\ttry again later')
                que.put(uid)
        else:
            print('\ttry again later')
            que.put(uid)

        time.sleep(SLEEP_TIME)
        que.task_done()


def profile_is_valid(soup):
    return soup.find('div', id='MODULES_MEMBER_CENTER') is not None


def user_index_is_valid(uid):
    uid_file = join(USER_FOLDER, uid + '.txt')
    if isfile(uid_file):
        soup = common.load_soup_local(uid_file)
        if profile_is_valid(soup):
            print('[user {}] PASSED: verified'.format(uid))
            return True
        else:
            print('[user {}] FAILED: corrupted'.format(uid))
            return False
    else:
        return False


uid_list = common.read_binary('uids.txt') \
    if isfile('uids.txt') else gen_uid_index()
print('{} users found'.format(len(uid_list)))

que = queue.Queue()

threads = []
for j in range(USER_THREAD_NUM):
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
for k in range(USER_THREAD_NUM):
    que.put(None)
for t in threads:
    t.join()

print('all user ids are ready')
