from django.test import TestCase
from django.contrib.auth.models import User
from .ai import create_bag_of_words, get_sorted_categories
from .models import Category, TrainingArticle, Article, UserProfile
from .services import get_articles_for_user, predictCategory, save_training_jsons, search_articles, user_read_article


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
        save_training_jsons()

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
        save_training_jsons()
    
        # Query the database to get the count of articles for each category
        category_article_counts = {category: TrainingArticle.objects.filter(category__name=category).count() for category in categories_to_track}
    
        # Ensure there is at least one article for each category
        for category in categories_to_track:
            self.assertGreaterEqual(category_article_counts[category], 1)

    ''' test if articles are in database after reading from files '''
    def test_save_training_jsons(self):
        # Call the method to save training JSONs
        save_training_jsons()

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
        save_training_jsons()
        
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



        
    
class UserArticlesTest(TestCase):
    def setUp(self):
        save_training_jsons()
        # call_command("create_initial_categories")

    def test_user_read_article(self):
        '''
            test if read articles appear in user_profile's "read_article" field
        '''
        user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password1': 'testpassword',
            'password2': 'testpassword',
        }
        # Create a category
        category = Category.objects.get(name='entertainment')

        # Create three articles
        article1 = Article.objects.create(
            title='Test Article 1',
            description='Test description 1',
            content='Test content 1',
            category=category
        )

        article2 = Article.objects.create(
            title='Test Article 2',
            description='Test description 2',
            content='Test content 2',
            category=category
        )

        article3 = Article.objects.create(
            title='Test Article 3',
            description='Test description 3',
            content='Test content 3',
            category=category
        )

        response = self.client.post('/signup/', user_data, follow=True)
        user = User.objects.get(username='testuser')
        user_profile = UserProfile.objects.get(user=user)

        user_read_article(user_profile, article1)
        user_read_article(user_profile, article2)
        user_read_article(user_profile, article3)

        self.assertIn(article1, user_profile.read_articles.all())
        self.assertIn(article2, user_profile.read_articles.all())
        self.assertIn(article3, user_profile.read_articles.all())



class ArticleSearchTest(TestCase):

    def setUp(self):
        # Create sample articles for testing
        self.article1 = Article.objects.create(title='Sample Article 1', description='Description 1')
        self.article2 = Article.objects.create(title='Sample Article 2', description='Description 2')
        self.article3 =  Article.objects.create(title='Another Article', description='Description 3')

    def test_search_articles(self):
        # Call the search_articles function directly with a search term
        articles = search_articles('sample')

        # Check that the correct articles are returned
        self.assertQuerysetEqual(
            articles,
            [self.article1, self.article2],
            ordered=False
        )

    def test_search_articles_no_results(self):
        # Call the search_articles function directly with a search term that has no results
        articles = search_articles('nonexistent')

        # Check that no articles are returned
        self.assertQuerysetEqual(articles, [])


class RatingTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.category = Category.objects.create(name="general")
        self.article = Article.objects.create(title='Test Article', content='Test content', category=self.category)
        self.user_profile = UserProfile.objects.create(user=self.user)
    def test_rating_view_post(self):
        # Log in the user
        self.client.login(username='testuser', password='testpassword')

        # Send a POST request to the rating view
        response = self.client.post(f'/article/{self.article.id}/rating/', {'rating': '1'}, follow=True)

        # Check if the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Refresh the user and article instances from the database
        self.user.refresh_from_db()
        self.article.refresh_from_db()

        # Check if the user's like_articles is updated
        self.assertIn(self.article, self.user.userprofile.like_articles.all())

        # Check if the article's likes is updated
        self.assertEqual(self.article.likes, 1)
