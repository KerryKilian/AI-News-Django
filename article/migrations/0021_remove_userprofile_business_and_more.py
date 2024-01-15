# Generated by Django 4.2.7 on 2024-01-15 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0020_article_country'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='business',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='entertainment',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='general',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='health',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='science',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='sports',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='technology',
        ),
        migrations.AlterField(
            model_name='article',
            name='author',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='article',
            name='dislikes',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='article',
            name='likes',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='article',
            name='publishedAt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='article',
            name='sourceName',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='trainingarticle',
            name='publishedAt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='trainingarticle',
            name='sourceName',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.DeleteModel(
            name='ArticleRating',
        ),
    ]