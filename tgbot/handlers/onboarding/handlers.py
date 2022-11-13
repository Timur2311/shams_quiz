

from telegram import ParseMode, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import CallbackContext


from users.models import User
from tgbot.handlers.onboarding.keyboards import make_keyboard_for_start_command, make_keyboard_for_regions
from tgbot import consts


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
        user = User.objects.get(user_id=update.message.from_user.id)
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
    user_id = data[2]
    user, _ = User.get_user_and_created(update, context)
    
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