#!/usr/bin/python3
# -*- coding:utf8 -*-
from common import USER_FOLDER
import common
from os.path import join
import re


class rawUser:
    def __init__(self, hid, uid):
        user_file = join(join(hid, USER_FOLDER), uid + '.txt')
        self.soup = common.load_soup_local(user_file)

        # OVERLAY
        self.overlay = self.soup.find('div', class_='memberOverlay')

        # LEFT PROFILE
        self.left_profile = self.soup.find('div', class_='leftProfile')

        # RIGHT CONTRIBUTIONS
        self.right_con = self.soup.find('div', class_='rightContributions')

    def get_user_name(self):
        return self.overlay.find(
            'h3', class_='username').getText().strip()

    def get_user_descriptions(self):
        # optional
        des_bar = self.overlay.find(
            'ul', class_=['memberdescription',
                          'memberdescriptionReviewEnhancements'])
        if des_bar is None:
            return None
        else:
            descriptions = []
            for item in des_bar.findAll('li'):
                descriptions.append(item.getText().strip())
            return descriptions

    def get_basic_stats(self):
        count_bar = self.overlay.find(
            'ul', class_=['counts', 'countsReviewEnhancements'])
        counts = {}
        for item in count_bar.findAll('li'):
            item_text = item.getText().strip()
            item_value = re.sub('\D', '', item_text).strip()
            item_key = re.sub('\d', '', item_text).strip()
            counts[item_key] = item_value
        return counts

    def get_review_distribution(self):
        # optional
        dist_bar = self.overlay.find(
            'div', class_=['row',
                          'chartRowReviewEnhancements'])
        if dist_bar is None:
            return None
        else:
            review_distribution = {}
            for item in dist_bar.findAll('div', class_='wrap'):
                item_key = item.find(
                    'span', class_=['rowLabelReviewEnhancements',
                                    'text']).getText().strip()
                item_value = re.sub('\D', '', item.find(
                    'span', class_=['rowCountReviewEnhancements',
                                    'numbersText']).getText().strip())
                review_distribution[item_key] = item_value
            return review_distribution

    def get_age_since(self):
        reg_bar = self.left_profile.find(
            'div', class_='ageSince')
        since = reg_bar.find('p', class_='since')
        reg_time = since.getText().strip()
        since.extract()
        age = [x.getText().strip() for x in reg_bar.findAll('p')]
        return reg_time if not age else \
            ''.join([reg_time, ' (', ';'.join(age), ')'])

    def get_hometown(self):
        return self.left_profile.find(
            'div', class_='hometown').getText().strip()

    def get_stats(self):
        stat_bar = self.left_profile.find('div', class_='member-points')
        stats = {}
        for item in stat_bar.findAll('li'):
            link = item.find('a')
            if link is None:
                continue
            link = link.getText().strip()
            item_value = link[0:link.index(' ')]
            item_key = link[link.index(' ') + 1:]
            stats[item_key] = item_value
        return stats

    def get_tags(self):
        # optional
        tag_bar = self.left_profile.find('div', class_='tagBlock')
        if tag_bar is None:
            return None
        else:
            tags = []
            for tag in tag_bar.findAll('div', class_='unclickable'):
                tags.append(tag.getText().strip())
            return tags

    def get_total_point(self):
        return self.right_con.find(
            'div', class_='modules-membercenter-total-points ').find(
            'div', class_='points').getText().strip().replace(',', '')

    def get_level(self):
        # optional
        level = self.right_con.find(
            'div', class_='modules-membercenter-level ').find('span')
        return None if level is None else level.getText().strip()

    def get_badges(self):
        # optional
        badges = []
        badge_bar = self.right_con.find(
            'div', class_='modules-membercenter-badge-flyout ')
        for badge in badge_bar.find(
                'div', class_='hidden').findAll(
                'div', attrs={'data-badge-id': True}):
            if badge.find('a') is None:
                badges.append(badge.find(
                    'div', class_='text').getText().strip())
        return badges