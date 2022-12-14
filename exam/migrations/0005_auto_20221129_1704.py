# Generated by Django 3.2.9 on 2022-11-29 17:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0004_auto_20221115_1527'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userexam',
            name='exam',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exam_user_exams', to='exam.exam'),
        ),
        migrations.AlterField(
            model_name='userexam',
            name='questions',
            field=models.ManyToManyField(related_name='user_exam_questions', to='exam.Question'),
        ),
    ]
