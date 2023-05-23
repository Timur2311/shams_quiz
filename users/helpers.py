from .models import User
from telegram import Bot
from dtb.settings import TELEGRAM_TOKEN
from django.http import JsonResponse
import time

bot = Bot(TELEGRAM_TOKEN)



def send_sms():
    # number = 1
    users = User.objects.filter(is_message_sended = False)
    users_count = users.count()
    # if users_count<2:
    #     number = users_count
        
    for user in users[:1]:
        try:
            bot.send_message(chat_id=user.user_id, text="📌Сиз каналда араб адабиёти ва араб филалогиясига боғлиқ маълумотлар билан танишишингиз мумкин.\n🏛️Канал араб тили ва филалогияси йўналишида таълим олаётган талабалар томонидан юритилади.\n\nhttps://t.me/+0g9BLMkFubQ2NDQy")  
            user.is_message_sended = True
            user.save()
        except Exception as e:	  
            user.is_message_sended = True
            user.is_blocked_bot = True    
            user.save()  
            bot.send_message(chat_id=1755197237, text = f"ERROR: {e}")
    
    time.sleep(30)
    bot.send_message(chat_id=1755197237, text = f"shu yerda 30 sekund dam oldi")   
    
    if users_count == 0:
        bot.send_message(chat_id=1755197237, text = f"Hamma foydalanuvchiga sms  xabar jo'natildi")
        for user in User.objects.all():
            user.is_message_sended = False
            user.save()
        return
    elif users_count>0:
        return send_sms()
        
    
    
        
    
    


    
    
    
    
    
    
    
    
    
    
    
    # users = User.objects.filter(is_message_sended = False)
    
    # if users.count()>=2000:
    #     users = users[:2000]
    # elif users.count()==0:
    #     return JsonResponse({"succecc": "all messages sended"})
        
    
    # for user in users:
    #     try:
    #         bot.send_message(chat_id=user.user_id, text="Salom")
    #         return JsonResponse({"succecc": "message is sended"})
    #     except:
    #         return JsonResponse({"error": "bot was blocked by user"})
