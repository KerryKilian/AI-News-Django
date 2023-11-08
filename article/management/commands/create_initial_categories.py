from django.core.management.base import BaseCommand
from article.models import Category

class Command(BaseCommand):
    help = 'Creates initial categories in the database'

    def handle(self, *args, **options):
        initial_categories = [
            "business",
            "entertainment",
            "general",
            "health",
            "science",
            "sports",
            "technology",
            "undefined"
        ]

        for category_name in initial_categories:
            Category.objects.get_or_create(name=category_name)
        self.stdout.write(self.style.SUCCESS('Initial categories created successfully.'))
