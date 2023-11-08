# Generated by Django 4.2.7 on 2023-11-07 14:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='article.category'),
        ),
        migrations.AddField(
            model_name='trainingarticle',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='article.category'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='bad_topics',
            field=models.ManyToManyField(related_name='user_profiles_with_bad_topics', to='article.category'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='good_topics',
            field=models.ManyToManyField(default=(), related_name='user_profiles_with_good_topics', to='article.category'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='ok_topics',
            field=models.ManyToManyField(related_name='user_profiles_with_ok_topics', to='article.category'),
        ),
    ]
