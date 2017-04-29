# DISCLAIMER

The source codes in the current repository are provided for general Python programming learning purpose only. Your use of any of these source codes is at your own risk.

# TripAdvisor Crawler

Not only the abundant travel information, but over 500 million valuable traveler reviews make TripAdvisor one of the most prestigious online travel platforms it is today. Over the past two decades, TripAdvisor has proven itself viable by adopting user-generated content that people throughout the world can refer to. Despite the acquisition of such content is demanding, its potential in a variety of advanced tasks rather than mere interaction is worth investigation. In addition to several constraints, current official APIs only allow limited fields and amount of data on a daily basis, and hence collecting large-scale of comprehensive sources in reasonable time seems practically impossible.

This work offers a faster and more flexible two-in-one alternative to the official APIs: the crawler collects online hotel records via multi-threading web analysis, while the extractor parses local results. Given a location, the crawler sends a query to TripAdvisor and indexes the resulting hotels; the crawler then fetches the home page and relevant reviews of each hotel; reviewer profiles are also collected where possible. All crawling results are stored as raw HTML to preserve maximum information, from which the extractor can select different levels of data fields. For example, hotel address and amenities, the room type a review mentions, and the number of cities a reviewer has visited.


## Instructions

1. (Optional) In `common.py` edit accordingly `SLEEP_TIME` seconds to wait between each connection to TripAdvisor; `SNIPPET_THREAD_NUM`, `DETAIL_THREAD_NUM`, `REVIEW_THREAD_NUM`, and `USER_THREAD_NUM` the number of threads in each crawling stage. In practice, a minimum pause of two seconds and at most three threads for each crawler are recommended.

2. Search a location on TripAdvisor and have the returning URL ready. Take Melbourne, it should be: 
> https://www.tripadvisor.com.au/Hotels-g255100-Melbourne_Victoria-Hotels.html

3. Run `crawlSnippets.py` and proceed with the URL; this will index all hotels within the location. 

4. Run `crawlDetails.py` to obtain home pages and review ids of each indexed hotel.

5. Run `crawlReviews.py` and wait until it fetches reviews of every single hotel.

6. Run `crawlUsers.py` for collecting profiles of most reviewers who wrote the reviews.

As a result, step 4 gathers all hotel information, followed by hotel reviews in step 5, and step 6 leads to reviewer profiles. Therefore, depending on the type of data required, one could stop the procedure at any step as long as the preceding steps are completed.


## Features

* Flexible crawling speed control
* Resumable crawling process with data corruption detection
* Easy access to a wide range of data fields (see `demo.py`)


## TODOs

* Database implementation for collected data
* General surveys on collected data
* Incremental reviews update
* Photo crawling support
