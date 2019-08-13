from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Max


class User(AbstractUser):
    """
    now don't use
    """

    def __str__(self):
        return self.email


class TwitterUser(models.Model):
    twitter_user_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=255, unique=False)  # set screen name
    is_target_user = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    @property
    def since_id(self):
        return self.tweets.aggregate(max_id=Max('tweet_id'))


class Tweet(models.Model):
    user = models.ForeignKey('TwitterUser', null=True,
                             related_name='tweets', on_delete=models.SET_NULL,)
    tweet_id = models.BigIntegerField(unique=True)
    created_at = models.DateTimeField()
    text = models.TextField(null=True)

    images = models.ManyToManyField('Picture', related_name='tweets')
    videos = models.ManyToManyField('Video', related_name='tweets')
    mentions = models.ManyToManyField('Mention', related_name='tweets')

    def __str__(self):
        return f'{self.user}-{self.text[:20]}'


class Mention(models.Model):
    mention_users = models.ManyToManyField('TwitterUser', related_name='mention_tweets')
    origin_tweet_id = models.CharField(max_length=255, null=True)


class Picture(models.Model):
    picture = models.ImageField()  # upload to S3
    picture_original_url = models.URLField(null=True)  # set twitter url


class Video(models.Model):
    video_url = models.URLField()
    video_original_url = models.URLField(null=True)
