

from telegram import ParseMode, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import CallbackContext


from users.models import User
from tgbot.handlers.onboarding.keyboards import make_keyboard_for_start_command, make_keyboard_for_regions
from tgbot import consts

from exam.models import UserExam
from group_challenge.models import UserChallenge


from utils.check_subscription import check_subscription


def command_start(update: Update, context: CallbackContext) -> None:
    u, created = User.get_user_and_created(update, context)
    
    chat_member = context.bot.get_chat_member(
        consts.CHANNEL_USERNAME, update.message.from_user.id)
    
    context.user_data["not_subscribed"] = False
    context.user_data['counter'] = 0
    # tem = False
    
    if chat_member['status'] == "left" :
        check_subscription(update,context, u)
        return consts.SELECTING_ACTION
    else:
        if created:
            if context.user_data.get(consts.FROM_CHAT):
                text = "Botga xush kelibsiz, iltimos ismingizni kiriting!"
                update.message.reply_text(text=text,
                                  reply_markup=make_keyboard_for_start_command())
                return consts.NAME
                
            elif u.name == "IsmiGul":
                text = "Iltimos ismingizni kiriting, agar ismingizni kiritmasangiz bot sizni \"IsmiGul\" deb saqlab qo'yadi"
                update.message.reply_text(text=text,
                                  reply_markup=make_keyboard_for_start_command())
                return consts.NAME
            elif u.region is None:
                text = "Ilitmos viloyatingizni kiriting"
                update.message.reply_text(text=text,
                                  reply_markup=make_keyboard_for_regions())
                return consts.REGION
        else:
            if u.name == "IsmiGul":
                text = "Siz botda IsmiGul bo'lib qolib ketibsiz , iltimos asl ismingizni kiriting yoki shundayligicha davom ettirish uchun quyidagilardan birini tanlang⬇️"
                update.message.reply_text(text=text,
                                  reply_markup=make_keyboard_for_start_command())
                return consts.NAME
            else:
                if u.region is None:
                    text = "Ilitmos viloyatingizni kiriting"
                    update.message.reply_text(text=text,
                                  reply_markup=make_keyboard_for_regions())
                    return consts.REGION
                text = f"{u.name} sizni botda qayta ko'rganimizdan xursandmiz, quyidagilardan birini tanlang⬇️"
                update.message.reply_text(text=text,
                                  reply_markup=make_keyboard_for_start_command())
                return consts.SELECTING_ACTION

        

    


def registration(update: Update, context: CallbackContext):
    user, created = User.get_user_and_created(update, context)

    chat_member = context.bot.get_chat_member(
        consts.CHANNEL_USERNAME, user.user_id)

    if chat_member['status'] == "left":
        check_subscription(update,context, user)
    else:
        
        user.name = update.message.text
        user.save()

        update.message.reply_text(
            text=f"{user.name} botimizga xush kelibsiz. Iltimos qaysi viloyatdan ekanligingizni quyida belgilang", reply_markup=make_keyboard_for_regions())

    return consts.REGION

def region(update: Update, context: CallbackContext):
    u, created = User.get_user_and_created(update, context)

    chat_member = context.bot.get_chat_member(
        consts.CHANNEL_USERNAME, u.user_id)

    if chat_member['status'] == "left":
        check_subscription(update,context, u)
    else:
        user = User.objects.prefetch_related('user_exams','as_owner','as_opponent','user_challenges','winners_challenge','challenge_answers','rates').get(user_id=update.message.from_user.id)
        user.region = update.message.text
        user.save()

        update.message.reply_text(
            text=f"{user.name} quyidagilardan birini tanlang⬇️", reply_markup=make_keyboard_for_start_command())

    return consts.SELECTING_ACTION




def checking_subscription(update: Update, context: CallbackContext):
    u, _ = User.get_user_and_created(update, context)
    chat_member = context.bot.get_chat_member(
        consts.CHANNEL_USERNAME, u.user_id)

    if chat_member['status'] == "left":
        context.user_data['not_subscribed'] = True
        
        check_subscription(update,context, u)
    else:
        user_message = update.callback_query.edit_message_text("Bosh sahifaga o'tish uchun \"Bosh sahifa\" tugmasini bosing", reply_markup=InlineKeyboardMarkup([
                                                               [InlineKeyboardButton("Bosh Sahifa", callback_data=f"home-page-{u.user_id}")]]))
        context.user_data["message_id"] = user_message.message_id

    return consts.SELECTING_ACTION


