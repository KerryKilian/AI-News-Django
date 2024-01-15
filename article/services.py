from collections import Counter
from datetime import datetime, timedelta, timezone
from queue import PriorityQueue
import random
from django.db import IntegrityError
from django.http import JsonResponse
import requests

from .models import Article, Category, Country, TrainingArticle, UserProfile
from decouple import config
from .utils import readFile, createUrl, saveFile, text_from_article
from .ai import create_bag_of_words, get_sorted_categories, predictCategory, compute_similarity
import pickle
from sklearn.metrics.pairwise import cosine_similarity

from django.core.cache import cache
from django.contrib.auth.models import User
from django.db.models import Q



tfidf_vectorizer = None
classifier = None
# USE_MOCKED_DATA = config('USE_MOCKED_DATA', default=False, cast=bool)
USE_MOCKED_DATA = False
API_KEY = config('API_KEY')
USE_CACHE = True

# def fetchTrainingArticles():
#     '''
#     DEPRECATED, DO NOT USE! fetches data for each category and saves it into the database
#     '''
#     try:
#         categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
        
#         for category in categories:
#             category_object = Category.objects.get_or_create(name=category)
#             # either mocked data or real data
#             if USE_MOCKED_DATA:
#                 print("Using mocked data")
#                 success, articles_data = readFile(category)
#                 if not success:
#                     print(f"Failed to read mocked data for category: {category}")
#                     continue
#             else:
#                 response = requests.get(createUrl(category))
#                 if response.status_code == 200:
#                     articles_data = response.json().get('articles', [])
#                 else:
#                     print(f"Failed to fetch data for category: {category}")
#                     continue

#             for article_data in articles_data:
#                 # Create a new Article object and save it to the database
#                 TrainingArticle.objects.create(
#                     title=article_data.get('title'),
#                     description=article_data.get('description'),
#                     author=article_data.get('author'),
#                     url=article_data.get('url'),
#                     urlToImage=article_data.get('urlToImage'),
#                     publishedAt=datetime.strptime(article_data.get('published_at'), "%Y-%m-%dT%H:%M:%SZ") if article_data.get('published_at') else None,
#                     content=article_data.get('content'),
#                     category=category_object
#                 )

#             # Save the fetched data or mocked data, if successful
#             if USE_MOCKED_DATA:
#                 saveFile(category, articles_data)

#         return JsonResponse({'message': 'Articles saved to the database'}, safe=False)
#     except Exception as e:
#         return JsonResponse({'message': 'Failed to fetch articles from the API. ' + str(e)}, status=500, safe=False)



def saveTrainingJsons():
    '''
    reads all json files which contain training data for the AI and saves it as trainings articles into database
    '''

    # Define the category names
    category_names = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

    for category_name in category_names:
        try:
            # Retrieve the Category object or create it if it doesn't exist
            category, created = Category.objects.get_or_create(name=category_name)

            # Iterate through possible file name variations
            for filename in [category_name, f"{category_name}-chatgpt"]:
                success, articles_data = readFile(filename)
                if success:
                    for article_data in articles_data:
                        existing_article = TrainingArticle.objects.filter(title=article_data.get('title')).first()
                        if existing_article is None:
                            # Create a new TrainingArticle object and save it to the database
                            TrainingArticle.objects.create(
                                title=article_data.get('title'),
                                description=article_data.get('description'),
                                category=category  # Assign the Category object
                            )
                            # print("New Article added: " + article_data.get("title"))
        except Exception as e:
            # Handle exceptions, such as if a category doesn't exist
            return False, e

    return True, "success"





def fetchWithoutCategories(country = "us"):
    '''
    takes articles from database and trains the ki with categories
    '''
    
    response = requests.get(createUrl("", country))
    if response.status_code == 200:
        articles_data = response.json().get('articles', [])
        for article_data in articles_data:
            print(article_data)
            if article_data.get("title") != "[Removed]":
            

                existing_article = Article.objects.filter(title=article_data.get('title')).first()
                if existing_article:
                    # If the article with the same title exists, you can skip it
                    continue
                category = predictCategory(article_data, country)
                # Create a new Article object and save it to the database
                Article.objects.create(
                    title=article_data.get('title'),
                    description=article_data.get('description'),
                    author=article_data.get('author'),
                    url=article_data.get('url'),
                    urlToImage=article_data.get('urlToImage'),
                    publishedAt=datetime.strptime(article_data.get('published_at'), "%Y-%m-%dT%H:%M:%SZ") if article_data.get('published_at') else None,
                    sourceName=article_data.get("source").get("source"),
                    content=article_data.get('content'),
                    category=Category.objects.get(name=category),
                    country=Country.objects.get(name=country)
                )


def bag_of_words(user_profile, articles):
    # sort Articles for user depending of bag of words
    if user_profile.read_articles.exists():
        # extract text from the last three articles
        read_articles = user_profile.read_articles.all().order_by('-id')[:3]
        read_articles_text = ""
        for article in read_articles:
            text = text_from_article(article)
            read_articles_text += text + "; "

        sorted_articles = sorted(
            articles,
            key=lambda article: compute_similarity(text_from_article(article), read_articles_text),
            reverse=True,
        )

        return sorted_articles
    else:
        return articles


