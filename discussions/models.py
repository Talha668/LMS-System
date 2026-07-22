from django.db import models
from django.contrib.auth import get_user_model
from courses.models import Course


User = get_user_model()


class DiscussionThread(models.Model):
    pass


class DiscussionReply(models.Model):
    pass