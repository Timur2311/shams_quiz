
from email.policy import default
from django.db import models

from users.models import User
# Create your models here.


# Create your models here.

SINGLE = "single"
MULTIPLE = "multiple"
QUESTION_CHOICE = (
    (SINGLE, "Bittalik savollar"),
    (MULTIPLE, "Ko'p savollar"),
)


ONE = '1'
TWO = '2'
THREE = '3'
FOUR = '4'
FIVE = '5'
SIX = '6'
SEVEN = '7'
EIGHT = '8'
NINE = '9'
TEN = '10'


EXAM_TOUR_CHOISES = (
    (ONE, "1"),
    (TWO, "2"),
    (THREE, "3"),
    (FOUR, "4"),
    (FIVE, "5"),
    (SIX, "6"),
    (SEVEN, "7"),
    (EIGHT, "8"),
    (NINE, "9"),
    (TEN, "10"),
)

EXAM_STAGE_CHOICES = (
    (ONE, "1"),
    (TWO, "2"),
    (THREE, "3"),
    (FOUR, "4"),
    (FIVE, "5"),
)


class Question(models.Model):
    content = models.TextField(max_length=2048)
    stage = models.CharField(choices=EXAM_STAGE_CHOICES, max_length=16)
    tour = models.CharField(choices=EXAM_TOUR_CHOISES, max_length=16)
    true_answered_users = models.ManyToManyField(User)
    time = models.IntegerField(
        "Savolar uchun mo'ljallangan vaqt(sekund)", default=10)
    true_definition = models.TextField(max_length=65536)

    def add_question_options(self, content, is_correct=False):
        QuestionOption.objects.create(
            question=self, content=content, is_correct=is_correct)

    def create_exam(self, exam_title):
        if Exam.objects.filter(title=exam_title).exists():
            exam = Exam.objects.get(title=exam_title)
            exam.questions.add(self)
        else:
            exam = Exam.objects.create(
                title=exam_title, stage=self.stage, tour=self.tour)
            exam.questions.add(self)


class QuestionOption(models.Model):
    content = models.CharField(max_length=256)
    is_correct = models.BooleanField(default=False)
    question = models.ForeignKey(
        Question, related_name="options", on_delete=models.CASCADE)


class Exam(models.Model):
    title = models.CharField(max_length=256)
    content = models.TextField(max_length=2048, null=True, blank=True)
    stage = models.CharField(max_length=16, default=0)
    tour = models.CharField(max_length=16, default=0)
    questions = models.ManyToManyField(Question, related_name = "examm")
    questions_count = models.IntegerField(
        "Savollar soni", default=10)

    duration = models.IntegerField("Imtixon vaqti (minut)", default=20)

    class Meta:
        verbose_name = "Imtihon"
        verbose_name_plural = "Imtihonlar"

    def create_user_exam(self, user,again=None):
        counter = 0
        userexam = UserExam.objects.create(exam=self, user=user)
        if again:
            UserExam.objects.filter(exam=self).filter(user = user).filter(is_finished=True).delete()
        
            
        finished_exams = UserExam.objects.filter(
            user=user).filter(exam=self).filter(is_finished=True)
        # print(f'questions === {self.questions.all()}')
        true_user_exam_answers = []
        if finished_exams.count() > 0:
            # print("if ni ichiga kirvotti")
            for finished_exam in finished_exams:                
                for user_exam_answer in UserExamAnswer.objects.filter(
                    user_exam=finished_exam).filter(answered=True).filter(is_correct=True):
                        true_user_exam_answers.append(user_exam_answer.question)

            for question in self.questions.all():
                if question in true_user_exam_answers:
                    # print("true queston ekan")
                    
                    continue
                else:
                    if counter < 10:
                        userexam.questions.add(question)
                        counter += 1
                    else:
                        break
        elif finished_exams.count() == 0:
            counter = 10
            userexam.questions.set(self.questions.all(
            ).order_by("?")[:10])
        return userexam, counter


class UserExam(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name = "user_exams")
    questions = models.ManyToManyField(Question)  # editable=False
    score = models.IntegerField(default=0)
    start_datetime = models.DateTimeField(auto_now_add=True)
    end_datetime = models.DateTimeField(null=True)
    is_finished = models.BooleanField(default=False)

    def update_score(self):
        score=UserExamAnswer.objects.filter(is_correct=True, user_exam=self).count()
        
        self.score = int(score)
       
        return int(score)

    def create_answers(self):
        exam_answers = []
        for question in self.questions.all().order_by("?"):
            exam_answers.append(UserExamAnswer(
                user_exam=self, question=question))
        UserExamAnswer.objects.bulk_create(exam_answers)

    def last_unanswered_question(self):
        user_exam_answer = self.answer.all().exclude(answered=True).first()
        return user_exam_answer.question if user_exam_answer else None

    def last_unanswered(self):
        user_exam_answer = self.answer.all().exclude(answered=True).first()
        return user_exam_answer


class UserExamAnswer(models.Model):
    user_exam = models.ForeignKey(
        UserExam, on_delete=models.CASCADE, related_name="answer")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name = "user_exam_anwer")
    option_id = models.IntegerField(default=0)
    number = models.CharField(max_length = 16, null=True)
    answered = models.BooleanField(default=False)
    is_correct = models.BooleanField(default=False)
    
    
