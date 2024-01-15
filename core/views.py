from django.http import HttpResponse
from django.shortcuts import render, redirect

from article.models import UserProfile
from article.services import getArticlesForUser
from .forms import SignupForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render
from django.utils.translation import get_language

# Create your views here.

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)

        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)

            return redirect('/login/')
    else:
        form = SignupForm()

    return render(request, 'core/signup.html', {
        'form': form
    })

@login_required
def index(request):
    '''
    homepage which displays articles depending on user
    '''
    country = get_language()
    print(str(country))
    if country == "en":
        country = "us"
    try:
        user = User.objects.get(id=request.user.id)
        user_profile = UserProfile.objects.get(user=user)
    except:
        return redirect("/login/")
    try:
        articles = getArticlesForUser(user_profile, country)
    except:
        return HttpResponse(status=500)
    return render(request, 'core/index.html', {'articles': articles})




