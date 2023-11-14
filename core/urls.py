from django.urls import path 
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView

from . import views
from .forms import LoginForm


app_name = "core"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("login/", auth_views.LoginView.as_view(template_name="core/login.html", authentication_form=LoginForm), name="login"),
    path("", views.index, name="index"),
    path('article/<int:pk>/', views.article_detail, name='article_detail'),
]