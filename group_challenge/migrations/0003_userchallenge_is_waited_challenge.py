# Generated by Django 3.2.9 on 2022-11-15 08:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group_challenge', '0002_userchallenge_in_proccecc'),
    ]

    operations = [
        migrations.AddField(
            model_name='userchallenge',
            name='is_waited_challenge',
            field=models.BooleanField(default=False),
        ),
    ]
