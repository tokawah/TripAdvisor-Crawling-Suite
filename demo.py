from hotelExtractor import Hotel


def fprint(t, k, v):
    print('{}{}: {}'.format('\t'*(t-1), k, v))

# initialize a hotel
hotel_id = input('hotel id: ')
hotel_id = '299549'
hotel = Hotel(hotel_id)
fprint(1, 'HOTEL', '=' * 50)
fprint(1, 'name', hotel.get_name())
fprint(1, 'trace', hotel.get_trace())
fprint(1, 'address', hotel.get_address())
fprint(1, 'overall rating', hotel.get_rating())
fprint(1, 'ranking', hotel.get_ranking())
fprint(1, 'tags', hotel.get_hotel_tags())
fprint(1, 'most mentioned', hotel.get_review_highlights())
# fprint(1, 'traveller photos', hotel.get_traveller_photos())
# fprint(1, 'management photos', hotel.get_management_photos())
# fprint(1, 'amenity tags', hotel.get_amenity_tags())
# fprint(1, 'amenity categories', hotel.get_amenity_categories())
# fprint(1, 'amenity description', hotel.get_description())
# fprint(1, 'additional amenity information', hotel.get_additional_info())

# initialize related reviews
for review in hotel.get_reviews():
    fprint(2, 'REVIEW', '=' * 50)
    fprint(2, 'title', review.get_title())
    fprint(2, 'overall rating', review.get_overall_rating())
    fprint(2, 'review date', review.get_date())
    fprint(2, 'content', review.get_content())
    # fprint(2, 'room tip', review.get_tips())
    fprint(2, 'stayed date', review.get_stayed_date())
    fprint(2, 'stayed type', review.get_stayed_type())
    fprint(2, 'sub-ratings', review.get_sub_ratings())
    fprint(2, 'thanks received', review.get_thanks())
    # fprint(2, 'response', review.get_response())

    # initialize the corresponding reviewer
    # user = review.get_user()
    # if user is not None:
    #     fprint(3, 'USER', '=' * 50)
    #     fprint(3, 'name', user.get_user_name())
    #     fprint(3, 'description', user.get_user_descriptions())
    #     fprint(3, 'basic statistics', user.get_basic_stats())
    #     fprint(3, 'review distribution', user.get_review_distribution())
    #     fprint(3, 'registered', user.get_age_since())
    #     fprint(3, 'hometown', user.get_hometown())
    #     fprint(3, 'statistics', user.get_stats())
    #     fprint(3, 'user tags', user.get_tags())
    #     # fprint(3, 'total point', user.get_total_point())
    #     # fprint(3, 'level', user.get_level())
    #     # fprint(3, 'badges', user.get_badges())
