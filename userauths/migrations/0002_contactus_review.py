# Generated by Django 5.0.2 on 2024-04-12 11:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauths', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactus',
            name='review',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
