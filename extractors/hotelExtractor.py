#!/usr/bin/python3
# -*- coding:utf8 -*-
import json
import re
import common


class rawHotel:
    # style_set = {'quiet', 'all inclusive', 'best value',
    #           'boutique', 'budget', 'business',
    #           'charming', 'classic', 'family-friendly',
    #           'luxury', 'mid-range', 'quaint',
    #           'resort hotel', 'romantic', 'trendy'}
    #
    # amenity_set = {'air conditioning', 'airport transportation',
    #              'bar/lounge', 'beach', 'breakfast included',
    #              'business services', 'casino', 'concierge',
    #              'fitness centre', 'free parking', 'free wifi',
    #              'golf course', 'internet', 'kitchenette',
    #              'meeting room', 'non-smoking hotel',
    #              'pets allowed', 'pool', 'reduced mobility rooms',
    #              'restaurant', 'room service', 'spa', 'suites',
    #              'wheelchair access'}

    def __init__(self, html):
        self._soup = common.load_soup_string(html)
        # JSON
        self._json = json.loads(str(self._soup.find(
            'script', type='application/ld+json').getText()))

    def get_html(self):
        return str(self._soup)

    def get_trace(self):
        traces = []
        nav_bar = self._soup.find(
            'div', id=['taplc_breadcrumb_desktop_0',
                       'taplc_global_nav_onpage_assets_0'])
        for loc in nav_bar.findAll(
                'span', {'itemprop': 'title'}):
            traces.append(loc.getText().strip())
        return traces if len(traces) > 0 else None

    def get_name(self):
        return self._json['name']

    def get_address(self):
        addr_list = [self._json['address']['streetAddress'],
                     self._json['address']['addressLocality'],
                     self._json['address']['addressRegion'],
                     self._json['address']['postalCode'],
                     self._json['address']['addressCountry']['name']]
        addr_list = list(filter(None, addr_list))
        return ', '.join(addr_list)

    def get_coords(self):
        lat = re.search('(?<=lat:\s)[0-9.]+(?=,)', str(self._soup))
        lng = re.search('(?<=lng:\s)[0-9.]+(?=,)', str(self._soup))
        if lat is not None and lng is not None:
            return [lat.group(0), lng.group(0)]
        return None

    def get_type(self):
        type_str = re.search(
            '(?<=\"HotelType\" : \[)[\w\"\n,\s]+(?=\])',
            str(self._soup))
        if type_str is not None:
            type_str = type_str.group(0).replace('\n', '')
            type_lst = []
            for itype in type_str.split(','):
                type_lst.append(itype[itype.index('"') + 1: -1])
            if len(type_lst) > 0:
                type_lst.remove('hotels')
            return type_lst
        return None

    def get_star(self):
        star = re.search(
            '(?<=\"HotelStarRating\" : \[\n\")\d+(?=\")',
            str(self._soup))
        return -1 if star is None else star.group(0)

    def get_style(self):
        style_str = re.search(
            '(?<=\"HotelStyle\" : \[)[\w\"\n,\s]+(?=\])',
            str(self._soup))
        if style_str is not None:
            style_str = style_str.group(0).replace('\n', '')
            style_lst = []
            for style in style_str.split(','):
                style_lst.append(style[style.index('"')+1: -1])
            return style_lst
        return None

    def get_rating(self):
        if 'aggregateRating' in self._json:
            rat_bar = self._json['aggregateRating']
            if rat_bar is not None:
                return rat_bar['ratingValue']
        return -1

    def get_ranking(self):
        # optional
        rnk_bar = self._soup.find('b', class_='rank')
        if rnk_bar is not None:
            return re.sub('\D', '', rnk_bar.getText().strip())
        return -1

    def get_highlights(self):
        # optional
        review_bar = self._soup.find(
            'div', id=['taplc_location_review_keyword_search_hotels_0',
                       'taplc_prodp13n_hr_sur_review_keyword_search_0'])
        if review_bar is not None:
            highlights = [mention.getText().strip() for
                          mention in review_bar.findAll(
                    'span', class_='ui_tagcloud')]
            if len(highlights) > 1:
                highlights.remove('All reviews')
            return highlights
        return None

    def get_photo_list(self):
        photos = self._soup.find(
            'div', id='taplc_hr_btf_north_star_photos_0')
        return [x.getText().strip() for x in photos.findAll(
            'div', class_=['albumInfo', 'albumName'])]
