import common
from hotelExtractor import rawHotel
import ast
from os.path import join, isfile, isdir
import os
import xml.etree.cElementTree as ET

XML_ROOT = 'root'
XML_HOTEL = 'hotel'
XM_REVIEW_HEAD = 'review'

XML_REVIEW_SIZE = 'reviews'
XML_HOTEL_NAME = 'name'
XML_HOTEL_ADDR = 'address'
XML_HOTEL_RATING = 'rating'
XML_HOTEL_RANKING = 'ranking'
XML_HOTEL_TAGS = 'tags'
XML_HOTEL_HIGHS = 'highlights'

XML_REVIEW_TITLE = 'title'
XML_REVIEW_CONTENT = 'content'
XML_REVIEW_RATING = 'rating'
XML_REVIEW_DATE = 'review_date'
XML_STAYED_DATE = 'stayed_date'
XML_STAYED_TYPE = 'stayed_type'
XML_SUB_RATINGS = 'sub_ratings'
XML_REVIEW_THANKS = 'thanks'


# lid = '255100'
def gen_xml_files(lid):
    hids = [x for x in ast.literal_eval(
        common.read_file(join(lid, 'hids.txt')))]
    print('{} hotels found'.format(len(hids)))
    for hid in hids:
        hotel_file = join(join(
            join(lid, common.REVIEW_FOLDER), hid), 'result.txt')
        print(hotel_file)
        if not isfile(hotel_file):
            continue

        hotel = rawHotel(lid, hid)
        reviews = hotel.get_reviews()

        root_tag = ET.Element(XML_ROOT)
        hotel_tag = ET.SubElement(root_tag, XML_HOTEL)

        ET.SubElement(hotel_tag, XML_REVIEW_SIZE)\
            .text = str(reviews.get_size())
        ET.SubElement(hotel_tag, XML_HOTEL_NAME)\
            .text = hotel.get_name()
        ET.SubElement(hotel_tag, XML_HOTEL_ADDR)\
            .text = hotel.get_address()
        ET.SubElement(hotel_tag, XML_HOTEL_RATING)\
            .text = hotel.get_rating()
        ET.SubElement(hotel_tag, XML_HOTEL_RANKING)\
            .text = hotel.get_ranking()
        ET.SubElement(hotel_tag, XML_HOTEL_TAGS)\
            .text = str(hotel.get_hotel_tags())
        ET.SubElement(hotel_tag, XML_HOTEL_HIGHS)\
            .text = str(hotel.get_review_highlights())

        cnt = 0
        for review in reviews:
            cnt += 1
            review_tag = ET.SubElement(root_tag, XM_REVIEW_HEAD + str(cnt))

            ET.SubElement(review_tag, XML_REVIEW_TITLE)\
                .text = review.get_title()
            ET.SubElement(review_tag, XML_REVIEW_CONTENT)\
                .text = review.get_content()
            ET.SubElement(review_tag, XML_REVIEW_RATING)\
                .text = review.get_overall_rating()
            ET.SubElement(review_tag, XML_REVIEW_DATE)\
                .text = review.get_date()
            ET.SubElement(review_tag, XML_STAYED_DATE)\
                .text = review.get_stayed_date()
            ET.SubElement(review_tag, XML_STAYED_TYPE)\
                .text = review.get_stayed_type()
            ET.SubElement(review_tag, XML_SUB_RATINGS)\
                .text = str(review.get_sub_ratings())
            ET.SubElement(review_tag, XML_REVIEW_THANKS)\
                .text = review.get_thanks()

        tree = ET.ElementTree(root_tag)

        xml_folder = join(lid, 'xmls')
        if not isdir(xml_folder):
            os.makedirs(xml_folder)
        tree.write(join(xml_folder, hid+'.xml'))
