#!/usr/bin/python3
# -*- coding:utf8 -*-
from common import HOTEL_FOLDER, REVIEW_FOLDER, USER_FOLDER
import common
from os.path import join
import re


class MetaExtractor:
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

    def __init__(self, hid):
        hotel_file = join(HOTEL_FOLDER, hid + '.txt')
        hotel_soup = common.load_soup_local(hotel_file)

        # hotel trace
        self.traces = []
        nav_bar = hotel_soup.find(
            'div', id='taplc_breadcrumb_desktop_0')
        for loc in nav_bar.findAll(
                'span', {'itemprop': 'title'}):
            self.traces.append(loc.getText().strip())

        # HEADING
        heading = hotel_soup.find('div', id='HEADING_GROUP')

        # hotel name
        self.name = heading.find('h1', id='HEADING').getText().strip()

        # hotel address
        add_bar = heading.find('span', class_='format_address')
        self.address = ', '.join([x.getText().strip().replace(',', '')
                                  for x in add_bar.findAll('span')])

        # hotel overall rating (optional)
        rat_bar = heading.find('div', {'property': 'aggregateRating'})
        rat_item = rat_bar.find('span', class_='ui_bubble_rating')
        self.rating = '-1' if rat_item is None else rat_item['content']

        # hotel rank (optional)
        self.rank = heading.find(
            'b', class_='rank').getText().strip().replace('#', '')

        # CONTENT
        content = hotel_soup.find('div', id='HR_HACKATHON_CONTENT')

        # hotel tags (optional)
        tag_bar = content.find(
            'div', class_='prw_common_p13n_attributes_on_location_detail')
        self.hotel_tags = []
        for tag in tag_bar.findAll('span', class_='tag'):
            self.hotel_tags.append(tag.getText().strip())

        # PHOTOS
        photos = hotel_soup.find('div', id='PHOTOS_TAB')

        # traveller photos (optional)
        traveller_bar = photos.find('div', class_='travelerPhotos')
        self.traveller_photos = []
        for album in traveller_bar.findAll('div', class_='albumCover'):
            self.traveller_photos.append(' '.join(
                [x.getText().strip() for x in album.findAll('span')]))

        # management photos (optional)
        management_bar = photos.find('div', class_='managementPhotos')
        self.management_photos = []
        for album in management_bar.findAll('div', class_='albumCover'):
            self.management_photos.append(' '.join(
                [x.getText().strip() for x in album.findAll('span')]))

        # AMENITIES
        amenities = hotel_soup.find('div', id='AMENITIES_TAB')

        # amenity tags (optional)
        highlight_bar = amenities.find('div', class_='first')
        self.amenity_tags = []
        for tag in highlight_bar.findAll('li'):
            self.amenity_tags.append(tag.getText().strip())

        # amenity categories (optional)
        cate_bar = amenities.find('div', class_='amenity_categories')
        self.amenity_categories = {}
        for cate in cate_bar.findAll('div', class_='amenity_row'):
            cate_title = cate.find(
                'div', class_='amenity_hdr').getText().strip()
            cate_list = []
            for tag in cate.find('div', class_='amenity_lst').findAll('li'):
                cate_list.append(tag.getText().strip())
            self.amenity_categories[cate_title] = cate_list

        # official description (optional)
        self.description = amenities.find(
            'span', class_='tabs_descriptive_text').getText().strip()

        # additional information (optional)
        self.additional_info = amenities.find(
            'div', class_='additional_info_amenities').find(
            'div', class_='content').getText().strip()
        self.additional_info = re.sub(
            '\\s*\\n\\s*', '\n', self.additional_info)

    def get_trace(self):
        return self.traces

    def get_name(self):
        return self.name

    def get_address(self):
        return self.address

    def get_rating(self):
        return self.rating

    def get_ranking(self):
        return self.rank

    def get_hotel_tags(self):
        return self.hotel_tags

    def get_amenity_tags(self):
        return self.amenity_tags

    def get_amenity_categories(self):
        return self.amenity_categories

    def get_description(self):
        return self.description

    def get_additional_info(self):
        return self.additional_info

    def get_traveller_photos(self):
        return self.traveller_photos

    def get_management_photos(self):
        return self.management_photos
