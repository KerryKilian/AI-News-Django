from django.shortcuts import get_object_or_404, redirect, render
import requests
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .services import fetchTrainingArticles, getArticlesForUser, fetchWithoutCategories, saveTrainingJsons, search_articles, user_dislikes, user_likes
from .ai import trainAi
import os
from .models import Article, TrainingArticle, UserProfile
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.models import User


@require_http_methods(["GET"])


def trainingNewsData(request):
    '''
    DEPRECATED. DO NOT USE! Requests News Articles for training the ai. Shall be called when server started.
    '''
    return fetchTrainingArticles()


def train(request):
    '''
    shall be called when server started
    '''
    predicted = trainAi()
    return JsonResponse({'predicted': str(predicted)})

def newsData(request):
    '''
    fetches new articles
    '''
    fetchWithoutCategories()

@login_required
def newsForUser(request):
    '''
    fetches specific news for user
    '''
    if request.user.is_authenticated:
        user_id = request.user.id
        try:
            getArticlesForUser(user_id)
        except UserProfile.DoesNotExist as e:
            return HttpResponse(status=404)
    else:
        return HttpResponse(status=401) 


def saveJsons(request):
    success, message = saveTrainingJsons()
    return JsonResponse({'message': str(message)})
                       

def search(request):
    query = request.GET.get('q', '')
    try:
        articles = search_articles(query)
        return render(request, 'core/search.html', {'articles': articles, 'query': query})
    except Exception as e:
        return HttpResponse(status=500)

@login_required
def like_article(request, article_id):
    if request.method == 'POST':
        if request.user.is_authenticated:
            user_profile = UserProfile.objects.get(user=request.user)
            article = get_object_or_404(Article, pk=article_id)
            new_value = user_likes(user_profile, article.id)
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=401) 

    return HttpResponse(status=400) 

@login_required
def dislike_article(request, article_id):
    if request.method == 'POST':
        if request.user.is_authenticated:
            user_profile = UserProfile.objects.get(user=request.user)
            article = get_object_or_404(Article, pk=article_id)
            new_value = user_dislikes(user_profile, article.id)
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=401) 

    return HttpResponse(status=400) 