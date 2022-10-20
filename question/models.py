from django.db import models

class QuestionFile(models.Model):
    file = models.FileField(upload_to = "questions/")


