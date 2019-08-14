import json

import requests
from django.contrib.auth.models import AbstractUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.db.models import Max, Min


class TwitterUser(models.Model):
    twitter_user_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=255, unique=False)  # set screen name
    is_target_user = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    @property
    def since_id(self):
        since_id = self.tweets.aggregate(since_id=Min('tweet_id'))['since_id']
        if since_id:
            return since_id
        return 1

    @property
    def max_id(self):
        max_id = self.tweets.aggregate(max_id=Max('tweet_id'))['max_id']
        if max_id:
            return max_id
        return


class Tweet(models.Model):
    user = models.ForeignKey('TwitterUser', null=True,
                             related_name='tweets', on_delete=models.SET_NULL,)
    tweet_id = models.BigIntegerField(unique=True)
    created_at = models.DateTimeField()
    text = models.TextField(null=True)
    retweet = models.ForeignKey('self',
                                related_name='retweets',
                                null=True, blank=True,
                                on_delete=models.CASCADE)

    images = models.ManyToManyField('Picture', related_name='tweets')
    videos = models.ManyToManyField('Video', related_name='tweets')
    mentions = models.ManyToManyField('Mention', related_name='tweets')
    hash_tags = models.ManyToManyField('Hashtag', related_name='tweets')

    def __str__(self):
        return f'{self.user}-{self.text[:20]}'


class Mention(models.Model):
    mention_users = models.ManyToManyField('TwitterUser', related_name='mention_tweets')
    origin_tweet_id = models.CharField(max_length=255, null=True)


class Picture(models.Model):
    media_id = models.BigIntegerField()
    picture = models.ImageField()  # upload to S3
    picture_original_url = models.URLField(null=True)  # set twitter url

    @staticmethod
    def create_image_from_url(image_path):
        content, content_type = Picture.download_image(image_path)
        name = image_path.split("/")[-1]
        name = name.replace(".PNG", '.png')

        uploaded_file = SimpleUploadedFile(name, content, content_type=content_type)

        pay_load = {
            'json-serialized-data': json.dumps({}),
            'file': uploaded_file,
        }

        return

    @staticmethod
    def download_image(image_path, timeout=10):
        response = requests.get(image_path, timeout=timeout)

        if response.status_code != 200:
            e = Exception("HTTP status: " + response.status_code)
            raise e
        if response.headers['content-type'] == 'text/html':
            raise ValueError(f"{image_path} is not image!")
        return response.content, response.headers['content-type']


class Video(models.Model):
    video_url = models.URLField()
    video_original_url = models.URLField(null=True)


class Hashtag(models.Model):
    hash_tag = models.CharField(max_length=140)

