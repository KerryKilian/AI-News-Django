# Generated by Django 4.2.7 on 2023-11-24 15:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0017_country_remove_trainingarticle_bag_of_words_matrix_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trainingarticle',
            name='country',
            field=models.ForeignKey(default='us', null=True, on_delete=django.db.models.deletion.CASCADE, to='article.country'),
        ),
    ]
