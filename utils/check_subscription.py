import imp
from tgbot import consts
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def check_subscription(update,context,u):
    if context.user_data["not_subscribed"]:
        context.user_data['counter']+=1
        user_message = update.callback_query.edit_message_text(text = f"{context.user_data['counter']} - urinishingiz bekor ketdi. Iltimos avval {consts.CHANNEL_USERNAME} telegram kanaliga a'zo bo'ling, so'ng  \"Tekshirish\" tugmasini bosing.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Tekshirish", callback_data=f"checking-subscription-")]]))
        context.user_data["message_id"] = user_message.message_id
        
    else:        
        user_message = context.bot.send_message(chat_id = u.user_id, text = f"Hurmatli foydalanuvchi botdan foydalanish uchun {consts.CHANNEL_USERNAME} telegram kanaliga a'zo bo'lishingizni so'raymiz. A'zo bo'lganingizdan so'ng \"Tekshirish\" tugmasini bosing.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Tekshirish", callback_data=f"checking-subscription-")]]))
        context.user_data["message_id"] = user_message.message_id
    
    
    
    
    