def categoriesAlgorithm(user_profile, country = "us"):
    print("categoriesAlgorithm")
    # sorted_categories = get_sorted_categories(user_profile=user_profile)

    print("Checking if I shall request new data")
    # request Articles
    today = datetime.now().date()
    cache_key = f'last_fetch_date_{country}'
    if USE_CACHE == True:
        print("using cache")
        last_fetch_date = cache.get(cache_key)
    else:
        print("not using cache")
        last_fetch_date = None

    # If last fetch date is not set or it's not today, fetch the data
    if not last_fetch_date or last_fetch_date.date() != today:
        print("fetching new data")
        # Update the last fetch date in the cache
        cache.set(cache_key, datetime.now(), timeout=timedelta(days=1).seconds)
        fetch_needed = True

        # fetch mock data
        if USE_MOCKED_DATA == True:
            success, data = readFile("top-headlines")
            
            for article_data in data:
                # Create a new Article object and save it to the database
                if article_data.get("title") != "[Removed]":

                    existing_article = Article.objects.filter(title=article_data.get('title')).first()
                    if existing_article:
                        continue
                    category = predictCategory(article_data)
                    Article.objects.create(
                        title=article_data.get('title'),
                        description=article_data.get('description'),
                        author=article_data.get('author'),
                        url=article_data.get('url'),
                        urlToImage=article_data.get('urlToImage'),
                        publishedAt=datetime.strptime(article_data.get('published_at'), "%Y-%m-%dT%H:%M:%SZ") if article_data.get('published_at') else None,
                        sourceName=article_data.get("source").get("source"),
                        content=article_data.get('content'),
                        category=Category.objects.get(name=category)
                    )
                
        else: # fetch real data
            print("fetchWithoutCategories")
            fetchWithoutCategories(country)
    else:
        fetch_needed = False
        print("not fetching new data")
    
    

    # get as many articles from database as specified in category_number
    # for category_name, category_number in sorted_categories.items():
    #     category = Category.objects.get(name=category_name)
    #     articles = Article.objects.filter(category=category, country=country_db)

    #     if len(articles) != 0:  # if there are articles in this category in the headlines
    #         if category_number > 0:
    #             for _ in range(category_number * 3): # as many articles as points in userprofile
    #                 # get articles which are not yet in positive and not read by user yet
    #                 available_articles = [
    #                     article for article in articles if article not in result and article not in user_profile.read_articles.all()
    #                 ]
    #                 if available_articles:
    #                     selected_article = available_articles[0]  # Select the first available article
    #                     result.append(selected_article)
    #         elif category_number == 0:
    #             for _ in range(2): 
    #                 # get articles which are not yet in zero and not read by user yet
    #                 available_articles = [
    #                     article for article in articles if article not in result and article not in user_profile.read_articles.all()
    #                 ]
    #                 if available_articles:
    #                     selected_article = available_articles[0]  # Select the first available article
    #                     result.append(selected_article)
    #         elif category_number < 0:
    #             # get articles which are not yet in negative and not read by user yet
    #             available_articles = [
    #                 article for article in articles if article not in result and article not in user_profile.read_articles.all()
    #             ]
    #             if available_articles:
    #                 selected_article = available_articles[0]  # Select the first available article
    #                 result.append(selected_article)

    result = []
    first_results = []
    end_results = []
    country_db = Country.objects.get(name=country)

    first_categories_to_fetch = []
    end_categories_to_fetch = []
    categories = ["entertainment", "general", "business", "health", "science", "sports", "technology"]

    # STEP 1: display at least one article from each category at the end
    for category in categories:
        category_db = Category.objects.get(name=category)
        end_categories_to_fetch.append(category_db)

    last_articles = user_profile.read_articles.all().order_by("-id")[:10]
    like_articles = user_profile.like_articles.all().order_by("-id")[:10]
    dislike_articles = user_profile.dislike_articles.all().order_by("-id")[:10]

    # STEP 2: Append every category from the last 10 read articles
    for article in last_articles:
        first_categories_to_fetch.append(article.category)

    # STEP 3: Append every category where user liked the article
    for article in like_articles:
        first_categories_to_fetch.append(article.category)

    print("STEP 4")
    # STEP 4: Remove one category for disliked article (only if there are are least 2 categories in the list)
    category_counts = Counter(first_categories_to_fetch)
    for article in dislike_articles:
        category = article.category
        if category in category_counts and category_counts[category] >= 1:
            first_categories_to_fetch.remove(category)
            category_counts[category] -= 1

    # STEP 5: Append all categories to result list at first place
    for category in first_categories_to_fetch:
        articles_by_category = Article.objects.filter(category=category, country=country_db)
        available_articles = [
            article for article in articles_by_category if article not in first_results and article not in user_profile.read_articles.all()
        ]
        if available_articles:
            first_results.append(available_articles[0])
            if len(available_articles) > 1:
                first_results.append(available_articles[1])

    # STEP 6: Append all categories to result list at the end (so that at least two articles from each category in list)
    for category in end_categories_to_fetch:
        articles_by_category = Article.objects.filter(category=category, country=country_db)
        available_articles = [
            article for article in articles_by_category if article not in first_results and article not in end_results and article not in user_profile.read_articles.all()
        ]
        if available_articles:
            end_results.append(available_articles[0])
            if len(available_articles) > 1:
                end_results.append(available_articles[1])
    
    # STEP 7: create bag of words and sort list by that
    first_results_sorted = bag_of_words(user_profile, first_results)
    end_results_sorted = bag_of_words(user_profile, end_results)

    result = first_results_sorted + end_results_sorted
    return result, fetch_needed




