from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import requests
import random
from django.core.cache import cache

from .models import Article, Category, TrainingArticle, UserProfile
import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib  
import os
from decouple import config
from collections import Counter
from .enums import categories



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

def readFile(category, chatgpt = False):
    data_folder = "data"
    if chatgpt == False:
        file_path = os.path.join(data_folder, category + ".json")
    else: 
        file_path = os.path.join(data_folder, category + "-chatgpt.json")
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return True, data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON data: {e}")
            return False, None
    else:
        print(f"File not found: {file_path}")
        return False, None

def saveFile(category, data):
    data_folder = "data" 

    if not os.path.exists(data_folder):                     
        os.makedirs(data_folder)

    with open(os.path.join(data_folder, category + ".json"), 'w') as file:
        json.dump(data, file)



def createUrl(category = None):
    """
    creates an url which will be used for fetching
    """
    # if no category is given, then there is a normal request not for training data
    if category == "" or category == None:
        return ('https://newsapi.org/v2/top-headlines?'
       'country=us&'
       'apiKey=' + API_KEY)
    return ('https://newsapi.org/v2/top-headlines?'
       'country=us&'
       'category=' + category + '&from=2023-10-03&to=2023-10-13'
       '&apiKey=' + API_KEY)
    # return ('https://newsapi.org/v2/everything?'
    #    'category=' + category + '&'
    #    '&apiKey=' + API_KEY)
    
# https://newsapi.org/v2/top-headlines?country=us&apiKey=b01b15596d04498689a73fa1b9b0733e

'''
takes articles from database and trains the ki with categories
'''
def trainAi():
    # Sample dataset (you should replace this with your own data)
    articles = TrainingArticle.objects.all()
    articles_data = [{
        'title': article.title,
        'description': article.description,
        'category': article.category,
        "author": article.author,
        "url": article.url,
        "urlToImage": article.urlToImage,
        "sourceName": article.sourceName,
        "content": article.content
        # Add other fields as needed
    } for article in articles]
    data = {
    'text': [(article['title'] or " ") + ' - ' + (article['description'] or " ") for article in articles_data],
    'category': [(article['category'].name) for article in articles_data]
    }


    df = pd.DataFrame(data)

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(df['text'], df['category'], test_size=0.2, random_state=42)

    # Create a TF-IDF vectorizer and Multinomial Naive Bayes classifier
    tfidf_vectorizer = TfidfVectorizer()
    classifier = MultinomialNB()

    # Transform the text data and train the model
    X_train_tfidf = tfidf_vectorizer.fit_transform(X_train)
    classifier.fit(X_train_tfidf, y_train)

    # Transform the test data and make predictions
    X_test_tfidf = tfidf_vectorizer.transform(X_test)
    y_pred = classifier.predict(X_test_tfidf)

    # Evaluate the model
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.2f}")
    print(classification_report(y_test, y_pred))

    # Inference with new text
    # new_text = ["astronauts"]
    # new_text_tfidf = tfidf_vectorizer.transform(new_text)
    # predicted_category = classifier.predict(new_text_tfidf)
    # print(f"Predicted Category: {predicted_category[0]}")
    
# Save the trained models as pickle files
    with open('tfidf_vectorizer.pkl', 'wb') as f:
        joblib.dump(tfidf_vectorizer, f)

    with open('classifier.pkl', 'wb') as f:
        joblib.dump(classifier, f)
    # return predicted_category[0]
    # data_folder = "ai-model"
    # if not os.path.exists(data_folder):                     
    #     os.makedirs(data_folder)
    # with open(os.path.join(data_folder, "tfidf_vectorizer.pkl"), 'wb') as file:
    #     joblib.dump(tfidf_vectorizer, file)
    # with open(os.path.join(data_folder, "classifier.pkl"), 'wb') as file:
    #     joblib.dump(classifier, file)



def predictCategory(article):
    '''
    Predicts the category from a given article.
    '''
    
    title = article.title if hasattr(article, 'title') else article.get('title')
    description = article.description if hasattr(article, 'description') else article.get('description')
    
    tfidf_vectorizer = joblib.load('tfidf_vectorizer.pkl')
    classifier = joblib.load('classifier.pkl')
    
    new_text = [f"{title} - {description}"]
    new_text_tfidf = tfidf_vectorizer.transform(new_text)
    
    predicted_category = classifier.predict(new_text_tfidf)
    
    return predicted_category[0]


def fetchWithoutCategories():
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
            # Create a new Article object and save it to the database
            Article.objects.create(
                title=article_data.get('title'),
                description=article_data.get('description'),
                author=article_data.get('author'),
                url=article_data.get('url'),
                urlToImage=article_data.get('urlToImage'),
                publishedAt=datetime.strptime(article_data.get('published_at'), "%Y-%m-%dT%H:%M:%SZ") if article_data.get('published_at') else None,
                content=article_data.get('content'),
                category=Category.objects.get(name=category)
            )


def getArticlesForUser(user_id):
    user_profile = UserProfile.objects.get(id=user_id)
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
                Article.objects.create(
                    title=article_data.get('title'),
                    description=article_data.get('description'),
                    author=article_data.get('author'),
                    url=article_data.get('url'),
                    urlToImage=article_data.get('urlToImage'),
                    publishedAt=datetime.strptime(article_data.get('published_at'), "%Y-%m-%dT%H:%M:%SZ") if article_data.get('published_at') else None,
                    content=article_data.get('content'),
                    category=Category.objects.get(name=category)
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
                        article for article in articles if article not in positive and article not in user_profile.read_articles.all()
                    ]
                    if available_articles:
                        selected_article = available_articles[0]  # Select the first available article
                        positive.append(selected_article)
            elif category_number == 0:
                # get articles which are not yet in zero and not read by user yet
                available_articles = [
                    article for article in articles if article not in zero and article not in user_profile.read_articles.all()
                ]
                if available_articles:
                    selected_article = available_articles[0]  # Select the first available article
                    zero.append(selected_article)
            elif category_number < 0:
                # get articles which are not yet in negative and not read by user yet
                available_articles = [
                    article for article in articles if article not in zero and article not in user_profile.read_articles.all()
                ]
                if available_articles:
                    selected_article = available_articles[0]  # Select the first available article
                    negative.append(selected_article)

    
    # for category_name, category_number in sorted_categories.items():
    #     category = Category.objects.get(name=category_name)
    #     articles = Article.objects.filter(category=category)

    #     if len(articles) != 0: # if there are articles in this category in the headlines
    #         if category_number > 0:
    #             selected_articles = articles[:category_number] # append as many as points there are
    #             for article in selected_articles:
    #                 positive.append(article)
    #         elif category_number == 0:
    #             selected_articles = articles[:1] # append 1 although zero
    #             zero.append(selected_articles)
    #         elif category_number < 0:
    #             selected_articles = articles[:1] # append 1 although negative
    #             zero.append(selected_articles) 

    # shuffle articles
    random.shuffle(positive)
    random.shuffle(zero)
    random.shuffle(negative)

    # append everything to the result list
    result.extend(positive)
    result.extend(zero)
    result.extend(negative)
    return result, fetch_needed

def get_sorted_categories(user_profile):
    # Get the category field names in the UserProfile model
    category_fields = ["entertainment", "general", "business", "health", "science", "sports", "technology"]

    # Create a dictionary with category names as keys and their values as values
    category_values = {field: getattr(user_profile, field) for field in category_fields}

    # Sort the dictionary by values in descending order
    sorted_categories = dict(sorted(category_values.items(), key=lambda item: item[1], reverse=True))

    return sorted_categories