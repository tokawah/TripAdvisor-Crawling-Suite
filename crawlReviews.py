import ast
import pickle
from commons import HOTEL_ID, REVIEW_FOLDER, TA_ROOT, SLEEP_TIME
from os.path import isfile, join
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
import requests
from bs4 import BeautifulSoup
import time
import math


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


# premised on non-empty ID list
def get_reviews(id_list):
    #print(id_list)
    nid_list = []
    chunk_size = 500
    slice_num = math.ceil(len(id_list) / chunk_size)
    for slice_pos in range(slice_num):
        spos = slice_pos*chunk_size
        epos = (slice_pos+1)*chunk_size if slice_pos+1 < slice_num else len(id_list)
        id_string = ','.join(id_list[spos: epos])
        print('\tfrom {} to {}'.format(spos+1, epos))
        #nid_list.extend(id_list[spos: epos])
        url = TA_ROOT + '/OverlayWidgetAjax?' \
                        'Mode=EXPANDED_HOTEL_REVIEWS&' \
                        'metaReferer=Hotel_Review' \
                        '&reviews=' + id_string
        web_data = ''
        try:
            web_data = requests.get(url)
        except:
            pass
        soup = BeautifulSoup(web_data.text, 'lxml')
        for div in soup.find_all('div'):
            if div.has_attr('reviewlistingid'):
                #print(nid_list)
                nid_list.append(div['reviewlistingid'])
    if set(id_list) == set(nid_list):
        # and len(id_list) == len(set(id_list))
        return soup.prettify()
    else:
        print('\tcorrupted')
        return None


with open('hids.txt', 'rb') as fp:
    hid_list = [ast.literal_eval(x)[HOTEL_ID] for x in pickle.load(fp)]
    fp.close()

cnt_skip = 0
cnt_get = 0
cnt_blank = 0
for hid_item in hid_list:
    index_dir = join(REVIEW_FOLDER, hid_item)
    index_file = join(index_dir, 'index.txt')
    review_file = join(index_dir, 'result.txt')
    print('hotel {}'.format(hid_item))
    if isfile(review_file):
        print('\tskipped')
        cnt_skip += 1
        continue
    with open(index_file, 'rb') as fp:
        rids = [x for x in pickle.load(fp)]
        fp.close()
    del rids[0]
    #print('{} reviews in hotel {}'.format(len(rids), hid_item))
    if len(rids) == 0:
        print('\tempty')
        cnt_blank += 1
        continue

    result = get_reviews(rids)
    if result is not None:
        with open(review_file, 'w', encoding='utf8') as fp:
            fp.write(result)
            fp.close()
        #print('\tdone')
        cnt_get += 1
    time.sleep(SLEEP_TIME)
print('\r\n\r\n{} hotels, {} obtained, {} skipped, {} blank.'
      .format(len(hid_list), cnt_get, cnt_skip, cnt_blank))

