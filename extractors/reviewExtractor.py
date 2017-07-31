#!/usr/bin/python3
# -*- coding:utf8 -*-
import re
import common


def calc_rating_value(value_str):
    return str(float(re.sub('\D', '', value_str)) / 10)


def find_rating_value(value_soup):
    value_bar = value_soup.find(
        ['span', 'div'], class_='ui_bubble_rating')
    if value_bar is None:
        return -1
    else:
        return calc_rating_value(value_bar['class'][1])


class rawReview:
    def __init__(self, html):
        self._review_soup = common.load_soup_string(
            html).find('div', class_='reviewSelector')

        # review id
        # len('review_') = 7
        self.rid = self._review_soup['id'].strip()[7:]

        # user id (optional)
        # len('_UID') =4; len(uid) = 32
        uid_string = self._review_soup.find(
            'div', class_='member_info').find(
            'div', id=re.compile('^UID_'))
        self.uid = None
        if uid_string is not None:
            self.uid = uid_string['id'].strip()[4:36]

        # BUBBLE
        self._bubble = self._review_soup.find(
            'div', class_='innerBubble').find(
            'div', class_='wrap')

        # RATING
        self._inline = self._bubble.find(
            'div', class_='reviewItemInline')

        # RECOMMEND
        self._rec_bar = self._bubble.find(
            'div', class_='rating-list')

    def get_html(self):
        return str(self._review_soup)

    def get_title(self):
        # 'quote' may have been deprecated
        return self._bubble.find(
            'div', class_=['quote', 'noQuotes']).getText().strip()

    def get_rating(self):
        return find_rating_value(self._inline)

    def get_date(self):
        date_bar = self._inline.find(
            'span', class_='ratingDate')
        if date_bar is not None:
            return date_bar['title'].strip()
        return None

    def get_content(self):
        return self._bubble.find(
            'div', class_='entry').getText().strip()

    def get_tips(self):
        # optional
        tip_bar = self._bubble.find('div', class_='inlineRoomTip')
        tips = None
        if tip_bar is not None:
            tip_bar.find('div', class_='no_cpu').decompose()
            # len('Room Tip: ') = 10
            tips = tip_bar.getText().strip()[10:]
        return tips

    def get_stayed_date(self):
        # optional
        if self._rec_bar is not None:
            rec_inline = self._rec_bar.find(
                'span', class_='recommend-titleInline')
            if rec_inline is not None:
                rec_date = re.search(
                    '(January|February|March|April|'
                    'May|June|July|August|September|'
                    'October|November|December) \\d{4}',
                    rec_inline.getText())
                if rec_date is not None:
                    return rec_date.group(0)
        return None

    def get_stayed_type(self):
        # optional
        if self._rec_bar is not None:
            rec_inline = self._rec_bar.find(
                'span', class_='recommend-titleInline')
            if rec_inline is not None:
                rec_type = re.search(
                    '(?<=travelled ).+', rec_inline.getText())
                if rec_type is not None:
                    return rec_type.group(0)
        return None

    def get_sub_ratings(self):
        # optional
        if self._rec_bar is not None:
            sub_ratings = []
            for sub in self._rec_bar.find_all(
                    'li', class_='recommend-answer'):
                sub_key = sub.find(
                    'div', class_='recommend-description').getText().strip()
                sub_value = find_rating_value(sub)
                sub_ratings.append({sub_key: sub_value})
            if len(sub_ratings) > 0:
                return sub_ratings
        return None

    def get_thanks(self):
        thank_bar = self._bubble.find(
            # 'span', class_='helpful_text').find(
            'span', class_='numHelp')
        if thank_bar is not None:
            thank_val = thank_bar.getText().strip()
            if len(thank_val) > 0:
                return thank_val
        return 0

    def get_response(self):
        rsp_bar = self._bubble.find('div', class_='mgrRspnInline')
        if rsp_bar is not None:
            return rsp_bar.getText().strip().replace(
                ', responded to this review', ': ')
        return None