def home_page(update: Update, context: CallbackContext):
    data = update.callback_query.data.split("-")
    user_id = int(data[2])
    
    user = User.objects.prefetch_related('user_exams','as_owner','as_opponent','user_challenges','winners_challenge','challenge_answers','rates').get(user_id = user_id)
    
    if len(data)==4 and data[3] == "challenge":
       pass
    else:
        update.callback_query.message.delete()
   
    
    if user.name == "IsmiGul":
        text = "Siz botda IsmiGul bo'lib qolib ketibsiz , iltimos asl ismingizni kiriting yoki shundayligicha davom ettirish uchun quyidagilardan birini tanlang⬇️"
    else:
        text = "Quyidagilardan birini tanlang⬇️"
    
    context.bot.send_message(chat_id=user_id, text=text,
                             reply_markup=make_keyboard_for_start_command())
        

    return consts.SELECTING_ACTION

def back_to_home_page(update: Update, context: CallbackContext):
    update.message.reply_text(text="Quyidagilardan birini tanlang⬇️",
                                  reply_markup=make_keyboard_for_start_command())
    return consts.SELECTING_ACTION

def contactus(update: Update, context: CallbackContext):
    update.message.reply_text("Iltimos, bog'lanish uchun @alamiy_bot ga o'ting", reply_markup=ReplyKeyboardMarkup([[consts.BACK]], resize_keyboard=True))
    return consts.CONTACTING

def bot_settings(update: Update, context: CallbackContext):
    user, _ = User.get_user_and_created(update, context)
    
    update.message.reply_text(f"⚠️Sozlamalar bo'limiga xush kelibsiz!!!\n\n<b>Botdagi ismingiz</b> - <b>{user.name}</b>\n\n1️⃣Ismingizni o'zgartirish uchun <b>\"Ism o'zgartirish\"</b> tugmasini bosing\n2️⃣Botda siz duch kelgan nosozliklarni to'g'rilash uchun - <b>\"Sozlash🔧\"</b> tugmasini bosing", reply_markup=ReplyKeyboardMarkup([[consts.CHANGE_NAME, consts.CORRECTING],[consts.BACK]], resize_keyboard=True), parse_mode = ParseMode.HTML)
    return consts.SETTINGS

def change_name(update: Update, context: CallbackContext):
    update.message.reply_text("Iltimos ismingizni kiriting")
    return consts.SETTINGS

def set_name(update: Update, context: CallbackContext):
    user, _ = User.get_user_and_created(update, context)
    user.name = update.message.text
    user.save()
    
    update.message.reply_text(f"Ismingiz {user.name} ga muvafaqqiyatli o'zgartirildi", reply_markup=make_keyboard_for_start_command())
    return consts.SELECTING_ACTION

def correct_settings(update: Update, context: CallbackContext):
    user, _ = User.get_user_and_created(update, context)
    user.is_busy = False
    user.is_ended_challenge_waites = False
    user.is_random_opponent_waites = False
    user.save()
    
    user_exams = UserExam.objects.prefetch_related(
        'questions',"answer").filter(user=user)
    for user_exam in user_exams:
        user_exam.is_finished = False
        user_exam.save()
        
    user_challenges = UserChallenge.objects.prefetch_related('questions',"answer").prefetch_related(
        'users').select_related('user').select_related('opponent').select_related('challenge').filter(users=user)
    for user_challenge in user_challenges:
        user_challenge.is_active = False
        user_challenge.is_random_opponent = False
        user_challenge.is_waited_challenge = False
        user_challenge.in_proccecc = False
        user_challenge.save()
        
    update.message.reply_text("Bot xatoliklardan tozalandi. Botda foydalanishni davom ettirish uchun quyidagilardan birini tanlang🔽", reply_markup=make_keyboard_for_start_command())
    
    return consts.SELECTING_ACTION
        
def hide(update: Update, context: CallbackContext):
    update.callback_query.message.delete()

def send_message(update: Update, context: CallbackContext):
    user, _ = User.get_user_and_created(update, context)
    if user.user_id == "1755197237":
        users = User.objects.prefetch_related('user_exams','as_owner','as_opponent','user_challenges','winners_challenge','challenge_answers','rates').all()
        for user in users:
            message = context.bot.send_message(chat_id=user.user_id, text="Assalamu alaykum! Botda o'zgarishlar qilindi. Bot to'g'ri ishlashi uchun iltimos quyidagi ketma-ketlikka rioya qiling:\n\n1️⃣Botga /start buyrug'ini yozish orqali botni qaytadan ishga tushiring!\n\n2️⃣Botdagi \"Sozlamalar⚙️\" tugmachasini bosing, chiqqan tugmachalar ichidan esa \"Sozlash🔧\" tugmasini bosing!\n\n3️⃣Yuqoridagi amallarni qilganingizdan so'ng botdan foydalanishni davom ettirishingiz mumkin.\n\n⚠️Bot sozlanganidan keyin ham vujudga kelgan har qanday muammoni, ayni vujudga kelish vaqtida skrinshot qilib @ulugbek2311 ga murojaat qilishingizni iltimos qilib qolar edik. Botni soz ishlashi uchun bu juda muhim! E'tiboringiz uchun rahmat. Kuningiz xayrli va barokatli o'tsin.")
        update.message.reply_text("success")

