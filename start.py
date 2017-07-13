import configparser
import logging
import re
import threading
import time
from os.path import isfile

import common
from tadb import tadb

lock = threading.Lock()


def init_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # disable requests logging
    logging.getLogger('requests').setLevel(logging.WARNING)

    # console handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # file handler
    millis = int(round(time.time() * 1000))
    handler = logging.FileHandler(str(millis) + '.log')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')

    # speed parameters
    _ = common
    _.SLEEP_TIME = int(config['DEFAULT']['SleepTime'])
    _.SNIPPET_THREAD_NUM = int(config['DEFAULT']['SnippetThread'])
    _.DETAIL_THREAD_NUM = int(config['DEFAULT']['DetailThread'])
    _.REVIEW_THREAD_NUM = int(config['DEFAULT']['ReviewThread'])
    _.USER_THREAD_NUM = int(config['DEFAULT']['UserThread'])
    logging.info('parameters: [{}; {}; {}; {}; {}]'.format(
        _.SLEEP_TIME, _.SNIPPET_THREAD_NUM, _.DETAIL_THREAD_NUM,
        _.REVIEW_THREAD_NUM, _.USER_THREAD_NUM))

    # location list
    url_list = config['LOCATION']['List'].split(';')
    logging.info('{} locations found'.format(len(url_list)))
    return url_list


if not isfile(common.TA_DB):
    with tadb(common.TA_DB) as db:
        db.create_tables()

init_logger()
urls = load_config()
for url in urls:
    gid = re.sub('\D', '', url)
    # crawlSnippets.start(gid, url.strip())
    # crawlHotels.start(gid)
    # crawlReviews.start(gid)
    # crawlUsers.start()

with tadb(common.TA_DB) as db:
    # db.extract_hotel_info()
    # db.extract_review_info()
    db.extract_user_info()

