from django.contrib import admin
from .models import Article, UserProfile, TrainingArticle, ArticleRating, ArticleComment, Category

# Register your models here.

admin.site.register(Category)
admin.site.register(UserProfile)
admin.site.register(Article)
admin.site.register(TrainingArticle)
admin.site.register(ArticleRating)
admin.site.register(ArticleComment)