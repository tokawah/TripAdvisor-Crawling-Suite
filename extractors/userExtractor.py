#!/usr/bin/python3
# -*- coding:utf8 -*-
import common
import re

class rawUser:
    def __init__(self, html):
        self.soup = common.load_soup_string(html)

        # OVERLAY
        self.overlay = self.soup.find(
            'div', class_='memberOverlay')

        # LEFT PROFILE
        self.left_profile = self.soup.find(
            'div', class_='leftProfile')

        # RIGHT CONTRIBUTIONS
        self.right_con = self.soup.find(
            'div', class_='rightContributions')

    def get_html(self):
        return str(self.soup)

    def get_name(self):
        return self.overlay.find(
            'h3', class_='username').getText().strip()

    def get_descriptions(self):
        # optional
        des_bar = self.overlay.find(
            'ul', class_=['memberdescription',
                          'memberdescriptionReviewEnhancements'])
        if des_bar is not None:
            return [item.getText().strip()
                    for item in des_bar.findAll('li')]
        return None

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
            'div', class_=['reviewchart', 'histogramReviewEnhancements'])
        if dist_bar is not None:
            dist = {}
            for item in dist_bar.findAll(
                    'div', class_=['wrap',
                                   'chartRowReviewEnhancements']):
                item_key = re.sub('[^a-zA-Z]', '', item.getText())
                item_value = re.sub('\D', '', item.getText())
                dist[item_key] = item_value
            return dist
        return None

    def get_registration_year(self):
        reg_bar = self.left_profile.find(
            'div', class_='ageSince')
        since = reg_bar.find('p', class_='since')
        reg_year = [since.getText().strip()]
        since.decompose()
        reg_year.extend(
            [x.getText().strip()
             for x in reg_bar.findAll('p')])
        return reg_year

    def get_hometown(self):
        return self.left_profile.find(
            'div', class_='hometown').getText().strip()

    def get_stats(self):
        stat_bar = self.left_profile.find('div', class_='member-points')
        if stat_bar is not None:
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
        return None

    def get_tags(self):
        # optional
        tag_bar = self.left_profile.find('div', class_='tagBlock')
        if tag_bar is not None:
            tags = []
            for tag in tag_bar.findAll('div', class_='unclickable'):
                tags.append(tag.getText().strip())
            return tags
        return None

    def get_total_point(self):
        return self.right_con.find(
            'div', class_='modules-membercenter-total-points ').find(
            'div', class_='points').getText().strip().replace(',', '')

    def get_level(self):
        # optional
        level = self.right_con.find(
            'div', class_='modules-membercenter-level ').find('span')
        return -1 if level is None else level.getText().strip()

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
