from django.urls import path, include
from . import views

urlpatterns = [
    path("trainai", views.trainingNewsData, name="trainai"),
    path("saveJsons", views.saveJsons, name="saveJsons"),
    path("train", views.train, name="train"),
    path("search", views.search, name="search"),
    path('<int:article_id>/like', views.like_article, name='like_article'),
    path('<int:article_id>/dislike', views.dislike_article, name='dislike_article'),
    path('rating/<int:article_id>', views.save_rating, name='rating'),
    # TODO: TODO TODO TODO TODO article_id/like, article_id/dislike, article_id/rating
]