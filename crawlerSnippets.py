#!/usr/bin/python3
# -*- coding:utf8 -*-

from os.path import isfile, join
from bs4 import BeautifulSoup
import requests
import time
import re
import ast
import commons
from commons import TA_ROOT
from commons import JSON_FOLDER
from commons import SLEEP_TIME
from commons import HOTEL_ID
from commons import HOTEL_URL
#from commons import HOTEL_SNIPPET
#from commons import HOTEL_DETAIL
import pickle
import math


def find_hotel_ids(soup_container):
    page_hotels = []
    for link in soup_container.find_all('div', id=re.compile('^hotel_')):
        if link.has_attr('id'):
            hid = link['id'][6:]
            # print('\tfound the snippet for {}'.format(hid))
            snippet = link.select('.metaLocationInfo')[0]
            url = snippet.select('.listing_title')[0].find('a')['href']
            time.sleep(SLEEP_TIME)
            page_hotels.append({HOTEL_ID: hid, HOTEL_URL: url})
    print('\t\t{} hotels'.format(len(page_hotels)))
    return page_hotels


def update_hotel_ids(new_pairs, pair_list):
    for new_pair in new_pairs:
        if not has_pair(new_pair[HOTEL_ID], pair_list):
            pair_list.extend(new_pair)
    return pair_list


def has_pair(id_value, pairs):
    for hid in pairs:
        if ast.literal_eval(hid)[HOTEL_ID] == id_value:
            return True
    return False


def find_max_page(soup_container):
    div = soup_container.find('div', class_='pageNumbers')
    num = div.find_all('a')[-1]
    return int(num['data-page-number'])


def calc_max_page(soup_container):
    return math.ceil(find_num_hotels(soup_container) / 30)


def find_num_hotels(soup_container):
    div = soup_container.find('fieldset', id='p13n_PROPTYPE_BOX')
    num = div.find('span', class_='tab_count').text
    num = int(num.replace('(', '').replace(')', ''))
    return num



# fg
with open('hids.txt', 'rb') as fp:
    hid_pair_list = [x for x in pickle.load(fp)]
    fp.close()

hotel_list_url = TA_ROOT + '/Hotels-g294212-Beijing-Hotels.html'
soup = commons.load_soup_online(hotel_list_url)

max_page = find_max_page(soup)
num_hotels = find_num_hotels(soup)

print('{} hotels in {} pages'.format(num_hotels, max_page))
hotels = find_hotel_ids(soup)
if max_page == calc_max_page(soup):
    for i in range(2, max_page + 1):
        hotel_detail_url = TA_ROOT + '/Hotels-g294212-oa' + \
                           str((i - 1) * 30) + '-Beijing-Hotels.html'
        time.sleep(SLEEP_TIME)
        print('\tpage {}'.format(i))
        web_data = requests.get(hotel_detail_url)  # , headers=headers
        soup = BeautifulSoup(web_data.text, 'lxml')
        hotels = find_hotel_ids(soup)
        hid_pair_list = update_hotel_ids(hotels, hid_pair_list)
        print(len(hotels))

#with open('hids.txt', 'wb') as fp:
    #pickle.dump(hid_list, fp)
    # fp.close()
print('{} hotels found'.format(hid_pair_list))