def getArticlesForUser(user_profile, country = "us"):
    print("getArticlesForUser")
    # get Articles for user depending on categories with trained AI
    articles, fetch_needed = categoriesAlgorithm(user_profile, country)
    return articles
    

    

# def user_read_article(user_profile, article_id):
#     '''
#         adds an article to the user's "read_article" field
#     '''
#     article = Article.objects.get(id=article_id)
#     user_profile.read_articles.add(article)

def user_likes_article(user_profile, article_id):
    '''
        adds an article to the user's "like_article" field
    '''
    article = Article.objects.get(id=article_id)
    print("Artikel soll geliked werden")
    if article not in user_profile.like_articles.all():
        print("Artikel noch nicht geliked")
        user_profile.like_articles.add(article)
        print("User Profile Like wurde hinzugefügt")
        article.likes = article.likes + 1
        print("Artikel Like wurde hinzugefügt")
        if article in user_profile.dislike_articles.all():
            print("Artikel wurde vorher gedisliked")
            user_profile.dislike_articles.remove(article)
            article.dislikes -= 1

    user_profile.save()
    article.save()

def user_dislikes_article(user_profile, article_id):
    '''
        adds an article to the user's "dislike_article" field
    '''
    article = Article.objects.get(id=article_id)
    
    if article not in user_profile.dislike_articles.all():
        user_profile.dislike_articles.add(article)
        article.dislikes += 1
        if article in user_profile.like_articles.all():
            user_profile.like_articles.remove(article)
            article.likes -= 1

    user_profile.save()
    article.save()

def search_articles(search_term):
    articles = Article.objects.filter(
        Q(title__icontains=search_term) | Q(description__icontains=search_term)
    )
    return articles

# def user_changes_rating(user_profile, article, points):
#     """
#     DEPRECATED user can rate an article
#     """
#     # change in userprofile
#     field_name = article.category.name
#     field_value = getattr(user_profile, field_name)
    
#     # change in article
#     like_articles = user_profile.like_articles.all()
#     dislike_articles = user_profile.dislike_articles.all()
#     if int(points) > 0 and article not in like_articles:
#         article.likes += 1
#         user_profile.like_articles.add(article)
#         field_value += int(points)
#         if article in dislike_articles:
#             user_profile.dislike_articles.remove(article)
#             article.dislikes -= 1
#             field_value += int(points)
#         setattr(user_profile, field_name, field_value)
#     elif int(points) < 0 and article not in dislike_articles:
#         article.dislikes += 1
#         user_profile.dislike_articles.add(article)
#         field_value += int(points) - 1

#         # if it is the first rating
#         if article not in like_articles:
#             field_value -= 3

#         # if article already rated
#         if article in like_articles:
#             user_profile.like_articles.remove(article)
#             article.likes -= 1
#             field_value += int(points) - 1
#         setattr(user_profile, field_name, field_value)
            

#     user_profile.save()
#     article.save()
#     return field_value



def user_read_article(user_profile, article):
    """
    method for registring the article into the read_articles field
    """
    user_profile.read_articles.add(article)
    # field_value = getattr(user_profile, article.category.name)
    # field_value += 1
    # setattr(user_profile, article.category.name, field_value)
    # user_profile.save()
    return user_profile


# def user_rates_article(user_profile, article, rating_value):
#     """
#     DEPRECATED user can rate an article which is affecting the users interests profile
#     """
#     print("User rates this article with " + str(rating_value))
#     try:
#         # Try to get an existing rating
#         article_rating = ArticleRating.objects.get(user=user_profile, article=article)
#         # If it exists, update the rating
#         article_rating.rating = rating_value
        
#         article_rating.save()
#     except ArticleRating.DoesNotExist:
#         # If it doesn't exist, create a new rating
#         article_rating = ArticleRating.objects.create(
#             user=user_profile,
#             article=article,
#             rating=rating_value,
#         )
#         article_rating.save()
#     except IntegrityError as e:
#         # Handle any integrity errors, such as unique constraint violations
#         print(f"IntegrityError: {str(e)}")
#         raise e
    
#     # rate category for user
#     # if rating_value == 1:
#     #     user_changes_rating(user_profile, article, -2)
#     # elif rating_value == 2:
#     #     user_changes_rating(user_profile, article, -1)
#     # elif rating_value == 3:
#     #     pass
#     # elif rating_value == 4:
#     #     user_changes_rating(user_profile, article, 1)
#     # elif rating_value == 5:
#     #     user_changes_rating(user_profile, article, 2)
#     user_changes_rating(user_profile, article, rating_value)
