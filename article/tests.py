from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command

from .ai import create_bag_of_words, trainAi


# Create your tests here.
from .models import Category, TrainingArticle, Article, UserProfile
from .services import get_sorted_categories, getArticlesForUser, predictCategory, saveTrainingJsons

class ArticlesTest(TestCase):
    def setUp(self):
        # Create Article objects with the provided titles and descriptions
        Article.objects.create(
            title="The stock market reached record highs today as investors gained confidence in the economy.",
            description="A new report on economic growth is causing excitement among financial experts."
        )

        Article.objects.create(
            title="A thrilling football match ended in a penalty shootout, and the home team emerged victorious.",
            description="The championship game was a nail-biting contest with a dramatic finish."
        )

        Article.objects.create(
            title="Researchers have discovered a breakthrough treatment for a rare genetic disease.",
            description="The medical community is buzzing with optimism about this groundbreaking discovery."
        )

        Article.objects.create(
            title="The highly anticipated sequel to the blockbuster movie is set to hit theaters next week.",
            description="Moviegoers are counting down the days until the release of this cinematic masterpiece."
        )

        Article.objects.create(
            title="Scientists have detected signs of water on a distant exoplanet, raising hopes for extraterrestrial life.",
            description="This astronomical discovery could change our understanding of the universe."
        )

        Article.objects.create(
            title="The latest smartphone model features a foldable screen and advanced AI capabilities.",
            description="Tech enthusiasts are eager to get their hands on this cutting-edge device."
        )

        Article.objects.create(
            title="Amidst the ongoing debate, citizens eagerly await the decision of their elected representatives.",
            description="The discussion in the city council meeting continues as local issues take center stage."
        )


    '''test if there are at least 5 training articles'''
    def test_fetch_training_articles(self):
        # Ensure there are no articles in the database initially
        initial_article_count = TrainingArticle.objects.count()
        self.assertEqual(initial_article_count, 0)

        # Call the method that fetches articles
        saveTrainingJsons()

        # Query the database again to check the number of articles
        final_article_count = TrainingArticle.objects.count()

        # Ensure there are at least 5 articles in the database
        self.assertGreaterEqual(final_article_count, 5)

    '''test if there is at least one article from each category in the training articles'''
    def test_fetch_with_categories(self):
        # Ensure there are no articles in the database initially
        initial_article_count = TrainingArticle.objects.count()
        self.assertEqual(initial_article_count, 0)
    
        # List of categories to track
        categories_to_track = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
    
        # Create Category objects for each category name
        for category_name in categories_to_track:
            Category.objects.get_or_create(name=category_name)
    
        # Call the method that fetches articles
        saveTrainingJsons()
    
        # Query the database to get the count of articles for each category
        category_article_counts = {category: TrainingArticle.objects.filter(category__name=category).count() for category in categories_to_track}
    
        # Ensure there is at least one article for each category
        for category in categories_to_track:
            self.assertGreaterEqual(category_article_counts[category], 1)

    
    '''test if ai can predict the categories'''
    def test_train_ai(self):
        # Save training articles into the database
        saveTrainingJsons()

        # Call the trainAi() method
        trainAi()

        article1 = Article.objects.get(title="The stock market reached record highs today as investors gained confidence in the economy.")
        article2 = Article.objects.get(title="A thrilling football match ended in a penalty shootout, and the home team emerged victorious.")
        article3 = Article.objects.get(title="Researchers have discovered a breakthrough treatment for a rare genetic disease.")
        article4 = Article.objects.get(title="The highly anticipated sequel to the blockbuster movie is set to hit theaters next week.")
        article5 = Article.objects.get(title="Scientists have detected signs of water on a distant exoplanet, raising hopes for extraterrestrial life.")
        article6 = Article.objects.get(title="The latest smartphone model features a foldable screen and advanced AI capabilities.")
        article7 = Article.objects.get(title="Amidst the ongoing debate, citizens eagerly await the decision of their elected representatives.")

        # Test predictCategory() with Article objects
        input_output_mapping = {
            article1: ["business"],
            article2: ["sports", "entertainment"],
            article3: ["health", "technology", "science"],
            article4: ["entertainment", "general"],
            article5: ["science", "technology"],
            article6: ["technology", "general"],
            article7: ["general", "science"]
        }

        for input_article, expected_outputs in input_output_mapping.items():
            predicted_category = predictCategory(input_article)
            self.assertIn(predicted_category, expected_outputs)
            print("Predicted: " + predicted_category + " - Expected: " + str(expected_outputs))

    ''' test if articles are in database after reading from files '''
    def test_save_training_jsons(self):
        # Call the method to save training JSONs
        saveTrainingJsons()

        # List of article titles to check
        article_titles = [
            "Economic Growth Boosts Stock Markets",
            "Moderna reins in 2023 COVID vaccine forecast, shares tumble - Reuters",
            "New Movie Release: A Thrilling Adventure in the World of Espionage",
            "‘House of the Dragon’ Season 2 to Return “Early Summer” 2024, First Trailer Screens - Hollywood Reporter",
            "Political Unrest in Capital City",
            "Minnesota justices appear skeptical that states should decide Trump's eligibility for the ballot - The Associated Press",
            "The Impact of Regular Exercise on Heart Health",
            "Beat the Clock, Beat Diabetes: How Breakfast Timing Influences Your Risk - SciTechDaily",
            "Breakthrough in Quantum Computing",
            "Two 'supervolcanoes' are showing signs of waking up - Times of India - IndiaTimes",
            "Exciting Soccer Match Ends in Overtime Thriller",
            "PFT's Week 9 2023 NFL picks, Florio vs. Simms - NBC Sports",
            "The Latest Advancements in Artificial Intelligence",
            "NZXT just FIXED Dual Chamber Cases! - Hardware Canucks",
        ]

        # Check if each article title exists in the TrainingArticle table
        for title in article_titles:
            article_exists = TrainingArticle.objects.filter(title=title).exists()
            self.assertTrue(article_exists, f"Article '{title}' not found in the TrainingArticle table.")
    
