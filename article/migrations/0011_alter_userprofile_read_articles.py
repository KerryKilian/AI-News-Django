# Generated by Django 4.2.7 on 2023-11-13 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0010_alter_userprofile_read_articles'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='read_articles',
            field=models.ManyToManyField(null=True, related_name='read_by_users', to='article.article'),
        ),
    ]
