from django.db import models

from .defaults import DEFAULT_TOPICS
# import CategoryChoices
# from newski.core.models import UserProfile
from .enums import CategoryChoices  # Import the CategoryChoices enumeration
from django.contrib.auth.models import User  # Import the User model from django.contrib.auth




CATEGORY_CHOICES = [
    ('business', 'Business'),
    ('entertainment', 'Entertainment'),
    ('general', 'General'),
    ('health', 'Health'),
    ('science', 'Science'),
    ('sports', 'Sports'),
    ('technology', 'Technology'),
]

CATEGORY_CHOICES = [
    ('us', 'us'),
    ('de', 'de'),
    ('fr', 'fr'),
]

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Country(models.Model):
    name = models.CharField(max_length=2)
    
class Article(models.Model):
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank = True, null = True)
    author = models.CharField(max_length=255, null = True)
    url = models.TextField(blank=True, null=True)
    urlToImage = models.TextField(blank = True, null = True)
    publishedAt = models.DateTimeField(auto_now_add=False, null=True) # manually from news api
    sourceName = models.CharField(max_length=255, null=True)
    content = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    likes = models.IntegerField(default=0, blank=True)
    dislikes = models.IntegerField(default=0, blank=True)
    
    def __str__(self):
        return self.title
    


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    entertainment = models.IntegerField(default=0)
    general = models.IntegerField(default=0)
    business = models.IntegerField(default=0)
    health = models.IntegerField(default=0)
    science = models.IntegerField(default=0)
    sports = models.IntegerField(default=0)
    technology = models.IntegerField(default=0)
    read_articles = models.ManyToManyField(Article, related_name='read_by_users', blank=True, default=[])
    like_articles = models.ManyToManyField(Article, related_name='like_articles', blank=True, default=[])
    dislike_articles = models.ManyToManyField(Article, related_name='dislike_articles', blank=True, default=[])

    def __str__(self):
        return self.user.username if self.user else "UserProfile"

    
class ArticleRating(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]
    rating = models.IntegerField(choices=RATING_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)



class ArticleComment(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s comment on {self.article.title}"


    
class TrainingArticle(models.Model):
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank = True, null = True)
    author = models.CharField(max_length=255, null = True)
    url = models.TextField(blank=True, null=True)
    urlToImage = models.TextField(blank = True, null = True)
    publishedAt = models.DateTimeField(auto_now_add=False, null=True) # manually from news api
    sourceName = models.CharField(max_length=255, null=True)
    content = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    # country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.title
    

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.message}"
    

