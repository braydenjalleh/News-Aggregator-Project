from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

# Create your models here.
class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


class NewsStory(models.Model):
    headline = models.CharField(max_length=64)
    CATEGORY_CHOICES = [
        ('pol', 'Politics'),
        ('art', 'Art'),
        ('tech', 'Technology'),
        ('trivia', 'Trivia'),
    ]
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    REGION_CHOICES = [
        ('uk', 'United Kingdom'),
        ('eu', 'Europe'),
        ('w', 'World'),
    ]
    region = models.CharField(max_length=10, choices=REGION_CHOICES)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    pub_date = models.DateField('Date published')
    details = models.CharField(max_length=128)

    def __str__(self):
        return self.headline
