import nltk
from sklearn.feature_extraction.text import CountVectorizer
from decouple import config

from .models import TrainingArticle
import pandas as pd
from .utils import text_from_article
import joblib  
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords

USE_MOCKED_DATA = config('USE_MOCKED_DATA', default=False, cast=bool)

# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('punkt', download_dir='nltk_data/')
# nltk.download('stopwords', download_dir='nltk_data/')
nltk.data.path.append('nltk_data/')
stop_words = set(stopwords.words("english"))

def create_bag_of_words(article): 
    
    vectorizer = CountVectorizer()

    # Fit and transform the preprocessed text to obtain the bag of words representation
    X = vectorizer.fit_transform([text_from_article(article)])

    # Get the feature names and bag of words matrix
    feature_names = vectorizer.get_feature_names_out()
    bag_of_words_matrix = X.toarray()

    return feature_names, bag_of_words_matrix

# def create_bag_of_words_for_user(user_profile): 
    
#     vectorizer = CountVectorizer()

#     # Fit and transform the preprocessed text to obtain the bag of words representation
#     X = vectorizer.fit_transform([text_from_article(user_profile.last_article)])

#     # Get the feature names and bag of words matrix
#     feature_names = vectorizer.get_feature_names_out()
#     bag_of_words_matrix = X.toarray()

#     return feature_names, bag_of_words_matrix

def preprocess_text(text):
    # Your implementation for text preprocessing, e.g., lowercasing and removing stop words
    # Example: Remove stop words and convert to lowercase
    words = [word.lower() for word in nltk.word_tokenize(text) if word.isalnum() and word.lower() not in stop_words]
    return " ".join(words)

def compute_similarity(text1, text2):
    # Create CountVectorizer instance
    vectorizer = CountVectorizer()

    # Fit and transform the texts to obtain bag-of-words representations
    X = vectorizer.fit_transform([preprocess_text(text1), preprocess_text(text2)])

    # Compute cosine similarity
    similarity_matrix = cosine_similarity(X)
    # Extract the similarity value
    similarity = similarity_matrix[0, 1]
    print(similarity)
    return similarity

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



def get_sorted_categories(user_profile):
    # Get the category field names in the UserProfile model
    category_fields = ["entertainment", "general", "business", "health", "science", "sports", "technology"]

    # Create a dictionary with category names as keys and their values as values
    category_values = {field: getattr(user_profile, field) for field in category_fields}

    # Sort the dictionary by values in descending order
    sorted_categories = dict(sorted(category_values.items(), key=lambda item: item[1], reverse=True))

    return sorted_categories



def predictCategory(article):
    '''
    Predicts the category from a given article.
    '''
    
    title = article.title if hasattr(article, 'title') else article.get('title')
    description = article.description if hasattr(article, 'description') else article.get('description')
    
    tfidf_vectorizer = joblib.load('tfidf_vectorizer.pkl')
    classifier = joblib.load('classifier.pkl')
    
    new_text = [text_from_article(article)]
    new_text_tfidf = tfidf_vectorizer.transform(new_text)
    
    predicted_category = classifier.predict(new_text_tfidf)
    
    return predicted_category[0]
