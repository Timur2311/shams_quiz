from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt

from . import views

app_name = "tgbot"

urlpatterns = [  
    # TODO: make webhook more secure
    path('', views.index, name="index"),
    path('add/question/', views.add_question, name="add_question"),
    path('super_secter_webhook/', csrf_exempt(views.TelegramBotWebhookView.as_view())),
]