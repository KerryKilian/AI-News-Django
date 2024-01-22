from django.http import HttpResponse
from django.shortcuts import render, redirect

from article.models import UserProfile
from article.services import get_articles_for_user
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
        articles = get_articles_for_user(user_profile, country)
    except Exception as e:
        print(str(e))
        return HttpResponse(status=500)
    return render(request, 'core/index.html', {'articles': articles})




