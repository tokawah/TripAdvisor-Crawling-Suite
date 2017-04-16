#!/usr/bin/python3
# -*- coding:utf8 -*-

import json
import os
import base64
from os import listdir
from os.path import isfile, join
from bs4 import BeautifulSoup
import requests
import re


JSON_FOLDER = 'jsons'
REVIEW_FOLDER = 'reviews'
USER_FOLDER = 'users'
SLEEP_TIME = 4
FORCE_UPDATE = True

TA_ROOT = 'https://www.tripadvisor.com.au'
HOTEL_ID = 'id'
HOTEL_URL = 'url'
HOTEL_SNIPPET = 'snippet'
HOTEL_DETAIL = 'detail'


import psutil
def kill_process(proc_name):
    for proc in psutil.process_iter():
        if proc.name == proc_name:
            proc.kill()


def load_soup_local(file_name):
    file = open(file_name, 'r', encoding="utf8").read()
    return BeautifulSoup(file, 'lxml')


def load_soup_online(soup_url):
    data = requests.get(soup_url)  # , headers=headers, verify=False
    return BeautifulSoup(data.text, 'lxml')


def json_write1(fn, data):
    with open(fn, 'w') as f:
        json.dump(str(data), f)#, ensure_ascii=False).encode('utf8'


def json_read1(fn):
    with open(fn, 'r') as f:
        return json.load(f)


def get_file_list(pattern):
    cwd = os.getcwd()
    #files = [f for f in listdir(path) if isfile(join(path, f))]
    print(os.listdir('.'))
    files = [f for f in cwd if re.match(pattern, f)]
    return files


#def create_dir_if_not_exist


def stringToBase64(s):
    return base64.b64encode(s.encode('utf-8'))


def base64ToString(b):
    return base64.b64decode(b).decode('utf-8')
