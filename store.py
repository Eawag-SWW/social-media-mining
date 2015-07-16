from datetime import datetime, timedelta
import logging
import os
import pickle
from os.path import join

import pandas as pd

from apis import twitter_api
from apis.twitter_api import Tweet, TwitterSearchQuery


STORE_DIR = 'store'
logger = logging.getLogger('main')


class StoreType(object):
    def __init__(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.directory = directory


STREAMING_TWEETS = StoreType(join(STORE_DIR, 'tweets', 'stream'))
SEARCH_TWEETS = StoreType(join(STORE_DIR, 'tweets', 'search'))
FLICKR_PLOT = StoreType(join(STORE_DIR, 'flickr', 'plot'))

# POINTS = 2



def read(query, store_type):
    logger.info('Reading store for %s ...', query)
    path = _get_storage_path(query, store_type)

    if store_type == FLICKR_PLOT:
        answer = pd.Series.from_csv(path)
    else:
        f = open(path, 'rb')
        answer = pickle.load(f)
        logger.debug('... finished. %n items read.', len(answer))
    return answer


def save(query, store_type):
    if store_type == STREAMING_TWEETS:
        listener = twitter_api.StoringListener(status_handler=_save_streaming_tweet)
        twitter_api.start_streaming(listener, query.bounding_box)

    if store_type == SEARCH_TWEETS:
        tweets = twitter_api.download_search_tweets(query)
        path = _get_storage_path(query, store_type)
        with open(path, 'wb') as f:
            pickle.dump(tweets, f)

    else:
        raise RuntimeError('Store for %s not yet implemented.', store_type)

        # path = _get_path(query, type)
        #
        # if type == StoreType.FLICKR_PLOT:
        # data = dict()
        #     for year in range(START_YEAR, END_YEAR):
        #         n_photos = flickr_api.count_photos(query, year)
        #         data[year] = n_photos
        #     series = pd.Series(data)
        #     series.to_csv(path)
        #
        # elif type == StoreType.POINTS:
        #     points = flickr_api.get_points(query)
        #     f = open(path, 'wb')
        #     pickle.dump(points, f)
        #
        # elif type == StoreType.TWEETS:
        #     tweets = twitter_api.download_tweets(query)
        #     f = open(path, 'wb')
        #     pickle.dump(tweets, f)
        #
        #


def get_search_tweets(place_id, begin_date, end_date, use_cache=False):
    n_days = int((end_date - begin_date).days)
    tweets = []

    for d in [begin_date + timedelta(days=i) for i in range(n_days)]:
        query = TwitterSearchQuery(place_id=place_id, date=d)

        if not use_cache:
            save(query, store_type=SEARCH_TWEETS)

        statuses = read(query, store_type=SEARCH_TWEETS)
        for status in statuses:
            tweets.append(Tweet(status))

    return tweets



# def get_tweets(store_type):
#     tweets = []
#     dirname = store_type.directory
#
#     for filename in os.listdir(dirname):
#         path = os.path.join(dirname, filename)
#         with open(path, 'r') as f:
#             data = pickle.load(f)
#             if store_type == SEARCH_TWEETS:
#                 for status in data:
#                     tweets.append(Tweet(status))
#             elif store_type == STREAMING_TWEETS:
#                 tweets.append(Tweet(data))
#
#     return tweets


# def get_tweets_dataframe(store_type, begin=None, end=None):
#     tweets = get_tweets(store_type)
#     tweet_dicts = [vars(tweet) for tweet in tweets]
#     dataframe = pd.DataFrame(tweet_dicts)
#     dataframe.index = dataframe.created_at
#     dataframe.sort(inplace=True)
#     dataframe = dataframe[begin:end]
#     return dataframe


def _get_storage_path(query, store_type):
    if store_type == FLICKR_PLOT:
        extension = 'csv'
    else:
        extension = 'p'

    dirname = store_type.directory
    filename = '%s.%s' % (repr(query), extension)
    return os.path.join(dirname, filename)


def _save_streaming_tweet(status):
    now = datetime.now()
    timestamp = (now - datetime(1970, 1, 1)).total_seconds()
    filename = '%s.p' % timestamp
    path = os.path.join(STREAMING_TWEETS.directory, filename)

    with open(path, mode='w') as f:
        pickle.dump(status, f)

