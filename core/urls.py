from django.urls import include, path 
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.views.i18n import set_language

from . import views
from .forms import LoginForm


app_name = "core"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("login/", auth_views.LoginView.as_view(template_name="core/login.html", authentication_form=LoginForm), name="login"),
    path("", views.index, name="index"),
    path('article/', include('article.urls', namespace='article'), name="article"),
    path('i18n/', set_language, name='set_language'),
]