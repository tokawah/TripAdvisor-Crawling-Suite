#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
from common import HOTEL_PER_PAGE
from os.path import isfile, join
import re
import math
import threading
import queue
import time
import ast
import logging
import os

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


def start(seed):
    def gather_hotels(title):
        def calc_max_page(soup_container):
            return math.ceil(find_num_hotels(
                soup_container) / HOTEL_PER_PAGE)

        def find_hotel_ids(url_str):
            def get_id_url_pair(divs_soup):
                page_pairs = []
                for link in divs_soup:
                    # len('hotel_') = 6
                    pair_hid = link['id'][6:]
                    pair_snippet = link.find(
                        'div', class_='metaLocationInfo')
                    if pair_snippet is None:
                        return None
                    pair_url = pair_snippet.find(
                        'div', class_='listing_title').find('a')['href']
                    page_pairs.append({pair_hid: pair_url[1:]})
                return page_pairs

            soup_container = common.load_soup_online(url_str)
            hdr = soup_container.find('div', class_='hdrTxt')
            while True:
                divs = hdr.findAllPrevious(
                    'div', id=re.compile('^hotel_')) \
                    if numPage == 1 and hdr is not None \
                    else soup_container.findAll(
                    'div', id=re.compile('^hotel_'))
                page_hotels = get_id_url_pair(divs)
                if page_hotels is not None:
                    return page_hotels

        def update_hotel_ids(new_pairs, pair_list):
            for new_pair in new_pairs:
                pair_key, pair_value = next(iter(new_pair.items()))
                # if hotel id not duplicate
                if pair_key not in pair_list:
                    pair_list[pair_key] = pair_value

        while True:
            logger.info('[worker {}] running'.format(title))
            pid = que.get()
            if pid is None:
                logger.info('[worker {}] shutting down'.format(title))
                break
            paras = '&'.join([
                'seen=0', 'sequence=1', 'geo=' + locID,
                'requestingServlet=Hotels', 'refineForm=true',
                'hs=', 'adults=2', 'rooms=1',
                                        'o=a' + str(pid * HOTEL_PER_PAGE),
                'pageSize=&rad=0', 'dateBumped=NONE',
                'displayedSortOrder=popularity'])
            page_url = ''.join([seed, '?', paras])
            logger.info('[page {}] {}'.format(pid + 1, page_url))
            hotels = find_hotel_ids(page_url)
            if len(hotels) < HOTEL_PER_PAGE and pid < numPage - 1:
                que.put(pid)
            elif pid == numPage - 1 \
                    and len(hotels) < numHotel % HOTEL_PER_PAGE:
                que.put(pid)
            else:
                with lock:
                    update_hotel_ids(hotels, hidPairs)
                    logger.info('\t#{}, totaling {}'.format(pid, len(hidPairs)))
                    common.write_file(
                        join(locID, 'hids.txt'), str(hidPairs))

            time.sleep(common.SLEEP_TIME)
            que.task_done()

    # seed = input('url: ')
    locID = re.sub('\D', '', seed)
    locName = seed[seed.index(locID) + len(locID) + 1:seed.rindex('-')]
    logger.info('[location] {} ({})'.format(locName.replace('_', ' '), locID))
    soup = common.load_soup_online(seed)
    numPage = find_max_page(soup)
    numHotel = find_num_hotels(soup)
    logger.info('{} hotels in {} pages'.format(numHotel, numPage))

    hid_file = join(locID, 'hids.txt')
    if not isfile(hid_file):
        common.write_file(hid_file, '{}')
    hidPairs = ast.literal_eval(common.read_file(hid_file))
    logger.info('{} hotels in the local list'.format(len(hidPairs)))

    # collecting hotel ids might take multiple iterations
    if len(hidPairs) < numHotel:
        if isfile(join(locID, 'ok')):
            os.remove(join(locID, 'ok'))
            print('del ok')

    while len(hidPairs) < numHotel:
        que = queue.Queue()

        threads = []
        thread_size = min(common.SNIPPET_THREAD_NUM, numPage)
        for j in range(thread_size):
            t = threading.Thread(
                target=gather_hotels, args=(str(j + 1))
            )
            t.start()
            threads.append(t)

        # push items into the queue
        # set start value to math.ceil(len(hidPairs) / HOTEL_PER_PAGE)
        # rather than 0 if the hotels are ordered in the list
        [que.put(x) for x in range(0, numPage)]

        # block until all tasks are done
        que.join()

        # stop workers
        for k in range(thread_size):
            que.put(None)
        for t in threads:
            t.join()

    logger.info('all hotel ids are ready'.format(len(hidPairs)))
