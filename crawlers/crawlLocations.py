#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
import re
import logging

logger = logging.getLogger()


def find_max_page(soup_container):
    div = soup_container.find('div', class_='pageNumbers')
    if div is None:
        return 1
    else:
        num = div.find_all('a')[-1]
        return int(num['data-page-number'])

urls = []
init_url = input('specify an area: ')
url_pattern = re.search(r'-g\d+-', init_url)
url_pos = url_pattern.start() + len(url_pattern.group(0))
page_number = find_max_page(common.load_soup_online(init_url))
print('locations in {} pages.'.format(page_number))
for idx_page in range(page_number):
    page_url = init_url if idx_page == 0 else ''.join(
            [init_url[:url_pos], 'oa', str(idx_page * 20),
             '-', init_url[url_pos:]])
    print('[page {}] {}'.format(idx_page + 1, page_url))
    soup = common.load_soup_online(page_url)
    for hotel in soup.findAll('div', class_='geo_name'):
        a = hotel.find('a')
        a = common.TA_ROOT + a['href'][1:]
        urls.append(a)
urls = list(set(urls))
print('{} locations found.'.format(len(urls)))
print('configuration string:\n{}'.format(';'.join(urls)))
