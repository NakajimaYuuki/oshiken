from logging import getLogger
from logging.handlers import BufferingHandler

import tweepy
from django.core.management import BaseCommand
from django.db import transaction
import environ

from tweet.models import TwitterUser, Tweet

logger = getLogger(__name__)
buffer_handler = BufferingHandler(capacity=1000000)
logger.addHandler(buffer_handler)


class Command(BaseCommand):

    help = 'Crate a superuser, and allow password to be provided'

    @transaction.atomic
    def handle(self, *args, **options):
        api = _get_api()
        for user in TwitterUser.objects.filter(is_target=True):
            try:
                _get_tweets(user, api)
            except Exception as e:
                logger.error(f'{user.id}-Error:{e.args}')


def _get_api():
    env = environ.Env()
    env.read_env('.env')

    consumer_token = env('CONSUMER_TOKEN')
    consumer_secret = env('CONSUMER_SECRET')
    access_token = env('ACCESS_TOKEN')
    access_secret = env('ACCESS_SECRET')

    # get from environment id
    auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
    auth.set_access_token(access_token, access_secret)
    return tweepy.API(auth)


def _get_tweets(user, api):

    for status in tweepy.Cursor(
            api.user_timeline(id=user.twitter_user_id,
                              tweet_mode='extended',
                              since_id=user.since_id)).items():
        _set_status(user, status)


def _set_status(tweet_user, status):
    tweet_id = status['id']

    try:
        defaults = {'created_at': status['created_at'],
                    'text': status['text'],
                    }
        tweet = Tweet.objects.update_or_create(
            user=tweet_user,
            tweet_id=tweet_id,
            defaults=defaults)

    except Exception as e:
        logger.error(f'user:{tweet_user.twitter_user_id}, '
                     f'status:{status["id"]}')
