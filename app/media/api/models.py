from __future__ import unicode_literals

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.contrib.auth.models import AbstractUser
from django_countries.fields import CountryField
from guardian.mixins import GuardianUserMixin

import api.managers

# Create your models here.


class Account(AbstractUser, GuardianUserMixin):
    country = CountryField()
    email = models.EmailField()
    # Persist a hash of the user's UI display settings
    # Default settings are assigned on account creation
    # profile = JSONField or hyperlinked profile
    account_settings = JSONField(null=True)
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email', 'password']
    accounts = api.managers.AccountManager

    class Meta:
        verbose_name = 'account'
        verbose_name_plural = 'accounts'
        abstract = False

    def change_profile_details(self, details):
        '''Changes user account profile settings with provided details.'''
        if details and self.has_perm('change_account'):
            # self.profile.modify(details)
            pass

    def change_account_settings(self, settings):
        self.account_settings = settings


class Log(models.Model):
    """
    Every log has a representation as a resource.
    A media log will be pulled from an activity log and the UI will infer how to display the log by information passed into the log through its association with the media.
    """
    message = models.CharField(max_length=255)


class ActivityLog(models.Model):
    title = models.CharField(max_length=100)
    authors = models.ManyToManyField(settings.AUTH_USER_MODEL)
    logs = models.ManyToManyField(Log)


class BlogPost(models.Model):
    log = models.ForeignKey(Log)
    slug = models.SlugField()
    title = models.CharField(max_length=100)
    authors = models.ManyToManyField(Account)
    body = models.TextField()
    objects = api.managers.BlogPostManager()

    def has_change_permission(self, user):
        if user.id in self.authors:
            return True
        else:
            return False