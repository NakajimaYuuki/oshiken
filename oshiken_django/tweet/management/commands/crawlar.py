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
from tweet.models import TwitterUser, Tweet, Picture, Mention

logger = getLogger(__name__)
buffer_handler = BufferingHandler(capacity=1000000)
logger.addHandler(buffer_handler)


class Command(BaseCommand):

    help = 'Crate a superuser, and allow password to be provided'

    @transaction.atomic
    def handle(self, *args, **options):
        get_tweet = GetTweet()
        for user in TwitterUser.objects.filter(
                is_target_user=True):
            try:
                get_tweet.get_tweets(user)
            except Exception as e:
                logger.error(f'{user.id}-Error:{e.args}')


class GetTweet():

    def __init__(self):
        # get from environment id
        ct = settings.CONSUMER_TOKEN
        cs = settings.CONSUMER_SECRET
        at = settings.ACCESS_TOKEN
        acs = settings.ACCESS_SECRET
        auth = tweepy.OAuthHandler(ct, cs)
        auth.set_access_token(at, acs)
        self.api = tweepy.API(auth)

    def get_tweets(self, tweet_user):

        param = {'id': tweet_user.twitter_user_id, 'tweet_mode': 'extended', }
        if tweet_user.max_id:
            param['max_id'] = tweet_user.max_id

        res = self.api.user_timeline(**param)

        for status in res:
            self.set_status(tweet_user, status)

    def set_status(self, tweet_user, status):

        try:
            # 先にメンションを作る
            mention = Mention.creat_mention(status)
            tweet = Tweet.create_tweet(tweet_user, status.id,
                                       status.created_at, status.full_text,
                                       mention
                                       )
            # create pictures
            for media in status.entities.get('media', []):
                # video or picture?
                try:
                    pic = Picture.objects.get(
                        image_original_url=media['media_url'])
                except Picture.DoesNotExist:
                    pic = Picture.create_image_from_url(
                        media['media_id'],
                        media['media_url'])
                tweet.images.add(pic)
            # create hash tag

        except Exception as e:
            logger.error(f'user:{tweet_user.twitter_user_id}, '
                         f'status:{status["id"]}')
