#!/usr/bin/python3
# -*- coding:utf8 -*-
import base64
from bs4 import BeautifulSoup
import requests
import pickle
import pycld2 as cld2
import string


SLEEP_TIME = None
SNIPPET_THREAD_NUM = None
DETAIL_THREAD_NUM = None
REVIEW_THREAD_NUM = None
USER_THREAD_NUM = None

HOTEL_PER_PAGE = 30
REVIEW_PER_PAGE = 5

HOTEL_FOLDER = 'hotels'
REVIEW_FOLDER = 'reviews'
USER_FOLDER = 'users'

TA_ROOT = 'https://www.tripadvisor.com.au/'


def load_soup_local(fn):
    file = read_file(fn)
    return BeautifulSoup(file, 'lxml')


def load_soup_online(url):
    req = requests.get(url)
    data = req.text
    req.close()
    return BeautifulSoup(data, 'lxml')


def read_binary(fn):
    with open(fn, 'rb') as fp:
        data = [x for x in pickle.load(fp)]
        fp.close()
    return data


def write_binary(fn, data):
    with open(fn, 'wb') as fp:
        pickle.dump(data, fp)
        fp.close()


def write_file(fn, data):
    with open(fn, 'w', encoding='utf8') as f:
        f.write(data)
        f.close()


def read_file(fn):
    with open(fn, 'r', encoding='utf8') as f:
        data = f.read()
        f.close()
    return data


def str_to_b64(s):
    return base64.b64encode(s.encode('utf8'))


def b64_to_str(b):
    return base64.b64decode(b).decode('utf8')


def remove_script_tag(soup):
    [s.extract() for s in soup.findAll('script')]
    return soup


def detect_lang(text):
    try:
        is_reliable, text_bytes_found, details = cld2.detect(text)
    except:
        text = ''.join(x for x in text if x in string.printable)
        is_reliable, text_bytes_found, details = cld2.detect(text)
    # print('detected: %s' % detectedLangName)
    # print('reliable: %s' % (isReliable != 0))
    # print('textBytes: %s' % textBytesFound)
    # print('details: %s' % str(details))
    return details[0][1]
