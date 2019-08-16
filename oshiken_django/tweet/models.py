import datetime
import os
from urllib.request import urlopen

from django.contrib.auth.models import AbstractUser
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db import models
from django.db.models import Max, Min


class TwitterUser(models.Model):
    user_id = models.BigIntegerField(unique=True, db_index=True)
    screen_name = models.CharField(max_length=255, unique=False)
    is_target = models.BooleanField(default=False)

    def __str__(self):
        return self.screen_name

    @property
    def max_id(self):
        min_id = self.tweets.aggregate(min_id=Min('tweet_id'))['min_id']
        if min_id:
            return min_id
        return None

    @staticmethod
    def create_user(user_info):
        defaults = {'screen_name': user_info['screen_name']}
        mention_user, _ = TwitterUser.objects.get_or_create(
            user_id=user_info['id'],
            defaults=defaults)
        return mention_user


class Tweet(models.Model):
    user = models.ForeignKey('TwitterUser', null=True,
                             related_name='tweets', on_delete=models.SET_NULL,)
    tweet_id = models.BigIntegerField(unique=True)
    created_at = models.DateTimeField()
    text = models.TextField(null=True)
    retweet_id = models.BigIntegerField(null=True)

    mention = models.ForeignKey('Mention', related_name='tweets',
                                null=True, on_delete=models.SET_NULL)

    images = models.ManyToManyField('Picture', related_name='tweets')
    videos = models.ManyToManyField('Video', related_name='tweets')
    hashtags = models.ManyToManyField('Hashtag', related_name='tweets')

    def __str__(self):
        return f'{self.user}-{self.text[:20]}'

    @staticmethod
    def create_tweet(tweet_user, status_id,  created_at, full_text, mention=None):
        created_at = created_at.astimezone(datetime.timezone.utc)
        defaults = {'created_at': created_at,
                    'text': full_text,
                    'mention': mention
                    }
        tweet, _ = Tweet.objects.update_or_create(
            user=tweet_user,
            tweet_id=status_id,
            defaults=defaults)
        return tweet


class Mention(models.Model):
    twitter_users = models.ManyToManyField('TwitterUser',
                                           related_name='mention_tweets')
    in_reply_to_status_id = models.BigIntegerField(null=True)

    @staticmethod
    def creat_mention(status):

        twitter_users = []
        for user_mention in status.entities.get('user_mentions', []):
            twitter_user = TwitterUser.create_user(user_mention)
            twitter_users.append(twitter_user)

        if not twitter_users:
            return None
        mention, _ = Mention.objects.get_or_create(
            in_reply_to_status_id=status.in_reply_to_status_id)

        mention.twitter_users.set(twitter_users)
        return mention


class Picture(models.Model):
    media_id = models.BigIntegerField()
    image = models.ImageField(upload_to='images')  # upload to S3
    image_original_url = models.URLField(null=True)  # set twitter url

    @staticmethod
    def create_image_from_url(media_id, image_url):
        root, ext = os.path.splitext(image_url)
        file_name = root.split('/')[-1]

        defaults = {'image_original_url': image_url}
        picture, _ = Picture.objects.get_or_create(
            media_id=media_id,
            defaults=defaults)
        if not picture.image:
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(image_url).read())
            img_temp.flush()
            picture.image.save(file_name+ext, File(img_temp))
            picture.save()
        return picture


class Video(models.Model):
    video = models.FileField(upload_to='videos')
    video_original_url = models.URLField(null=True)

    @staticmethod
    def create_video_from_url(file_url):
        root, ext = os.path.splitext(file_url)
        file_name = root.split('/')[-1]

        video, _ = Video.objects.get_or_create(video_original_url=file_url)
        if not video.video:
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(file_url).read())
            img_temp.flush()
            video.video.save(file_name+ext, File(img_temp))
            video.save()
        return video


class Hashtag(models.Model):
    name = models.CharField(max_length=140, unique=True)

    def __str__(self):
        return self.name
