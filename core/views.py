from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from article.models import ArticleComment, ArticleRating, ChatMessage, UserProfile
from article.services import getArticlesForUser, user_changes_rating, user_read_article
from .forms import ChatForm, SignupForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from article.models import Article
from django.db.models import Avg
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




def article_detail(request, pk):
    user_profile = UserProfile.objects.get(user=request.user)
    article = get_object_or_404(Article, pk=pk)
    user_read_article(user_profile, article)
    ratings = ArticleRating.objects.filter(article=article)
    comments = ArticleComment.objects.filter(article=article)
    messages = ChatMessage.objects.filter(article=article).order_by('-timestamp')[:50]

    return render(request, 'core/article_detail.html', 
                  {'article': article, 
                   'ratings': ratings, 
                   'comments': comments,
                   "messages": messages
                   })

@login_required
def article_chat(request, article_id):
    article = Article.objects.get(pk=article_id)
    messages = ChatMessage.objects.filter(article=article).order_by('-timestamp')[:50]
    return render(request, 'core/article_chat.html', {'article': article, 'messages': messages})

@login_required
def post_article_message(request, article_id):
    if request.method == 'POST':
        user = request.user
        article = Article.objects.get(pk=article_id)
        message = request.POST.get('message')

        if message:
            chat_message = ChatMessage.objects.create(user=user, article=article, message=message)
            data = {
                'username': chat_message.user.username,
                'message': chat_message.message,
                'timestamp': chat_message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            }
            return JsonResponse(data)

    return JsonResponse({'error': 'Invalid request'})


@login_required
def read_articles(request):
    user_profile = UserProfile.objects.get(user=request.user)
    articles = user_profile.read_articles.all()
    return render(request, 'core/read_articles.html', 
              {'articles': articles })    

@login_required
def rating(request, article_id):
    if request.method == 'POST':
        user_profile = UserProfile.objects.get(user=request.user)
        article = Article.objects.get(pk=article_id)
        rating = request.POST.get("rating")

        user_changes_rating(user_profile, article, rating)
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=405)
