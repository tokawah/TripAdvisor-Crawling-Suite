#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
from common import HOTEL_PER_PAGE
import re
import math
import threading
import queue
import time
import logging
from tadb import taDB

logger = logging.getLogger()
lock = threading.Lock()


def find_max_page(soup_container):
    div = soup_container.find('div', class_='pageNumbers')
    if div is None:
        return 1
    else:
        num = div.find_all('a')[-1]
        return int(num['data-page-number'])


def find_num_hotels(soup_container):
    div = soup_container.find('fieldset', id='p13n_PROPTYPE_BOX')
    num = div.find('span', class_='tab_count').text
    num = int(re.sub('\D', '', num))
    return num


def start(gid, init_url):
    def gather_hotels(title):
        def calc_max_page(soup_container):
            return math.ceil(find_num_hotels(
                soup_container) / HOTEL_PER_PAGE)

        def find_hotel_ids(url_str):
            soup_container = common.load_soup_online(url_str)
            hdr = soup_container.find('div', class_='hdrTxt')
            if num_page == 1 and hdr is not None:
                divs_soup = hdr.find_all_previous(
                    'div', id=re.compile('^HOTELDEAL\d+'))
            else:
                divs_soup = soup_container.find_all(
                    'div', id=re.compile('^HOTELDEAL\d+'))

            page_pairs = []
            for link in divs_soup:
                # len('HOTELDEAL') = 6
                pair_hid = link['id'][9:]
                pair_url = link.find(
                    'div', class_='listing_title').find('a')['href']
                page_pairs.append({pair_hid: pair_url[1:]})
            return page_pairs

        def update_hotel_ids(new_pairs, pair_list):
            for new_pair in new_pairs:
                pair_key, pair_value = next(iter(new_pair.items()))
                # if hotel id not duplicate
                if pair_key not in pair_list:
                    pair_list[pair_key] = pair_value

        while True:
            # logger.info('[worker {}] running'.format(title))
            pid = que.get()
            if pid is None:
                logger.info('[worker {}] shutting down'.format(title))
                break
            paras = '&'.join([
                'seen=0', 'sequence=1', 'geo=' + gid,
                'requestingServlet=Hotels', 'refineForm=true',
                'hs=', 'adults=2', 'rooms=1',
                                        'o=a' + str(pid * HOTEL_PER_PAGE),
                'pageSize=&rad=0', 'dateBumped=NONE',
                'displayedSortOrder=popularity'])
            page_url = ''.join([init_url, '?', paras])
            logger.info('[page {}] {}'.format(pid + 1, page_url))
            # print('aa')
            hotels = find_hotel_ids(page_url)
            # print('bb')
            if hotels is None:
                que.put(pid)
            elif len(hotels) < HOTEL_PER_PAGE and pid < num_page - 1:
                que.put(pid)
            elif pid == num_page - 1 \
                    and len(hotels) < num_hotel % HOTEL_PER_PAGE:
                que.put(pid)
            else:
                with lock:
                    update_hotel_ids(hotels, hid_pairs)
                    logger.info('\t#{}, totaling {}'.format(pid, len(hid_pairs)))
                    with taDB(common.TA_DB) as db:
                        record = [gid, str(hid_pairs)]
                        db.insert_a_location(record)

            time.sleep(common.SLEEP_TIME)
            que.task_done()

    loc_name = init_url[init_url.index(gid) + len(gid) + 1:init_url.rindex('-')]
    logger.info('[location {}] {}'.format(gid, loc_name.replace('_', ' ')))
    soup = common.load_soup_online(init_url)
    num_page = find_max_page(soup)
    num_hotel = find_num_hotels(soup)
    logger.info('{} hotels in {} pages'.format(num_hotel, num_page))

    with taDB(common.TA_DB) as iodb:
        hid_pairs = iodb.get_hotel_url_pairs(gid)
    logger.info('{} hotels in local cache'.format(len(hid_pairs)))

    # collecting hotel ids might take multiple iterations
    while len(hid_pairs) < num_hotel:
        que = queue.Queue()

        threads = []
        thread_size = common.SNIPPET_THREAD_NUM
        for j in range(thread_size):
            t = threading.Thread(
                target=gather_hotels, args=(str(j + 1))
            )
            t.start()
            threads.append(t)

        # set start value to math.ceil(len(hid_pairs) / HOTEL_PER_PAGE)
        # rather than 0 if the hotels are ordered in the list
        [que.put(x) for x in range(0, num_page)]

        que.join()

        for k in range(thread_size):
            que.put(None)
        for t in threads:
            t.join()

    logger.info('all hotel ids are ready'.format(len(hid_pairs)))
