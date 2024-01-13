from django.urls import path, include
from . import views

app_name = 'article'

urlpatterns = [
    path("train_ai", views.train_ai, name="train_ai"),
    path("search", views.search, name="search"),
    path('<int:pk>/', views.article_detail, name='article_detail'),
    path('<int:article_id>/chat/', views.article_chat, name='article_chat'),
    path('<int:article_id>/post_message/', views.post_article_message, name='post_article_message'),
    path('<int:article_id>/rating/', views.rating, name='rating'),
    path('read_articles', views.read_articles, name='read_articles'),
]