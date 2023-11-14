from django.http import HttpResponse
from django.shortcuts import render, redirect

from article.models import UserProfile
from article.services import getArticlesForUser, user_read_article
from .forms import SignupForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from article.models import Article
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
    try:
        user = User.objects.get(id=request.user.id)
        user_profile = UserProfile.objects.get(user=user)
    except:
        return redirect("/login/")
    try:
        articles = getArticlesForUser(user_profile)
    except:
        return HttpResponse(status=500)
    return render(request, 'core/index.html', {'articles': articles})




def article_detail(request, pk):
    user_profile = UserProfile.objects.get(user=request.user)
    article = get_object_or_404(Article, pk=pk)
    new_value = user_read_article(user_profile, article.id)
    
    return render(request, 'core/article_detail.html', {'article': article})