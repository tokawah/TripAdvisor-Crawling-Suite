#!/usr/bin/python3
# -*- coding:utf8 -*-
import base64
from bs4 import BeautifulSoup
import requests
import pickle

SLEEP_TIME = 2
SNIPPET_THREAD_NUM = 3
DETAIL_THREAD_NUM = 3
REVIEW_THREAD_NUM = 3
USER_THREAD_NUM = 3

HOTEL_PER_PAGE = 30
REVIEW_PER_PAGE = 10

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
