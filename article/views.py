from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
import requests
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from article.utils import readFile
from .services import getArticlesForUser, search_articles, user_dislikes_article, user_likes_article, user_read_article, user_changes_rating
from .ai import train_ai_with_training_articles
import os
from .models import Article, ArticleComment, ArticleRating, Category, ChatMessage, Country, TrainingArticle, UserProfile
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test

@require_http_methods(["GET"])

@user_passes_test(lambda u: u.username == 'admin')
def train_ai(request):
    '''
    http endpoint for training the model based on the articles in data folder. Only accessible by admin user
    '''
    # Step 1 : Add Articles to TrainingArticles Database
    category_names = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
    countries = ["us", "fr", "de"]

    # create 3 countries
    for country in countries:
        Country.objects.get_or_create(name=country)

    # read articles and save to db
    for country in countries:
        print(country)
        for category_name in category_names:
            print(category_name)
            category, created = Category.objects.get_or_create(name=category_name)
            for filename in [category_name, f"{category_name}-chatgpt"]:
                success, articles_data = readFile(filename, country)
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
        
    
    # Step 2 : Train AI with TrainingArticles
    for country in countries:
        train_ai_with_training_articles(country)

    return HttpResponse(status=200)


@login_required
def newsForUser(request):
    '''
    fetches specific news for user
    DEPRECATED!!!!
    '''
    if request.user.is_authenticated:
        user_id = request.user.id
        try:
            getArticlesForUser(user_id)
        except UserProfile.DoesNotExist as e:
            return HttpResponse(status=404)
    else:
        return HttpResponse(status=401) 
                       

def search(request):
    query = request.GET.get('q', '')
    try:
        articles = search_articles(query)
        return render(request, 'article/search.html', {'articles': articles, 'query': query})
    except Exception as e:
        return HttpResponse(status=500)



def article_detail(request, pk):
    user_profile = UserProfile.objects.get(user=request.user)
    article = get_object_or_404(Article, pk=pk)
    user_read_article(user_profile, article)
    ratings = ArticleRating.objects.filter(article=article)
    comments = ArticleComment.objects.filter(article=article)
    messages = ChatMessage.objects.filter(article=article).order_by('-timestamp')[:50]

    return render(request, 'article/article_detail.html', 
                  {'article': article, 
                   'ratings': ratings, 
                   'comments': comments,
                   "messages": messages
                   })

@login_required
def article_chat(request, article_id):
    article = Article.objects.get(pk=article_id)
    messages = ChatMessage.objects.filter(article=article).order_by('-timestamp')[:50]
    return render(request, 'article/article_chat.html', {'article': article, 'messages': messages})

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
    return render(request, 'article/read_articles.html', 
              {'articles': articles })    

# @login_required
# def rating(request, article_id):
#     if request.method == 'POST':
#         user_profile = UserProfile.objects.get(user=request.user)
#         article = Article.objects.get(pk=article_id)
#         rating = request.POST.get("rating")

#         user_changes_rating(user_profile, article, rating)
#         return HttpResponse(status=200)
#     else:
#         return HttpResponse(status=405)

@login_required
def rating(request, article_id):
    print("Now in rating")
    if request.method == 'POST':
        user_profile = UserProfile.objects.get(user=request.user)
        rating = request.POST.get("rating")

        if int(rating) > 0:
            print("rating positive")
            user_likes_article(user_profile, article_id)
        elif int(rating) < 0:
            print("rating negative")
            user_dislikes_article(user_profile, article_id)
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=405)

