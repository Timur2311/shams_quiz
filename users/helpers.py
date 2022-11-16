from .models import User
from telegram import Bot


bot = Bot("5562717565:AAEs4q5ejjv2H3ma4byDZTG1DD-YvrkoVPg")
def warning_users():
    users = User.objects.all()
    for user in users:
        try:
            bot.send_message(chat_id=user.user_id, text="Assalamu alaykum! Botda o'zgarishlar qilindi. Bot to'g'ri ishlashi uchun iltimos quyidagi ketma-ketlikka rioya qiling:\n\n1️⃣Botga /start buyrug'ini yozish orqali botni qaytadan ishga tushiring!\n\n2️⃣Botdagi \"Sozlamalar⚙️\" tugmachasini bosing, chiqqan tugmachalar ichidan esa \"Sozlash🔧\" tugmasini bosing!\n\n3️⃣Yuqoridagi amallarni qilganingizdan so'ng botdan foydalanishni davom ettirishingiz mumkin.\n\n⚠️Bot sozlanganidan keyin ham vujudga kelgan har qanday muammoni, ayni vujudga kelish vaqtida skrinshot qilib @ulugbek2311 ga murojaat qilishingizni iltimos qilib qolar edik. Botni soz ishlashi uchun bu juda muhim! E'tiboringiz uchun rahmat. Kuningiz xayrli va barokatli o'tsin.")
        except:
            bot.send_message(chat_id=1755197237, text = "error")