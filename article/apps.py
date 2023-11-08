from django.apps import AppConfig
# from .services import trainAi

class ArticleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'article'
    # def ready(self):
    #     trainAi()
