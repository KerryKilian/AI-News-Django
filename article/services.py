from collections import Counter
from datetime import datetime, timedelta
import requests

from .models import Article, Category, Country, TrainingArticle
from decouple import config
from .utils import read_file, create_url, text_from_article
from .ai import predictCategory, compute_similarity
from django.core.cache import cache
from django.db.models import Q
from .defaults import categories


tfidf_vectorizer = None
classifier = None
USE_MOCKED_DATA = config('USE_MOCKED_DATA')
API_KEY = config('API_KEY')
USE_CACHE = config('USE_CACHE')

def save_training_jsons():
    '''
    reads all json files which contain training data for the AI and saves it as trainings articles into database. Created for test purposes
    '''

    # Define the category names
    category_names = categories

    for category_name in category_names:
        try:
            # Retrieve the Category object or create it if it doesn't exist
            category, created = Category.objects.get_or_create(name=category_name)

            # Iterate through possible file name variations
            for filename in [category_name, f"{category_name}-chatgpt"]:
                success, articles_data = read_file(filename)
                if success:
                    for article_data in articles_data:
                        existing_article = TrainingArticle.objects.filter(title=article_data.get('title')).first()
                        if existing_article is None:
                            # Create a new TrainingArticle object and save it to the database
                            TrainingArticle.objects.create(
                                title=article_data.get('title'),
                                description=article_data.get('description'),
                                category=category
                            )
        except Exception as e:
            # Handle exceptions, such as if a category doesn't exist
            return False, e

    return True, "success"

def fetch_mock():
    success, data = read_file("top-headlines")
            
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



def fetch_real(country = "us"):
    '''
    takes articles from database and trains the ki with categories
    '''
    
    response = requests.get(create_url("", country))
    if response.status_code == 200:
        articles_data = response.json().get('articles', [])
        for article_data in articles_data:
            try:
                print(article_data)
                if article_data.get("title") != "[Removed]":


                    existing_article = Article.objects.filter(title=article_data.get('title')).first()
                    if existing_article:
                        print("Article already existing")
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
            except Exception as e:
                print(str(e))


def bag_of_words(user_profile, articles):
    '''
    sorts the articles by the words that may be interesting for the user (depending on what the user has read the last three times)
    '''
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

def algorithm(user_profile, country = "us"):
    '''
    algorithm for searching the users most interesting news articles
    '''
    result = []
    first_results = []
    end_results = []
    country_db = Country.objects.get(name=country)

    first_categories_to_fetch = []
    end_categories_to_fetch = []

    # STEP 1: display at least one article from each category at the end
    for category in categories:
        category_db = Category.objects.get(name=category)
        end_categories_to_fetch.append(category_db)

    last_articles = user_profile.read_articles.all().order_by("-id")[:5]
    like_articles = user_profile.like_articles.all().order_by("-id")[:5]
    dislike_articles = user_profile.dislike_articles.all().order_by("-id")[:5]

    # STEP 2: Append every category from the last 10 read articles
    for article in last_articles:
        first_categories_to_fetch.append(article.category)

    # STEP 3: Append every category where user liked the article
    for article in like_articles:
        first_categories_to_fetch.append(article.category)

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

    return result


def get_articles_for_user(user_profile, country = "us"):
    '''
    logic that fetches new articles once a day and then searching the best fitting articles for the user with an algorithm
    '''
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

        if USE_MOCKED_DATA == True:
            fetch_mock()     
        else: 
            fetch_real(country)

    articles = algorithm(user_profile, country)
    return articles



def user_likes_article(user_profile, article_id):
    '''
        adds an article to the user's "like_article" field
    '''
    article = Article.objects.get(id=article_id)
    if article not in user_profile.like_articles.all():
        user_profile.like_articles.add(article)
        article.likes = article.likes + 1
        if article in user_profile.dislike_articles.all():
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
    '''
    logic to search articles
    '''
    articles = Article.objects.filter(
        Q(title__icontains=search_term) | Q(description__icontains=search_term)
    )
    return articles

def user_read_article(user_profile, article):
    """
    logic for registring the article into the read_articles field
    """
    user_profile.read_articles.add(article)
    user_profile.save()
    return user_profile
