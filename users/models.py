from __future__ import annotations

from django.apps import apps


from typing import Union, Optional, Tuple

from django.db import models
from django.db.models import QuerySet, Manager
from telegram import Update
from telegram.ext import CallbackContext

from dtb.settings import DEBUG
from tgbot.handlers.utils.info import extract_user_data_from_update
from utils.models import CreateUpdateTracker, nb, CreateTracker, GetOrNoneManager

class AdminUserManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_admin=True)


class User(CreateUpdateTracker):    
    
    user_id = models.PositiveBigIntegerField(primary_key=True)  # telegram_id
    username = models.CharField(max_length=32, **nb)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, **nb)
    language_code = models.CharField(max_length=8, help_text="Telegram client's lang", **nb)
    deep_link = models.CharField(max_length=64, **nb)
    is_blocked_bot = models.BooleanField(default=False)
    is_message_sended = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    objects = GetOrNoneManager()  # user = User.objects.get_or_none(user_id=<some_id>)
    admins = AdminUserManager()  # User.admins.all()
    name = models.CharField(max_length=128, null=True, blank=True, default="IsmiGul")
    region = models.CharField(max_length = 32, null=True)
    
    score = models.IntegerField(default=0)
    challenges_count = models.IntegerField(default=0)    
    
    is_busy = models.BooleanField(default = False)
    is_random_opponent_waites = models.BooleanField(default = False)
    is_ended_challenge_waites = models.BooleanField(default = False)
    challenge_id  =  models.CharField(max_length = 256, default = "no")
    
    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
   
    def set_user_score(self):
        UserChallenge = apps.get_model(app_label='group_challenge', model_name='UserChallenge')
        
        user_challenges = UserChallenge.objects.filter(user = self)

        opponent_challenges = UserChallenge.objects.filter(opponent = self)

        challenges_count = UserChallenge.objects.filter(users = self).count()

        self.challenges_count =  challenges_count
        self.save()   
        
        score = 0
        
        for user_exam in user_challenges:
            score+=user_exam.user_score
        
        
        for user_challenge in opponent_challenges:
            score+=user_challenge.opponent_score
            
        if score>self.score:
            self.score = score
            self.save()
            
        
            
    def __str__(self):
        return f'@{self.username}' if self.username is not None else f'{self.user_id}'

    @classmethod
    def get_user_and_created(cls, update: Update, context: CallbackContext) -> Tuple[User, bool]:
        """ python-telegram-bot's Update, Context --> User instance """
        data = extract_user_data_from_update(update)
        u, created = cls.objects.update_or_create(user_id=data["user_id"], defaults=data)

        if created:
            # Save deep_link to User model  
            if context is not None and context.args is not None and len(context.args) > 0:
                payload = context.args[0]
                if str(payload).strip() != str(data["user_id"]).strip():  # you can't invite yourself
                    u.deep_link = payload
                    u.save()

        return u, created

    @classmethod
    def get_user(cls, update: Update, context: CallbackContext) -> User:
        u, _ = cls.get_user_and_created(update, context)
        return u

    @classmethod
    def get_user_by_username_or_user_id(cls, username_or_user_id: Union[str, int]) -> Optional[User]:
        """ Search user in DB, return User or None if not found """
        username = str(username_or_user_id).replace("@", "").strip().lower()
        if username.isdigit():  # user_id
            return cls.objects.filter(user_id=int(username)).first()
        return cls.objects.filter(username__iexact=username).first()

    @property
    def invited_users(self) -> QuerySet[User]:
        return User.objects.filter(deep_link=str(self.user_id), created_at__gt=self.created_at)

    @property
    def tg_str(self) -> str:
        if self.username:
            return f'@{self.username}'
        return f"{self.first_name} {self.last_name}" if self.last_name else f"{self.first_name}"


class Location(CreateTracker):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()

    objects = GetOrNoneManager()

    def __str__(self):
        return f"user: {self.user}, created at {self.created_at.strftime('(%H:%M, %d %B %Y)')}"

    def save(self, *args, **kwargs):
        super(Location, self).save(*args, **kwargs)
        # Parse location with arcgis
        from arcgis.tasks import save_data_from_arcgis
        if DEBUG:
            save_data_from_arcgis(latitude=self.latitude, longitude=self.longitude, location_id=self.pk)
        else:
            save_data_from_arcgis.delay(latitude=self.latitude, longitude=self.longitude, location_id=self.pk)
