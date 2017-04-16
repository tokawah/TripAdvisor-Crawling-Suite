#!/usr/bin/python3
# -*- coding:utf8 -*-
import ast
import pickle
from commons import HOTEL_ID, REVIEW_FOLDER, USER_FOLDER, TA_ROOT, SLEEP_TIME
from os.path import isfile, join
import re
import requests
from bs4 import BeautifulSoup
import time


def gen_uid_index():
    print('retrieving user ids...\r\nthis could take several minutes.')
    with open('hids.txt', 'rb') as fp:
        hid_list = [ast.literal_eval(x)[HOTEL_ID] for x in pickle.load(fp)]
    uids = []
    for hid_item in hid_list:
        review_file = join(join(REVIEW_FOLDER, hid_item), 'result.txt')
        if not isfile(review_file):
            continue
        #print('hotel {}'.format(hid_item))
        with open(review_file, 'r', encoding='utf8') as fp:
            web_data = fp.read()
            fp.close()
        m = re.findall('(?<=profile_)[0-9A-Z]{32}', web_data)
        uids.extend(m)
        #print('\t{} out of {} unique users'
              #.format(len(set(uids)), len(uids)))
    unique_uids = list(set(uids))
    print('{} out of {} unique users'
          .format(len(unique_uids), len(uids)))
    with open('uids.txt', 'wb') as fp:
        pickle.dump(unique_uids, fp)
        fp.close()


if not isfile('uids.txt'):
    gen_uid_index()

with open('uids.txt', 'rb') as fp:
    uid_list = [x for x in pickle.load(fp)]
    fp.close()
print('{} users found'.format(len(uid_list)))
cnt_skip = 0
cnt_get = 0
for uid in uid_list:
    print('user {}'.format(uid))
    uid_file = join(USER_FOLDER, uid+'.txt')
    if isfile(uid_file):
        # should verify the existing file
        print('\tskipped')
        cnt_skip += 1
        continue
    url = TA_ROOT + '/MemberOverlay?uid=' + uid
    web_data = ''
    try:
        web_data = requests.get(url)
    except:
        pass
    soup = BeautifulSoup(web_data.text, 'lxml')
    if len([x for x in soup.find_all('a') if
            x.text.strip() == 'Full profile']) > 0:
        #print('\tdone')
        cnt_get += 1
        with open(uid_file, 'w', encoding='utf8') as f:
            f.write(soup.prettify())
            f.close()
        #time.sleep(SLEEP_TIME)
    #break
print('\r\n\r\n{} user ids, {} obtained, {} skipped.'
      .format(len(uid_list), cnt_get, cnt_skip))
# uuids of users who register outside TA_ROOT are not shown
# this script is supposed to be run after collecting all reviews
