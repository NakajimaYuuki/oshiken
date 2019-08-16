import os
from urllib.request import urlopen

from django.contrib.auth.models import AbstractUser
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db import models
from django.db.models import Max, Min


class TwitterUser(models.Model):
    twitter_user_id = models.BigIntegerField(unique=True, db_index=True)
    screen_name = models.CharField(max_length=255, unique=False)
    is_target_user = models.BooleanField(default=False)

    def __str__(self):
        return self.screen_name

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

    @staticmethod
    def create_user(user_info):
        defaults = {'screen_name': user_info['screen_name']}
        mention_user, _ = TwitterUser.objects.get_or_create(
            twitter_user_id=user_info['id'],
            defaults=defaults)
        return mention_user


class Tweet(models.Model):
    user = models.ForeignKey('TwitterUser', null=True,
                             related_name='tweets', on_delete=models.SET_NULL,)
    tweet_id = models.BigIntegerField(unique=True)
    created_at = models.DateTimeField()
    text = models.TextField(null=True)
    retweet_id = models.BigIntegerField(null=True)

    images = models.ManyToManyField('Picture', related_name='tweets')
    videos = models.ManyToManyField('Video', related_name='tweets')
    mention = models.ForeignKey('Mention', related_name='tweets', on_delete=models.SET_NULL)
    hash_tags = models.ManyToManyField('Hashtag', related_name='tweets')

    def __str__(self):
        return f'{self.user}-{self.text[:20]}'

    @staticmethod
    def create_tweet(tweet_user, status_id,  created_at, full_text, mention=None):
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
    mention_users = models.ManyToManyField('TwitterUser',
                                           related_name='mention_tweets')
    in_reply_to_status_id = models.BigIntegerField(null=True)

    @staticmethod
    def creat_mention(status):

        mention_users = []
        for user_mention in status.entities.get('user_mentions', []):
            mention_user = TwitterUser.create_user(user_mention)
            mention_users.append(mention_user)

        if not mention_users:
            return None
        mention, _ = Mention.objects.get_or_create(
            in_reply_to_status_id=status.in_reply_to_status_id)

        mention.mention_users.set(**mention_users)
        return mention


class Picture(models.Model):
    media_id = models.BigIntegerField()
    image = models.ImageField(upload_to='images')  # upload to S3
    image_original_url = models.URLField(null=True)  # set twitter url

    @staticmethod
    def create_image_from_url(media_id, image_url):
        root, ext = os.path.splitext(image_url)
        file_name = root.split('/')[-1]

        picture = Picture(media_id=media_id, image_original_url=image_url)
        img_temp = NamedTemporaryFile(delete=True)
        img_temp.write(urlopen(image_url).read())
        img_temp.flush()
        picture.image.save(file_name, File(img_temp))
        return None


class Video(models.Model):
    video_url = models.FileField(upload_to='files')
    video_original_url = models.URLField(null=True)


class Hashtag(models.Model):
    hash_tag = models.CharField(max_length=140)
