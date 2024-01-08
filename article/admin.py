from django.contrib import admin
from .models import Article, ChatMessage, Country, UserProfile, TrainingArticle, ArticleRating, ArticleComment, Category

# Register your models here.

admin.site.register(Category)
admin.site.register(UserProfile)
admin.site.register(Article)
admin.site.register(TrainingArticle)
admin.site.register(ArticleRating)
admin.site.register(ArticleComment)
admin.site.register(ChatMessage)
admin.site.register(Country)