
from tgbot import consts
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode


def check_subscription(update, context, u):
    if context.user_data["not_subscribed"]:
        update.callback_query.message.delete()
        user_message = context.bot.send_message(chat_id = u.user_id,text=f"Iltimos avval \"A'lamiy\" telegram kanaliga a'zo bo'ling, so'ng  \"{consts.JOINED}\" tugmasini bosing. Kanalga o'tish uchun \"Kanalga o'tish\" tugmasini bosing.", reply_markup=InlineKeyboardMarkup([
                                                               [InlineKeyboardButton(consts.JOINED, callback_data=f"checking-subscription-")], [InlineKeyboardButton("Kanalga o'tish", url = "https://t.me/alamiy_uz")]]))
        context.user_data["message_id"] = user_message.message_id

    else:
        user_message = context.bot.send_message(chat_id=u.user_id, text=f"Hurmatli foydalanuvchi botdan foydalanish uchun \"A'lamiy\" telegram kanaliga a'zo bo'lishingizni so'raymiz. A'zo bo'lganingizdan so'ng \"{consts.JOINED}\" tugmasini bosing. Kanalga o'tish uchun \"Kanalga o'tish\" tugmasini bosing", reply_markup=InlineKeyboardMarkup([
                                                [InlineKeyboardButton(consts.JOINED, callback_data=f"checking-subscription-")], [InlineKeyboardButton("Kanalga o'tish", url = "https://t.me/alamiy_uz")]]), parse_mode =  ParseMode.HTML)
        context.user_data["message_id"] = user_message.message_id
