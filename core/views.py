from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from article.models import ArticleComment, ArticleRating, ChatMessage, UserProfile
from article.services import getArticlesForUser, user_read_article
from .forms import ChatForm, SignupForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from article.models import Article
from django.db.models import Avg

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
    ratings = ArticleRating.objects.filter(article=article)
    comments = ArticleComment.objects.filter(article=article)
    messages = ChatMessage.objects.filter(article=article).order_by('-timestamp')[:50]

    if ratings is not None and len(ratings) > 0:
        average_rating = int(ratings.aggregate(Avg('rating'))['rating__avg'])
        average_rating = round(average_rating)
        stars_list = list(range(average_rating))# [0,1,2]
        stars_until_5_list = list(range(5 - average_rating)) # [3,4]
    else: 
        average_rating = 0
        stars_list = [0]
        stars_until_5_list = list(range(4))

    # Calculate the user's rating for this article
    try:
        user_rating = ArticleRating.objects.get(user=user_profile, article=article).rating
        user_rating = round(user_rating)
        user_stars_list = list(range(user_rating)) # [0,1,2]
        user_stars_until_5_list = list(range(5 - user_rating)) # [3,4]
    except ArticleRating.DoesNotExist:
        user_rating = 0
        user_stars_list = [0]
        user_stars_until_5_list = list(range(4))
    return render(request, 'core/article_detail.html', 
                  {'article': article, 
                   'ratings': ratings, 
                   'comments': comments, 
                   'average_rating': average_rating, 
                   "stars_list": stars_list, 
                   "stars_until_5_list": stars_until_5_list,
                   "stars_5_list": [0,1,2,3,4],
                   "user_stars_list": user_stars_list,
                   "user_stars_until_5_list": user_stars_until_5_list,
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