class UserTest(TestCase):
    def setUp(self):
        saveTrainingJsons()
        
    def test_user_existance(self):
        User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        user = User.objects.get(username='testuser')
        # Perform assertions to check if the user was created and saved
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertTrue(user.check_password('testpassword'))

    def test_user_signup_with_userprofile(self):
        # Define user data for signing up
        user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password1': 'testpassword',
            'password2': 'testpassword',
        }

        # Create categories in the database
        # call_command("create_initial_categories")
        initial_categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

        # Check if categories exist
        for category_name in initial_categories:
            self.assertTrue(Category.objects.filter(name=category_name).exists())

        # Send a POST request to the signup view
        response = self.client.post('/signup/', user_data, follow=True)

        # Check if the user is created
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='testuser').exists())

        # Get the user from the database
        user = User.objects.get(username='testuser')

        # Check if the UserProfile is created
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

        # Access the UserProfile and check if it is associated with the user
        user_profile = UserProfile.objects.get(user=user)
        self.assertEqual(user_profile.user, user)

        # Check if UserProfile's category fields have default values of 0
        category_fields = ["entertainment", "general", "business", "health", "science", "sports", "technology"]
        for field_name in category_fields:
            self.assertEqual(getattr(user_profile, field_name), 0)

        
    
class UserArticlesTest(TestCase):
    def setUp(self):
        saveTrainingJsons()
        # call_command("create_initial_categories")

    
    def test_get_sorted_categories(self):
        # Create a UserProfile instance with specific values for the category fields
        user_profile = UserProfile(
            entertainment=5,
            general=0,
            business=-1,
            health=-3,
            science=7,
            sports=1,
            technology=6,
        )
        user_profile.save()

        # Use the get_sorted_categories function to get the sorted categories
        sorted_categories = get_sorted_categories(user_profile)

        # Define the expected sorted order
        expected_sorted_order = ["science", "technology", "entertainment", "sports", "general", "business", "health"]

        # Check if the sorted categories match the expected order
        self.assertEqual(list(sorted_categories.keys()), expected_sorted_order)

    def test_get_sorted_categories_universe(self):
        
        user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password1': 'testpassword',
            'password2': 'testpassword',
        }
        article = Article.objects.create(
            title='The dark universe. When do we learn more with our telescopes?',
            description='NASA build new telescopes but when do we see more into the dark of the universe?',
            content=""
        )
        feature_names, bag_of_words_matrix = create_bag_of_words(article)
        article.bag_of_words_matrix = bag_of_words_matrix
        article.save()

        response = self.client.post('/signup/', user_data, follow=True)
        user = User.objects.get(username='testuser')
        user_profile = UserProfile.objects.get(user=user)
        user_profile.entertainment = 0
        user_profile.general = -1
        user_profile.business = -2
        user_profile.health = 4
        user_profile.science = 5
        user_profile.sports = 1
        user_profile.technology = 3
        user_profile.last_article = article
        user_profile.save()

        result = getArticlesForUser(user_profile.id)
        print(result)
        self.assertIsNotNone(result)
        # cannot really test what is in here because mock data is not good enough (not every category is in mock data)

    # def test_get_sorted_categories_gaza(self):
        
    #     user_data = {
    #         'username': 'testuser',
    #         'email': 'testuser@example.com',
    #         'password1': 'testpassword',
    #         'password2': 'testpassword',
    #     }
    #     article = Article.objects.create(
    #         title='War between Israel and Gaza is getting worse',
    #         description='President Netanyahu is in Israel',
    #         content=""
    #     )
    #     feature_names, bag_of_words_matrix = create_bag_of_words(article)
    #     article.bag_of_words_matrix = bag_of_words_matrix
    #     article.save()

    #     response = self.client.post('/signup/', user_data, follow=True)
    #     user = User.objects.get(username='testuser')
    #     user_profile = UserProfile.objects.get(user=user)
    #     user_profile.entertainment = 0
    #     user_profile.general = -1
    #     user_profile.business = -2
    #     user_profile.health = 4
    #     user_profile.science = 5
    #     user_profile.sports = 1
    #     user_profile.technology = 3
    #     user_profile.last_article = article
    #     user_profile.save()

    #     result = getArticlesForUser(user_profile.id)
    #     print(result)
    #     self.assertIsNotNone(result)
    #     # cannot really test what is in here because mock data is not good enough (not every category is in mock data)