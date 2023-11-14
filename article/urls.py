from django.urls import path, include
from . import views

urlpatterns = [
    path("trainai", views.trainingNewsData, name="trainai"),
    path("saveJsons", views.saveJsons, name="saveJsons"),
    path("train", views.train, name="train"),
    path("search", views.search, name="search"),
    path('like/<int:article_id>/', views.like_article, name='like_article'),
    path('dislike/<int:article_id>/', views.dislike_article, name='dislike_article'),
    
]