import xml.etree.ElementTree as ET
import xmlExporter
import json
from geopy.geocoders import Nominatim
import re
from datetime import datetime


def parse_date(date):
    date = str(date)
    month = re.search(
            '(January|February|March|April|'
            'May|June|July|August|September|'
            'October|November|December)', date)
    year = re.search('\\d{4}', date)
    if year is not None and month is not None:
        year = year.group(0)
        if int(year) <= datetime.now().year:
            # print('{} {}'.format(year, month))
            return year, month.group(0)
    return None, None


class _xmlReview():
    def __init__(self, node):
        self.node = node

    def get_review_title(self):
        title = self.node.find(xmlExporter.XML_REVIEW_TITLE).text
        return '' if title is None else title

    def get_review_content(self):
        content = self.node.find(xmlExporter.XML_REVIEW_CONTENT).text
        return '' if content is None else content

    def get_review_rating(self):
        return float(self.node.find(xmlExporter.XML_REVIEW_RATING).text)

    def get_review_date(self):
        return parse_date(self.node.find(xmlExporter.XML_REVIEW_DATE).text)

    def get_stayed_date(self):
        return parse_date(self.node.find(xmlExporter.XML_STAYED_DATE).text)

    def get_stayed_type(self):
        return self.node.find(xmlExporter.XML_STAYED_TYPE).text

    def get_sub_ratings(self):
        return json.loads(self.node.find(xmlExporter.XML_SUB_RATINGS).text)

    def get_thanks(self):
        return self.node.find(xmlExporter.XML_REVIEW_THANKS).text


class xmlHotel():
    def __init__(self, fn):
        with open(fn, 'r', encoding='utf-8') as xml_file:
            self.root = ET.parse(xml_file).getroot()

        self.hotel = self.root.find(xmlExporter.XML_HOTEL)
        self.size = int(self.hotel.find(xmlExporter.XML_REVIEW_SIZE).text)
        self.reviews = [_xmlReview(self.root.find(
            xmlExporter.XM_REVIEW_HEAD + str(i+1))) for i in range(self.size)]
        self.addr = self.hotel.find(xmlExporter.XML_HOTEL_ADDR).text

    def get_hotel_name(self):
        return self.hotel.find(xmlExporter.XML_HOTEL_NAME).text

    def get_review_size(self):
        return self.size

    def get_hotel_addr(self):
        return self.addr

    def get_hotel_loc(self):
        geolocator = Nominatim()
        location = geolocator.geocode(self.addr)
        # print(location.address)
        # print(location.raw)
        return None, None if location is None else \
            location.latitude, location.longitude

    def get_hotel_rating(self):
        return float(self.hotel.find(xmlExporter.XML_HOTEL_RATING).text)

    def get_hotel_ranking(self):
        return int(self.hotel.find(xmlExporter.XML_HOTEL_RANKING).text)

    def get_hotel_tags(self):
        return json.loads(
            self.hotel.find(xmlExporter.XML_HOTEL_TAGS).text)

    def get_hotel_highlights(self):
        return json.loads(
            self.hotel.find(xmlExporter.XML_HOTEL_HIGHS).text)

    def get_reviews(self):
        return self.reviews

    def get_review(self, pos):
        return self.reviews[pos] if pos < self.size else None
