from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    now don't use
    """

    def __str__(self):
        return self.email
