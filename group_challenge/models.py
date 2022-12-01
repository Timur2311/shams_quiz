from django.db import models
from users.models import User
from tgbot import consts
from exam.models import Question


NOT_FINISHED = "not_finished"
IN_PROGRESS = "in_progress"
FINISHED = "finished"


CHALLENGE_STATUS = (
    (consts.PUBLIC, "public"),
    (consts.PRIVATE, "private"),

)

USER_TASK_STATUS = (
    (NOT_FINISHED, "not_finished"),
    (IN_PROGRESS, "in_progress"),
    (FINISHED, "finished"),
)


class Challenge(models.Model):
    stage = models.CharField(max_length=16, null=True, blank=True)
    questions = models.ManyToManyField(Question, related_name="challenge_questions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bellashuv"
        verbose_name_plural = "Bellashuvlar"

    def create_user_challenge(self, telegram_id, challenge):
        user = User.objects.prefetch_related('user_exams','as_owner','as_opponent','user_challenges','winners_challenge','challenge_answers','rates').get(user_id=telegram_id)
        user_challenge = UserChallenge.objects.create(
            user=user, challenge=challenge)
        user_challenge.users.add(user)
        user_challenge.questions.set(self.questions.all(
        ).order_by("?")[:10])
        return user_challenge


class UserChallenge(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="as_owner", db_index=True)
    opponent = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="as_opponent", null=True, blank=True, db_index=True)
    winner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="winners_challenge", null=True, blank=True, db_index=True) 
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    users = models.ManyToManyField(User, related_name="user_challenges", db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    is_random_opponent =  models.BooleanField(default=False, db_index=True)
    
    questions = models.ManyToManyField(Question, related_name="user_challenge_questions")

    user_score = models.IntegerField(default=0)
    opponent_score = models.IntegerField(default=0)
    
    user_timer = models.CharField(max_length=512, null=True, blank=True)
    opponent_timer= models.CharField(max_length=512, null=True, blank=True)

    user_started_at = models.DateTimeField(null=True)
    user_finished_at = models.DateTimeField(null=True)
    
    opponent_started_at = models.DateTimeField(null=True)
    opponent_finished_at = models.DateTimeField(null=True)
    

    is_user_finished = models.BooleanField(default=False)
    is_opponent_finished = models.BooleanField(default=False)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_waited_challenge = models.BooleanField(default=False, db_index=True)
    
    in_proccecc = models.BooleanField(default=False)    
    
    created_challenge_message_id = models.CharField(max_length=1024, null = True)
    created_challenge_chat_id = models.CharField(max_length=1024, null = True)
    
    user_message_id = models.CharField(max_length=1024, null = True)
    opponent_message_id = models.CharField(max_length=1024, null = True)
    user_chat_id = models.CharField(max_length=1024, null = True)
    opponent_chat_id = models.CharField(max_length=1024, null = True)
    
    class Meta:
        verbose_name = "Foydalanuvchi Bellashuvi"
        verbose_name_plural = "Foydalanuvchi Bellashuvlari"
    
    def __str__(self) -> str:
        return str(self.is_active)
    
    
    def user_duration(self):
        difference = self.user_finished_at-self.user_started_at
        difference = difference.total_seconds()
        difference = int(difference)
        

        return difference
    
    def opponent_duration(self):
        difference = self.opponent_finished_at-self.opponent_started_at 
        difference = difference.total_seconds()
        difference = int(difference)
        
        return difference
        
    def update_score(self, type):
        if type == 'user':
            score = UserChallengeAnswer.objects.select_related('user_challenge','user','question','user_challenge__user','user_challenge__opponent','user_challenge__challenge','user_challenge__winner').prefetch_related('user_challenge__users','user_challenge__questions','user_challenge__challenge__questions').filter(user_challenge=self).filter(user=self.user).filter(is_correct=True).count()
            self.user_score = int(score)
            
        elif type == "opponent":
            score = UserChallengeAnswer.objects.select_related('user_challenge','user','question','user_challenge__user','user_challenge__opponent','user_challenge__challenge','user_challenge__winner').prefetch_related('user_challenge__users','user_challenge__questions','user_challenge__challenge__questions').filter(user_challenge=self).filter(user=self.opponent).filter(is_correct=True).count()
            self.opponent_score = int(score)

        return score

    def create_user_answers(self):
        challenge_answers_for_user = []
        for question in self.questions.all().order_by("?"):
            challenge_answers_for_user.append(UserChallengeAnswer(
                user_challenge=self, question=question, user=self.user))

        UserChallengeAnswer.objects.bulk_create(challenge_answers_for_user)

    def create_opponent_answers(self):
        challenge_answers_for_opponent = []

        for question in self.questions.all().order_by("?"):
            challenge_answers_for_opponent.append(UserChallengeAnswer(
                user_challenge=self, question=question, user = self.opponent))
            
            
        UserChallengeAnswer.objects.bulk_create(challenge_answers_for_opponent)
    
    
    def last_unanswered_question(self,user):
        user_challenge_answer = self.answer.all().exclude(answered=True).filter(user = user).first()
        return user_challenge_answer.question if user_challenge_answer else None

    def last_unanswered(self,user):
        user_challenge_answer = self.answer.all().exclude(answered=True).filter(user=user).first()
        return user_challenge_answer


class UserChallengeAnswer(models.Model):
    user_challenge = models.ForeignKey(
        UserChallenge, on_delete=models.CASCADE, related_name="answer", db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="challenge_answers", db_index=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="user_challenge_answer_question", db_index=True)
    option_id = models.IntegerField(default=0)

    
    number = models.CharField(max_length = 16, null=True)
    
    
    answered = models.BooleanField(default=False, db_index=True)
    is_correct = models.BooleanField(default=False,db_index=True)

    
class Rate(models.Model):
    stars_count = models.IntegerField(default=0)
    old_stars_count = models.IntegerField(default=0)    
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="rates")
    user_challenge = models.ForeignKey(UserChallenge, on_delete=models.CASCADE, null=True, blank = True)
    
    
        
