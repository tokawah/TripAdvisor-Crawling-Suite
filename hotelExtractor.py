#!/usr/bin/python3
# -*- coding:utf8 -*-
from common import HOTEL_FOLDER
import common
from reviewExtractor import rawReviews, find_rating_value
from os.path import join
import re


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

    def __init__(self, lid, hid):
        self.lid = lid
        self.hid = hid
        hotel_file = join(join(lid, HOTEL_FOLDER), hid + '.txt')
        self.soup = common.load_soup_local(hotel_file)

        # HEADING
        # self.heading = self.soup.find('div', id='HEADING_GROUP')

        # PHOTOS
        self.photos = self.soup.find('div', id='PHOTOS_TAB')

        # AMENITIES
        self.amenities = self.soup.find('div', id='AMENITIES_TAB')

    def get_trace(self):
        traces = []
        nav_bar = self.soup.find(
            'div', id='taplc_breadcrumb_desktop_0')
        for loc in nav_bar.findAll(
                'span', {'itemprop': 'title'}):
            traces.append(loc.getText().strip())
        return traces

    def get_name(self):
        return self.soup.find(
            'h1', id='HEADING').getText().strip()

    def get_address(self):
        add_bar = self.soup.find(
            'div', class_=['header_address', 'address'])
        return ', '.join(
            [x.getText().replace('\n', ' ').replace(',', '').strip()
             for x in add_bar.findAll('span') if x.has_attr('property')])

    def get_rating(self):
        # optional
        rat_bar = self.soup.find(
            'div', class_='rs rating')
        if rat_bar is None:
            rat_bar = self.soup.find(
                'div', {'property': 'aggregateRating'})
        return find_rating_value(rat_bar)

    def get_ranking(self):
        # optional
        rnk_bar = self.soup.find(
            'div', class_='popRanking')
        if rnk_bar is None:
            rnk_bar = self.soup.find(
                'span', class_='header_popularity ')
        return rnk_bar.find(
            'b', class_='rank').getText().strip().replace('#', '')

    def get_hotel_tags(self):
        # optional
        content = self.soup.find('div', id='HR_HACKATHON_CONTENT')
        tag_bar = content.find(
            'div', class_='prw_common_p13n_attributes_on_location_detail')
        hotel_tags = []
        for tag in tag_bar.findAll('span', class_='tag'):
            hotel_tags.append(tag.getText().strip())
        return hotel_tags

    def get_review_highlights(self):
        # optional
        review_bar = self.soup.find(
            'div', id='taplc_prodp13n_hr_sur_review_keyword_search_0')
        highlights = [mention.getText().strip() for
                      mention in review_bar.findAll(
                'span', class_='ui_tagcloud')]
        if len(highlights) > 0:
            highlights.remove('All reviews')
        return highlights

    def get_traveller_photos(self):
        # optional
        traveller_bar = self.photos.find(
            'div', class_='travelerPhotos')
        traveller_photos = []
        for album in traveller_bar.findAll(
                'div', class_='albumCover'):
            traveller_photos.append(' '.join(
                [x.getText().strip() for x in album.findAll('span')]))
        return traveller_photos

    def get_management_photos(self):
        # optional
        management_bar = self.photos.find(
            'div', class_='managementPhotos')
        management_photos = []
        for album in management_bar.findAll(
                'div', class_='albumCover'):
            management_photos.append(' '.join(
                [x.getText().strip() for x in album.findAll('span')]))
        return management_photos

    def get_amenity_tags(self):
        # optional
        highlight_bar = self.amenities.find('div', class_='first')
        amenity_tags = []
        for tag in highlight_bar.findAll('li'):
            amenity_tags.append(tag.getText().strip())
        return amenity_tags

    def get_amenity_categories(self):
        # optional
        cate_bar = self.amenities.find(
            'div', class_='amenity_categories')
        amenity_categories = {}
        for cate in cate_bar.findAll(
                'div', class_='amenity_row'):
            cate_title = cate.find(
                'div', class_='amenity_hdr').getText().strip()
            cate_list = []
            for tag in cate.find(
                    'div', class_='amenity_lst').findAll('li'):
                cate_list.append(tag.getText().strip())
            amenity_categories[cate_title] = cate_list
        return amenity_categories

    def get_description(self):
        # optional
        return self.amenities.find(
            'span', class_='tabs_descriptive_text').getText().strip()

    def get_additional_info(self):
        # optional
        additional_info = self.amenities.find(
            'div', class_='additional_info_amenities').find(
            'div', class_='content').getText().strip()
        additional_info = re.sub(
            '\\s*\\n\\s*', '\n', additional_info)
        return additional_info

    def get_reviews(self):
        # optional
        return rawReviews(self.lid, self.hid)
