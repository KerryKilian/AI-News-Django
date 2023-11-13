from django.shortcuts import redirect, render
import requests
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .services import fetchTrainingArticles, getArticlesForUser, fetchWithoutCategories, saveTrainingJsons, search_articles
from .ai import trainAi
import os
from .models import TrainingArticle, UserProfile
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
        # User is logged in, and you can access their ID
        user_id = request.user.id
        try:
            getArticlesForUser(user_id)
        except UserProfile.DoesNotExist as e:
            return HttpResponse(status=404)
    else:
        # User is not logged in
        return HttpResponse(status=401) 


def saveJsons(request):
    success, message = saveTrainingJsons()
    return JsonResponse({'message': str(message)})
                       

def search(request):
    query = request.GET.get('q', '')
    try:
        search_articles(query)
    except Exception as e:
        return HttpResponse(status=500)
    
