import json
from logging import getLogger
from logging.handlers import BufferingHandler

import requests
import tweepy
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import BaseCommand
from django.db import transaction
import environ
from oauthlib.oauth1.rfc5849.endpoints import access_token

from oshiken_django import settings
from tweet.models import TwitterUser, Tweet, Picture

logger = getLogger(__name__)
buffer_handler = BufferingHandler(capacity=1000000)
logger.addHandler(buffer_handler)


class Command(BaseCommand):

    help = 'Crate a superuser, and allow password to be provided'

    @transaction.atomic
    def handle(self, *args, **options):
        api = _get_api()
        for user in TwitterUser.objects.filter(
                is_target_user=True):
            try:
                _get_tweets(user, api)
            except Exception as e:
                logger.error(f'{user.id}-Error:{e.args}')


def _get_api():
    # get from environment id
    ct = settings.CONSUMER_TOKEN
    cs = settings.CONSUMER_SECRET
    at = settings.ACCESS_TOKEN
    acs = settings.ACCESS_SECRET
    auth = tweepy.OAuthHandler(ct, cs)
    auth.set_access_token(at, acs)
    return tweepy.API(auth)


def _get_tweets(tweet_user, api):

    param = {'id': tweet_user.twitter_user_id, 'tweet_mode': 'extended', }
    if tweet_user.max_id:
        param['max_id'] = tweet_user.max_id

    res = api.user_timeline(**param)

    for status in res:
        _set_status(tweet_user, status)


def _set_status(tweet_user, status):

    try:
        _create_status(tweet_user, status)

    except Exception as e:
        logger.error(f'user:{tweet_user.twitter_user_id}, '
                     f'status:{status["id"]}')


def _create_status(tweet_user, status):
    defaults = {'created_at': status.created_at,
                'text': status.full_text,
                }
    tweet, _ = Tweet.objects.update_or_create(
        user=tweet_user,
        tweet_id=status.id,
        defaults=defaults)

    for media in status.entities.get('media', []):
        # downloadしてupload
        Picture.create_image_from_url(media['media_url'])



