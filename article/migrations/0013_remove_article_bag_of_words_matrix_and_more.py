# Generated by Django 4.2.7 on 2023-11-17 12:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0012_remove_userprofile_last_article_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='article',
            name='bag_of_words_matrix',
        ),
        migrations.RemoveField(
            model_name='article',
            name='feature_names',
        ),
    ]
