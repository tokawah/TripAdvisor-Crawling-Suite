#!/usr/bin/python3
# -*- coding:utf8 -*-
from common import HOTEL_FOLDER, REVIEW_FOLDER, USER_FOLDER
import common
from os.path import join
import re


class UserExtractor:
    def __init__(self, uid):
        user_file = join(USER_FOLDER, uid + '.txt')
        user_soup = common.load_soup_local(user_file)

        # user name
        self.name = user_soup.find(
            'h3', class_='username').getText().strip()

        # user description
        des_bar = user_soup.find('ul', class_='memberdescription')
        self.descriptions = []
        for item in des_bar.findAll('li'):
            self.descriptions.append(item.getText().strip())

        # counts
        count_bar = user_soup.find('div', class_='lowerMemberOverlay')
        self.counts = {}
        for item in count_bar.findAll('li'):
            links = item.findAll('a')
            item_value = links[0].getText().strip()
            item_key = links[1].getText().strip()
            self.counts[item_key] = item_value

        # review distribution (option)
        dist_bar = user_soup.find('ul', class_='barchartmemoverlay')
        self.review_distribution = {}
        if dist_bar is None:
            self.review_distribution = None
        else:
            for item in dist_bar.findAll('div', class_='wrap'):
                item_key = item.find(
                    'span', class_='text').getText().strip()
                item_value = re.sub('\D', '', item.find(
                    'span', class_='numbersText').getText().strip())
                self.review_distribution[item_key] = item_value

        # LEFT PROFILE
        left_profile = user_soup.find('div', class_='leftProfile')

        # age since
        self.age_since = left_profile.find(
            'div', class_='ageSince').getText().strip()
        self.age_since = re.sub('\\s*\\n\\s*', '\n', self.age_since)

        # home town
        self.hometown = left_profile.find(
            'div', class_='hometown').getText().strip()

        # points
        stat_bar = left_profile.find('div', class_='member-points')
        self.stats = {}
        for item in stat_bar.findAll('li'):
            link = item.find('a').getText().strip()
            item_value = link[0:link.index(' ')]
            item_key = link[link.index(' ') + 1:]
            self.stats[item_key] = item_value

        tag_bar = left_profile.find('div', class_='tagBlock')
        self.tags = []
        for tag in tag_bar.findAll('div', class_='unclickable'):
            self.tags.append(tag.getText().strip())

        # RIGHT CONTRIBUTIONS
        right_con = user_soup.find('div', class_='rightContributions')

        # total point
        self.total_point = right_con.find(
            'div', class_='modules-membercenter-total-points ').find(
            'div', class_='points').getText().strip().replace(',', '')

        # level (option)
        level = right_con.find(
            'div', class_='modules-membercenter-level ').find('span')
        self.level = None if level is None else level.getText().strip()

        # badges (optional)
        self.badges = []
        badge_bar = right_con.find(
            'div', class_='modules-membercenter-badge-flyout ')
        for badge in badge_bar.find(
                'div', class_='hidden').findAll(
                'div', attrs={'data-badge-id': True}):
            if badge.find('a') is None:
                self.badges.append(badge.find(
                    'div', class_='text').getText().strip())

    def get_user_name(self):
        return self.name

    def get_user_descriptions(self):
        return self.descriptions

    def get_counts(self):
        return self.counts

    def get_review_distribution(self):
        return self.review_distribution

    def get_age_since(self):
        return self.age_since

    def get_hometown(self):
        return self.hometown

    def get_stats(self):
        return self.stats

    def get_tags(self):
        return self.tags

    def get_total_point(self):
        return self.total_point

    def get_level(self):
        return self.level

    def get_badges(self):
        return self.badges
