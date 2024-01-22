import json
import os
from decouple import config
import re

API_KEY = config('API_KEY')

def read_file(category, country = "us"):
    """
    reads a given file of training data
    """
    data_folder = f"data/{country}"
    file_path = os.path.join(data_folder, category + ".json")
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

def save_file(category, data):
    """
    saves the training data to a file
    """
    data_folder = "data" 

    if not os.path.exists(data_folder):                     
        os.makedirs(data_folder)

    with open(os.path.join(data_folder, category + ".json"), 'w') as file:
        json.dump(data, file)



def create_url(category = None, country = "us"):
    """
    creates an url which will be used for fetching
    """
    # if no category is given, then there is a normal request not for training data
    if category == "" or category == None:
        return (f'https://newsapi.org/v2/top-headlines?'
       f'country={country}&'
       'apiKey=' + API_KEY)
    return ('https://newsapi.org/v2/top-headlines?'
       f'country={country}&'
       'category=' + category + '&from=2023-10-03&to=2023-10-13'
       '&apiKey=' + API_KEY)

    


def text_from_article(article):
    '''
    extracts title and description from the article
    '''
    title = article.title if hasattr(article, 'title') else article.get('title')
    description = article.description if hasattr(article, 'description') else article.get('description')
    content = article.content if hasattr(article, "content") else article.get("content")

    if content is None:
        content = ""
    # Use regular expression to remove text within squared brackets at the end
    content_preprocessed = re.sub(r'\[.*\]$', '', content)
    return f"{title} - {description}: {content_preprocessed}"