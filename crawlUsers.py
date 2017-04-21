#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
from common import HOTEL_ID, REVIEW_FOLDER, USER_FOLDER
from common import TA_ROOT, SLEEP_TIME, USER_THREAD_NUM
from os.path import isfile, join
import re
import requests
from bs4 import BeautifulSoup
import time
import threading
import queue


def gen_uid_index():
    print('retrieving user ids...\r\nthis could take several minutes.')
    hidList = [x[HOTEL_ID] for x in common.read_binary('hids.txt')]
    uids = []
    for hidItem in hidList:
        review_file = join(join(REVIEW_FOLDER, hidItem), 'result.txt')
        if isfile(review_file):
            webData = common.read_file(review_file)
            m = re.findall('(?<=profile_)[0-9A-Z]{32}', webData)
            uids.extend(m)
        else:
            pass
    uuids = list(set(uids))
    print('{} out of {} unique users'
          .format(len(uuids), len(uids)))
    common.write_binary('uids.txt', uuids)
    return uuids


def gather_profiles(title):
    while True:
        print('[worker {}] running'.format(title))
        uid = que.get()
        if uid is None:
            print('[worker {}] shutting down'.format(title))
            break
        print('user {}'.format(uid))
        url = TA_ROOT + 'MemberOverlay?uid=' + uid
        web_data = requests.get(url)
        soup = BeautifulSoup(web_data.text, 'lxml')
        time.sleep(SLEEP_TIME)
        if profile_is_valid(soup):
            uidFile = join(USER_FOLDER, uid + '.txt')
            common.write_file(uidFile, soup.prettify())
        else:
            que.put(uid)
        que.task_done()


def profile_is_valid(soup):
    return len([x for x in soup.find_all('a')
                if x.text.strip() == 'Full profile']) > 0


def user_index_is_valid(uid):
    uidFile = join(USER_FOLDER, uid + '.txt')
    if isfile(uidFile):
        soup = BeautifulSoup(common.read_file(uidFile), 'lxml')
        if profile_is_valid(soup):
            print('[user {}] PASSED: verified'.format(uid))
            return True
        else:
            print('[user {}] FAILED: corrupted'.format(uid))
            return False
    else:
        return False


uidList = common.read_binary('uids.txt') \
    if isfile('uids.txt') else gen_uid_index()
print('{} users found'.format(len(uidList)))

que = queue.Queue()

threads = []
for j in range(USER_THREAD_NUM):
    t = threading.Thread(
        target=gather_profiles, args=(str(j + 1))
    )
    t.start()
    threads.append(t)

# push items into the queue
[que.put(x) for x in uidList if not user_index_is_valid(x)]

# block until all tasks are done
que.join()

# stop workers
for k in range(USER_THREAD_NUM):
    que.put(None)
for t in threads:
    t.join()

print('all user ids are ready')
