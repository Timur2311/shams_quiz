# Generated by Django 3.2.9 on 2022-12-03 19:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_alter_user_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_message_sended',
            field=models.BooleanField(default=False),
        ),
    ]
