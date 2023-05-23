# Generated by Django 3.2.9 on 2022-12-01 10:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_alter_user_options'),
        ('group_challenge', '0010_auto_20221201_1017'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userchallenge',
            name='challenge',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='challenge_user_challenges', to='group_challenge.challenge'),
        ),
        migrations.AlterField(
            model_name='userchallenge',
            name='opponent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='opponent_user_challenges', to='users.user'),
        ),
        migrations.AlterField(
            model_name='userchallenge',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owner_user_challenges', to='users.user'),
        ),
        migrations.AlterField(
            model_name='userchallenge',
            name='winner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='winner_user_challenges', to='users.user'),
        ),
    ]