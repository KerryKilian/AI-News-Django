from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

from article.utils import read_file
from .services import get_articles_for_user, search_articles, user_dislikes_article, user_likes_article, user_read_article
from .ai import train_ai_with_training_articles
from .models import Article, ArticleComment, Category, ChatMessage, Country, TrainingArticle, UserProfile
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from .defaults import categories, countries

@require_http_methods(["GET"])

@user_passes_test(lambda u: u.username == 'admin')
def train_ai(request):
    '''
    http endpoint for training the model based on the articles in data folder. Only accessible by admin user
    '''
    try:
        # Step 1 : Add Articles to TrainingArticles Database
        for country in countries:
            Country.objects.get_or_create(name=country)

        # read articles and save to db
        for country in countries:
            print(country)
            for category_name in categories:
                print(category_name)
                category, created = Category.objects.get_or_create(name=category_name)
                for filename in [category_name, f"{category_name}-chatgpt"]:
                    success, articles_data = read_file(filename, country)
                    for article in articles_data:
                        existing_article = TrainingArticle.objects.filter(title=article.get('title')).first()
                        if existing_article is None:
                            # Create a new TrainingArticle object and save it to the database
                            TrainingArticle.objects.create(
                                title=article.get('title'),
                                description=article.get('description'),
                                category=category,
                                country=Country.objects.get(name=country)
                            )
    except Exception as e:
        print(str(e))
        return HttpResponse(status=500)
        
    
    # Step 2 : Train AI with TrainingArticles
    for country in countries:
        train_ai_with_training_articles(country)

    return HttpResponse(status=200)

                       

def search(request):
    '''
    view for search function
    '''
    query = request.GET.get('q', '')
    try:
        articles = search_articles(query)
        return render(request, 'article/search.html', {'articles': articles, 'query': query})
    except Exception as e:
        print(str(e))
        return HttpResponse(status=500)



def article_detail(request, pk):
    '''
    view for details of an article
    '''
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        article = get_object_or_404(Article, pk=pk)
        user_read_article(user_profile, article)
        comments = ArticleComment.objects.filter(article=article)
        messages = ChatMessage.objects.filter(article=article).order_by('-timestamp')[:50]

        return render(request, 'article/article_detail.html', 
                      {'article': article, 
                       'comments': comments,
                       "messages": messages
                       })
    except Exception as e:
        print(str(e))
        return HttpResponse(status=500)

@login_required
def article_chat(request, article_id):
    '''
    get all chat messages for an article
    '''
    try:
        article = Article.objects.get(pk=article_id)
        messages = ChatMessage.objects.filter(article=article).order_by('-timestamp')[:50]
    except Exception as e:
        print(str(e))
        return HttpResponse(status=500)
    return render(request, 'article/article_chat.html', {'article': article, 'messages': messages})

@login_required
def post_article_message(request, article_id):
    '''
    possibility for users to write commments below articles
    '''
    if request.method == 'POST':
        try:
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
        except Exception as e:
            print(str(e))
            return HttpResponse(status=500)
    return HttpResponse(status=405)


@login_required
def read_articles(request):
    '''
    view for all articles that the user has read
    '''
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        articles = user_profile.read_articles.all()
        return render(request, 'article/read_articles.html', 
              {'articles': articles })  
    except Exception as e:
        print(str(e))
        return HttpResponse(status=500)
    
      


@login_required
def rating(request, article_id):
    '''
    possibility for users to rate an article with thumbs up or down
    '''
    if request.method == 'POST':
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            rating = request.POST.get("rating")

            if int(rating) > 0:
                user_likes_article(user_profile, article_id)
            elif int(rating) < 0:
                user_dislikes_article(user_profile, article_id)
            return HttpResponse(status=200)
        except Exception as e:
            print(str(e))
            return HttpResponse(status=500)
    else:
        return HttpResponse(status=405)

