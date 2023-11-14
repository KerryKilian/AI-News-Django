from datetime import datetime, timedelta
from queue import PriorityQueue
import random
from django.http import JsonResponse
import requests

from .models import Article, Category, TrainingArticle, UserProfile
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
USE_MOCKED_DATA = config('USE_MOCKED_DATA', default=False, cast=bool)
API_KEY = config('API_KEY')

def fetchTrainingArticles():
    '''
    DEPRECATED, DO NOT USE! fetches data for each category and saves it into the database
    '''
    try:
        categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

        for category in categories:
            # either mocked data or real data
            if USE_MOCKED_DATA:
                print("Using mocked data")
                success, articles_data = readFile(category)
                if not success:
                    print(f"Failed to read mocked data for category: {category}")
                    continue
            else:
                response = requests.get(createUrl(category))
                if response.status_code == 200:
                    articles_data = response.json().get('articles', [])
                else:
                    print(f"Failed to fetch data for category: {category}")
                    continue

            for article_data in articles_data:
                # Create a new Article object and save it to the database
                TrainingArticle.objects.create(
                    title=article_data.get('title'),
                    description=article_data.get('description'),
                    author=article_data.get('author'),
                    url=article_data.get('url'),
                    urlToImage=article_data.get('urlToImage'),
                    publishedAt=datetime.strptime(article_data.get('published_at'), "%Y-%m-%dT%H:%M:%SZ") if article_data.get('published_at') else None,
                    content=article_data.get('content'),
                    category=category
                )

            # Save the fetched data or mocked data, if successful
            if USE_MOCKED_DATA:
                saveFile(category, articles_data)

        return JsonResponse({'message': 'Articles saved to the database'}, safe=False)
    except Exception as e:
        return JsonResponse({'message': 'Failed to fetch articles from the API. ' + str(e)}, status=500, safe=False)



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
                        # Create a new TrainingArticle object and save it to the database
                        TrainingArticle.objects.create(
                            title=article_data.get('title'),
                            description=article_data.get('description'),
                            category=category  # Assign the Category object
                        )
        except Exception as e:
            # Handle exceptions, such as if a category doesn't exist
            return False, e

    return True, "success"





def fetchWithoutCategories():
    '''
    takes articles from database and trains the ki with categories
    '''
    response = requests.get(createUrl(""))
    if response.status_code == 200:
        articles_data = response.json().get('articles', [])
        for article_data in articles_data:

            existing_article = Article.objects.filter(title=article_data.get('title')).first()
            if existing_article:
                # If the article with the same title exists, you can skip it or update it
                # Skip it:
                continue
            category = predictCategory(article_data)
            feature_names, bag_of_words_matrix = create_bag_of_words(article_data)
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
                feature_names=feature_names,
                bag_of_words_matrix=bag_of_words_matrix,
            )





