import common
# from common import SLEEP_TIME
# from common import SNIPPET_THREAD_NUM, DETAIL_THREAD_NUM
# from common import REVIEW_THREAD_NUM, USER_THREAD_NUM
# from common import HOTEL_FOLDER, REVIEW_FOLDER, USER_FOLDER
import configparser
import re
import os
from os.path import join
import logging
import time
import crawlSnippets
import crawlDetails
import crawlReviews
import crawlUsers


def init_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

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

init_logger()
urls = load_config()
for url in urls:
    locID = re.sub('\D', '', url)
    if not os.path.exists(locID):
        os.makedirs(locID)
        os.makedirs(join(locID, common.HOTEL_FOLDER))
        os.makedirs(join(locID, common.REVIEW_FOLDER))
        os.makedirs(join(locID, common.USER_FOLDER))
    crawlSnippets.start(url.strip())
    if not os.path.isfile(join(locID, 'ok')):
        crawlDetails.start(locID)
        crawlReviews.start(locID)
    # crawlUsers.start(locID)

