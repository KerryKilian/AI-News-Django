from django.urls import path, include
from . import views

urlpatterns = [
    path("trainai", views.trainingNewsData, name="trainai"),
    path("saveJsons", views.saveJsons, name="saveJsons"),
    path("train", views.train, name="train"),
]