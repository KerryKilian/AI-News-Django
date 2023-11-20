from django.urls import path, include
from . import views

urlpatterns = [
    path("trainai", views.trainingNewsData, name="trainai"),
    path("saveJsons", views.saveJsons, name="saveJsons"),
    path("train", views.train, name="train"),
    path("search", views.search, name="search"),
    path('rating/<int:article_id>', views.save_rating, name='rating'),
]