#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
from common import REVIEW_FOLDER
from userExtractor import User
from os.path import join
import re


def find_rating_value(value_soup):
    value_bar = value_soup.find(
        ['span', 'div'], class_='ui_bubble_rating')
    return None if value_bar is None else str(float(
        re.sub('\D', '', value_bar['class'][1])) / 10)


class Reviews:
    # travel_type = {'Families', 'Couples', 'Solo', 'Business', 'Friends'}

    def __init__(self, hid):
        self.hid = hid
        review_file = join(join(REVIEW_FOLDER, hid), 'result.txt')
        self.soup = common.load_soup_local(review_file)
        self.reviews = []
        for review_bar in self.soup.findAll(
                'div', class_='reviewSelector'):
            review = _Review(review_bar)
            self.reviews.append(review)
        print('[hotel {}] {} reviews found'.format(
            self.hid, len(self.reviews)))

    def __iter__(self):
        return iter(self.reviews)


class _Review:
    def __init__(self, review_soup):
        # review id
        # len('review_') = 7
        self.rid = review_soup['id'].strip()[7:]

        # user id (optional)
        # len('_UID') =4; len(uid) = 32
        uid_string = review_soup.find(
            'div', class_='member_info').find(
            'div', id=re.compile('^UID_'))
        self.uid = None if uid_string is None \
            else uid_string['id'].strip()[4:36]

        # BUBBLE
        self.bubble = review_soup.find(
            'div', class_='innerBubble').find(
            'div', class_='wrap')

        # RATING
        self.inline = self.bubble.find(
            'div', class_='reviewItemInline')

        # RECOMMEND
        self.rec_bar = self.bubble.find('div', class_='rating-list')
        self.rec_inline = self.rec_bar.find(
            'span', class_='recommend-titleInline').getText().strip()

    def get_title(self):
        return self.bubble.find(
            'div', class_='quote').getText().strip()[1:-1]

    def get_overall_rating(self):
        return find_rating_value(self.inline)

    def get_date(self):
        return self.inline.find(
            'span', class_='ratingDate')['title'].strip()

    def get_content(self):
        return self.bubble.find(
            'div', class_='entry').getText().strip()

    def get_tips(self):
        # optional
        tip_bar = self.bubble.find('div', class_='inlineRoomTip')
        if tip_bar is not None:
            tip_bar.find('div', class_='no_cpu').decompose()
            # len('Room Tip: ') = 10
            tips = tip_bar.getText().strip()[10:]
        else:
            tips = None
        return tips

    def get_stayed_date(self):
        # optional
        rec_date = None if self.rec_bar is None else re.search(
            '(January|February|March|April|'
            'May|June|July|August|September|'
            'October|November|December) \\d{4}', self.rec_inline)
        return None if rec_date is None else rec_date.group(0)

    def get_stayed_type(self):
        # optional
        rec_type = None if self.rec_bar is None else re.search(
            '(?<=travelled ).+', self.rec_inline)
        return None if rec_type is None else rec_type.group(0)

    def get_sub_ratings(self):
        # optional
        sub_ratings = []
        for sub in self.rec_bar.findAll(
                'li', class_='recommend-answer'):
            sub_key = sub.find(
                'div', class_='recommend-description').getText().strip()
            sub_value = find_rating_value(sub)
            sub_ratings.append({sub_key: sub_value})
        return sub_ratings

    def get_thanks(self):
        thank_bar = self.bubble.find(
            'span', class_='helpful_text').find(
            'span', class_='numHlpIn')
        return 0 if thank_bar is None \
            else thank_bar.getText().strip()

    def get_response(self):
        rsp_bar = self.bubble.find('div', class_='mgrRspnInline')
        return None if rsp_bar is None else \
            rsp_bar.getText().strip().replace(
                ', responded to this review', ': ')

    def get_user(self):
        return None if self.uid is None else User(self.uid)
