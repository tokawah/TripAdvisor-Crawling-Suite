import ast
import sqlite3
import common

from extractors.hotelExtractor import rawHotel
from extractors.reviewExtractor import rawReview
from extractors.userExtractor import rawUser


class taDB():
    def __init__(self, db_name):
        self.db_name = db_name
        self._conn = sqlite3.connect(db_name)
        self._c = self._conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._c.close()
        self._conn.close()

    def insert_a_location(self, record):
        self._c.execute('''
            INSERT OR REPLACE INTO locations (gid, hid_str)
            VALUES (?, ?);''', record)
        self._conn.commit()

    def read_a_location(self, gid):
        return self._c.execute('''
              SELECT hid_str FROM locations 
              WHERE gid = ?;''', (gid,)).fetchone()

    def get_hotel_url_pairs(self, gid):
        db_hid_str = self.read_a_location(gid)
        if db_hid_str is not None:
            return ast.literal_eval(db_hid_str[0])
        return {}

    def insert_a_hotel(self, record):
        self._c.execute('''
            INSERT OR REPLACE INTO hotels (
            hid, html, gid, rno, rid_str)
            VALUES (?, ?, ?, ?, ?);''', record)
        self._conn.commit()

    def read_a_hotel(self, hid):
        return self._c.execute('''
            SELECT hid, html, gid, rno, rid_str FROM hotels 
            WHERE hid = ?;''', (hid,)).fetchone()

    def insert_many_reviews(self, record):
        self._c.executemany('''
            INSERT OR REPLACE INTO reviews (rid, html, uid)
            VALUES (?, ?, ?);''', record)
        self._conn.commit()

    def read_a_review(self, rid):
        return self._c.execute('''
            SELECT uid, html FROM reviews
            WHERE rid = ?;''', (rid,)).fetchone()

    def update_review_list_in_hotel(self, hid, rno, rid_str):
        self._c.execute('''UPDATE hotels
                SET rno = ?, rid_str = ?
                WHERE hid = ?;''', (rno, rid_str, hid))
        self._conn.commit()

    def insert_a_user(self, record):
        self._c.execute('''
            INSERT OR REPLACE INTO users (uid, html)
            VALUES (?, ?);''', record)
        self._conn.commit()

    def read_a_user(self, uid):
        return self._c.execute(
            '''SELECT html FROM users 
            WHERE uid = ?;''', (uid,)).fetchone()

    def read_all_user_ids(self):
        return [x[0] for x in self._c.execute(
            '''SELECT uid FROM users;''').fetchall()]

    def remove_user_id_in_review(self, uid):
        self._c.execute('''UPDATE reviews
                SET uid = ?
                WHERE uid = ?;''', (None, uid))
        self._c.execute(
            '''DELETE FROM users 
                WHERE uid = ?;''', (uid,))
        self._conn.commit()

    def generate_unique_users(self):
        records = self._c.execute(
            '''SELECT DISTINCT uid FROM reviews 
            WHERE uid IS NOT NULL;''').fetchall()
        self._c.executemany('''
                    INSERT OR IGNORE INTO users (uid)
                    VALUES (?);''', records)
        self._conn.commit()

    def extract_hotel_info(self):
        def batch_insert():
            self._c.executemany(
                '''UPDATE hotels
                  SET htrace = ?, 
                  hname = ?, addr = ?, 
                  coords = ?, hstar = ?, 
                  htype = ?, hstyle = ?,
                  rating = ?, ranking = ?, 
                  highlights = ?
                  WHERE hid = ?;''', records)
            self._conn.commit()
            # print('\tinserted.')

        records = []
        for result in self._c.execute('''
              SELECT hid FROM hotels;''').fetchall():
            hid = result[0]
            print('extracting hotel {}...'.format(hid))
            _result = self._c.execute('''
            SELECT html FROM hotels 
            WHERE hid = ?;''', (hid,)).fetchone()
            html = _result[0]
            _ = rawHotel(html)
            record = (str(_.get_trace()),
                      _.get_name(),
                      _.get_address(),
                      str(_.get_coords()),
                      int(_.get_star()),
                      str(_.get_type()),
                      str(_.get_style()),
                      float(_.get_rating()),
                      int(_.get_ranking()),
                      str(_.get_highlights()),
                      hid)
            records.append(record)
            if len(records) >= common.EXTRACT_CHUNK_SIZE:
                batch_insert()
                records = []
        # finalizing
        batch_insert()
        print('hotel extraction done.')

    def extract_review_info(self):
        def batch_insert():
            self._c.executemany(
                '''UPDATE reviews
                  SET title = ?, content = ?, 
                  rdate = ?, sdate = ?, 
                  stype = ?, rating = ?, 
                  subratings = ?, thanks = ?
                  WHERE rid = ?;''', records)
            self._conn.commit()
            # print('\tinserted.')

        cnt = 0
        records = []
        for result in self._c.execute('''
              SELECT rid FROM reviews;''').fetchall():
            rid = result[0]
            # print('extracting review {}...'.format(rid))
            _result = self._c.execute('''
            SELECT html FROM reviews 
            WHERE rid = ?;''', (rid,)).fetchone()
            html = _result[0]
            if html is None:
                continue

            cnt += 1
            _ = rawReview(html)
            record = (_.get_title(),
                      _.get_content(),
                      str(_.get_date()),
                      str(_.get_stayed_date()),
                      str(_.get_stayed_type()),
                      float(_.get_rating()),
                      str(_.get_sub_ratings()),
                      int(_.get_thanks()), rid)
            records.append(record)
            if len(records) >= common.EXTRACT_CHUNK_SIZE:
                batch_insert()
                records = []
                print(cnt, 'reviews extracted.')
        # finalizing
        batch_insert()
        print('review extraction done.')

    def extract_user_info(self):
        def batch_insert():
            self._c.executemany(
                '''UPDATE users
                SET uname = ?, udesc = ?, 
                bstat = ?, astat = ?, 
                rdist = ?, hometown = ?, 
                regyear = ?, utags = ?, 
                upoint = ?, ulevel = ?
                WHERE uid = ?;''', records)
            self._conn.commit()
            # print('\tinserted.')

        cnt = 0
        records = []
        for result in self._c.execute('''
              SELECT uid FROM users;''').fetchall():
            uid = result[0]
            # print('[user {}]'.format(uid))
            _result = self._c.execute('''
            SELECT html FROM users 
            WHERE uid = ?;''', (uid,)).fetchone()
            html = _result[0]
            if html is None:
                continue

            cnt += 1
            _ = rawUser(html)
            record = (_.get_name(),
                      str(_.get_descriptions()),
                      str(_.get_basic_stats()),
                      str(_.get_stats()),
                      str(_.get_review_distribution()),
                      _.get_hometown(),
                      str(_.get_registration_year()),
                      str(_.get_tags()),
                      float(_.get_total_point()),
                      float(_.get_level()), uid)
            records.append(record)
            if len(records) >= common.EXTRACT_CHUNK_SIZE:
                batch_insert()
                records = []
                print(cnt, 'users extracted.')
        # finalizing
        batch_insert()
        print('user extraction done.')

    def compress(self):
        print('compressing hotel records...')
        h_records = [
            (None, hid[0]) for hid in self._c.execute(
                '''SELECT hid FROM hotels;''').fetchall()]
        self._c.executemany(
            '''UPDATE hotels SET html = ? 
              WHERE hid = ?;''', h_records)

        print('compressing review records...')
        r_records = [
            (None, rid[0]) for rid in self._c.execute(
                '''SELECT rid FROM reviews;''').fetchall()]
        self._c.executemany(
            '''UPDATE reviews SET html = ? 
              WHERE rid = ?;''', r_records)

        print('compressing user records...')
        u_records = [
            (None, uid[0]) for uid in self._c.execute(
                '''SELECT uid FROM users;''').fetchall()]
        self._c.executemany(
            '''UPDATE users SET html = ?
              WHERE uid = ?;''', u_records)

        print('finalizing...')
        self._conn.commit()
        self._conn.execute('''VACUUM''')
        print('cleansing done.')

    def create_tables(self):
        # create crawl table
        self._c.execute('''DROP TABLE IF EXISTS locations;''')
        self._c.execute('''CREATE TABLE locations (
                            gid TEXT, hid_str TEXT,
                            UNIQUE(gid));''')
        # Create hotel table
        self._c.execute('''DROP TABLE IF EXISTS hotels;''')
        self._c.execute('''CREATE TABLE hotels (
                    gid TEXT, hid TEXT, html TEXT,
                    rno INTEGER, rid_str TEXT,
                    htrace TEXT, hname TEXT, addr TEXT,
                    coords TEXT, hstar REAL,
                    htype TEXT, hstyle TEXT, rating REAL,
                    ranking REAL, highlights TEXT,
                    hdesc TEXT, amenities TEXT,
                    nearby TEXT, similar TEXT,
                    is_complete INTEGER DEFAULT 0,
                    UNIQUE(hid));''')
        # create review table
        self._c.execute('''DROP TABLE IF EXISTS reviews;''')
        self._c.execute('''CREATE TABLE reviews (
                    rid TEXT, uid TEXT, html TEXT,
                    title TEXT, content TEXT, rdate TEXT,
                    sdate TEXT, stype TEXT, rating REAL,
                    subratings TEXT, thanks INTEGER,
                    is_complete INTEGER DEFAULT 0,
                    UNIQUE(rid));''')
        # create user table
        self._c.execute('''DROP TABLE IF EXISTS users;''')
        self._c.execute('''CREATE TABLE users (
                    uid TEXT, html TEXT,
                    uname TEXT, udesc TEXT, bstat TEXT, astat TEXT,
                    rdist TEXT, hometown TEXT, regyear TEXT,
                    utags TEXT, upoint REAL, ulevel REAL,
                    is_complete INTEGER DEFAULT 0,
                    UNIQUE(uid));''')
        self._conn.commit()
