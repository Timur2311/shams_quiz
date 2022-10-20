import json
import logging
from django.views import View
from django.http import JsonResponse
from django.shortcuts import render
from django.http import HttpResponseRedirect

from dtb.settings import DEBUG
from tgbot.dispatcher import process_telegram_event

from tgbot.forms import QuestionForm
from utils.saving_data import saving_data

logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'index.html')

def add_question(request):
    if request.method == "POST":
        # print(f"{request.FILES}")
        form = QuestionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            
        saving_data()
            
            # <process form cleaned data>
    else:
        form = QuestionForm()

    return render(request, 'form_template.html', {'form': form})
    


class TelegramBotWebhookView(View):
    # WARNING: if fail - Telegram webhook will be delivered again. 
    # Can be fixed with async celery task execution
    def post(self, request, *args, **kwargs):
        if DEBUG:
            process_telegram_event(json.loads(request.body))
        else:  
            # Process Telegram event in Celery worker (async)
            # Don't forget to run it and & Redis (message broker for Celery)! 
            # Read Procfile for details
            # You can run all of these services via docker-compose.yml
            process_telegram_event.delay(json.loads(request.body))

        # TODO: there is a great trick to send action in webhook response
        # e.g. remove buttons, typing event
        return JsonResponse({"ok": "POST request processed"})
    
    def get(self, request, *args, **kwargs):  # for debug
        return JsonResponse({"ok": "Get request received! But nothing done"})