def categoriesAlgorithm(user_profile):
    
    sorted_categories = get_sorted_categories(user_profile=user_profile)

    # request Articles
    cache_key = f'last_fetch_date'
    last_fetch_date = cache.get(cache_key)
    today = datetime.now().date()

    # If last fetch date is not set or it's not today, fetch the data
    if not last_fetch_date or last_fetch_date.date() != today:
        # Update the last fetch date in the cache
        cache.set(cache_key, datetime.now(), timeout=timedelta(days=1).seconds)
        fetch_needed = True

        # fetch mock data
        if USE_MOCKED_DATA == True:
            success, data = readFile("top-headlines")
            
            for article_data in data:
                # Create a new Article object and save it to the database
                existing_article = Article.objects.filter(title=article_data.get('title')).first()
                if existing_article:
                    continue
                category = predictCategory(article_data)
                feature_names, bag_of_words_matrix = create_bag_of_words(article_data)
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
                    feature_names=feature_names,
                    bag_of_words_matrix=bag_of_words_matrix,
                )
                
        else: # fetch real data
            fetchWithoutCategories()
    else:
        fetch_needed = False
    
    # sort the categories by positive, zero or negative in the according list
    positive = []
    zero = []
    negative = []
    result = []


    # get as many articles from database as specified in category_number
    for category_name, category_number in sorted_categories.items():
        category = Category.objects.get(name=category_name)
        articles = Article.objects.filter(category=category)

        if len(articles) != 0:  # if there are articles in this category in the headlines
            if category_number > 0:
                for _ in range(category_number): # as many articles as points in userprofile
                    # get articles which are not yet in positive and not read by user yet
                    available_articles = [
                        article for article in articles if article not in result and article not in user_profile.read_articles.all()
                    ]
                    if available_articles:
                        selected_article = available_articles[0]  # Select the first available article
                        result.append(selected_article)
            elif category_number == 0:
                # get articles which are not yet in zero and not read by user yet
                available_articles = [
                    article for article in articles if article not in result and article not in user_profile.read_articles.all()
                ]
                if available_articles:
                    selected_article = available_articles[0]  # Select the first available article
                    result.append(selected_article)
            elif category_number < 0:
                # get articles which are not yet in negative and not read by user yet
                available_articles = [
                    article for article in articles if article not in result and article not in user_profile.read_articles.all()
                ]
                if available_articles:
                    selected_article = available_articles[0]  # Select the first available article
                    result.append(selected_article)



    # shuffle articles
    # random.shuffle(positive)
    # random.shuffle(zero)
    # random.shuffle(negative)

    # # append everything to the result list
    # result.extend(positive)
    # result.extend(zero)
    # result.extend(negative)
    return result, fetch_needed


# def getArticlesForUser(user_id):
#     user_profile = UserProfile.objects.get(id=user_id)
#     # get Articles for the user depending on categories with trained AI
#     articles, fetch_needed = categoriesAlgorithm(user_profile)

#     if user_profile.read_articles:
#         # sort Articles for the user depending on the bag of words
#         priority_queue = PriorityQueue()

#         # Extract text from the last three articles
#         read_articles = user_profile.read_articles.all().order_by('-id')[:3]
#         read_articles_text = ""
#         for article in read_articles:
#             text = text_from_article(article)
#             read_articles_text += text + "; "

#         print(read_articles_text)

#         for article in articles:
#             print(text_from_article(article))
#             print(read_articles_text)
#             similarity = compute_similarity(text_from_article(article), read_articles_text)

#             # Add the (similarity, article_id) pair to the priority queue
#             priority_queue.put((-similarity, article.id))
#             print("similarity: " + str(similarity))

#         # Retrieve the sorted article IDs from the priority queue
#         sorted_article_ids = []

#         while not priority_queue.empty():
#             _, article_id = priority_queue.get()
#             sorted_article_ids.append(article_id)

#         # Get the corresponding articles based on their IDs
#         sorted_articles = Article.objects.filter(id__in=sorted_article_ids)

#         return sorted_articles
#     else:
#         return articles
def getArticlesForUser(user_profile):
    # get Articles for user depending on categories with trained AI
    articles, fetch_needed = categoriesAlgorithm(user_profile)

    


    if user_profile.read_articles.exists():
        # sort Articles for user depending of bag of words

        # user_article_text = text_from_article(user_profile.last_article)
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

def user_read_article(user_profile, article_id):
    '''
        adds an article to the user's "read_article" field
    '''
    article = Article.objects.get(id=article_id)

    user_profile.read_articles.add(article)

def search_articles(search_term):
    articles = Article.objects.filter(
        Q(title__icontains=search_term) | Q(description__icontains=search_term)
    )
    return articles


def user_likes(user_profile, article_id):
    article = Article.objects.get(id=article_id)
    field_value = getattr(user_profile, article.category.name)
    field_value += 2
    setattr(user_profile, article.category.name, field_value)
    return field_value

def user_dislikes(user_profile, article_id):
    article = Article.objects.get(id=article_id)
    field_value = getattr(user_profile, article.category.name)
    field_value -= 1
    setattr(user_profile, article.category.name, field_value)
    return field_value


def user_read_article(user_profile, article_id):
    article = Article.objects.get(id=article_id)
    user_profile.read_articles.add(article)
    user_profile.save()
    return user_profile