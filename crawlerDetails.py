#!/usr/bin/python3
# -*- coding:utf8 -*-

from os.path import isfile, join
import ast
import time
import re

import pickle
from commons import HOTEL_ID, HOTEL_URL, HOTEL_DETAIL

import commons
from commons import TA_ROOT, JSON_FOLDER, REVIEW_FOLDER
from bs4 import BeautifulSoup

import glob
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
import math
import os
import re
from selenium.webdriver.support.ui import WebDriverWait
# from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import selenium.webdriver.support.ui as ui
import threading
import queue
import tempfile
import shutil


def navigate(browser, url):
    while True:
        try:
            browser.switch_to.window(browser.window_handles[0])
            browser.get(url)
            break
        except WebDriverException:
            pass
        except TimeoutException:
            pass


def set_lang(browser):
    radio_all_id = 'taplc_prodp13n_hr_sur_review_filter_controls_0_filterLang_ALL'
    wait = WebDriverWait(browser, 10)
    try:
        browser.switch_to.window(browser.window_handles[0])
        # radio_all = wait.until(EC.visibility_of_element_located((By.ID, radio_all_id)))
        radio_all = wait.until(EC.element_to_be_clickable((By.ID, radio_all_id)))
        # if not radio_all.is_selected():
        radio_all.click()
        time.sleep(1)
        print('\t\tlang set')
        # else:
        # print('\t\tlang skipped')
        # else:
    except TimeoutException:
        print('\ttime out')
        # browser.refresh()
        #browser.get(browser.current_url)


def find_review_ids(url):
    reviews = []
    browser = None
    while browser is None:
        try:
            browser = webdriver.Chrome()
        except WebDriverException:
            browser = None
    navigate(browser, url)
    time.sleep(1)
    source = BeautifulSoup(browser.page_source).prettify()
    review_num = find_num_review(browser)
    page_num = calc_max_page(browser)

    if page_num == 0:
        print('\tno review at all')
    else:
        print('\t{} reviews in {} pages'
              .format(review_num, page_num))
        set_lang(browser)

        url_pattern = '-Reviews-'
        url_pos = url.index(url_pattern) + len(url_pattern)
        for i in range(1, page_num + 1):
            # print('\t\tpage {}'.format(i))
            items = match_review_ids(browser)
            # print('\t\t\t{} reviews'.format(len(items)))
            reviews.extend(items)
            if len(items) < 10 and i < page_num:
                print('\t\tcorrupted')
                return source, []

            if i < page_num:
                page_url = url[:url_pos] + 'or' + \
                           str(i * 10) + '-' + url[url_pos:]
                navigate(browser, page_url)
                time.sleep(1)
    browser.quit()
    print('\t{} reviews retrieved'.format(len(reviews)))
    reviews.insert(0, str(review_num))
    return source, reviews


def match_review_ids(browser):
    return re.findall('(?<=review_)\d+', browser.page_source)


def find_max_page(browser):
    soup = BeautifulSoup(browser.page_source, 'lxml')
    div = soup.find('div', class_='pageNumbers')
    if div is None:
        # div = soup.find('div', id='taplc_hr_reviews_list_0')
        return 1 if len(match_review_ids(browser)) > 0 else 0
    else:
        num = div.find_all('a')[-1]
        return int(num['data-page-number'])


def calc_max_page(browser):
    return math.ceil(find_num_review(browser) / 10)


def find_num_review(browser):
    try:
        div = browser.find_element_by_css_selector('.more.taLnk')
        div = div.text
        div = div[:div.index(' ')].replace(',', '')
        return int(div)
    except NoSuchElementException:
        return 0


def remove_temp_files():
    for tmp_folder in glob.glob(
            join(tempfile.gettempdir(), 'scoped*')
    ):
        try:
            shutil.rmtree(tmp_folder)
            if os.path.isdir(tmp_folder):
                os.rmdir(tmp_folder)
        except:
            pass


def verify_hotel_index(hotel_id):
    review_index_file = join(join(REVIEW_FOLDER, hotel_id), 'index.txt')
    if not isfile(review_index_file):
        return False
    else:
        with open(review_index_file, 'rb') as fp:
            rids = [x for x in pickle.load(fp)]
            fp.close()
        num = int(rids[0])
        del rids[0]
        set_size = len(set(rids))
        if num > set_size:
            print('{} corrupted'.format(hotel_id))
            os.rename(review_index_file,
                      review_index_file + str(int(round(time.time()*1000))))
            #os.remove(review_index_file)
        elif num < set_size:
            print('{} EXCEEDS #'.format(hotel_id))
        return num <= set_size


def gather_review_ids(pairs_in_queue, thread_title):
    cnt = 0
    while not pairs_in_queue.empty():
        print('[worker {}]'.format(thread_title))
        queue_dict = pairs_in_queue.get()
        hurl = TA_ROOT + queue_dict[HOTEL_URL]
        hid = queue_dict[HOTEL_ID]
        print('hotel {}: {}'.format(hid, hurl))
        return_source, review_list = find_review_ids(hurl)
        hotel_detail_file = join(JSON_FOLDER, hid + '_' + HOTEL_DETAIL + '.txt')
        with open(hotel_detail_file, 'w', encoding='utf8') as fp:
            fp.write(return_source)
            fp.close()
        if len(review_list) > 0:
            index_folder = join(REVIEW_FOLDER, hid)
            if not os.path.exists(index_folder):
                os.makedirs(index_folder)
            with open(join(index_folder, 'index.txt'), 'wb') as fp:
                pickle.dump(review_list, fp)
                fp.close()
        cnt += 1
        if cnt % 15 == 0:
            print('clean cache')
            remove_temp_files()
    print('shutting down worker {}'.format(thread_title))


with open('hids.txt', 'rb') as f:
    hid_pairs = [ast.literal_eval(x) for x in pickle.load(f)]

q = queue.Queue()
[q.put(x) for x in hid_pairs if not verify_hotel_index(x[HOTEL_ID])]
if q.empty():
    print('all review ids are ready')
else:
    THREAD_NUM = 4
    threads = []
    for j in range(THREAD_NUM):
        t = threading.Thread(
            target=gather_review_ids, args=(q, str(j + 1))
        )
        threads.append(t)
        # t.daemon = True
        t.start()
