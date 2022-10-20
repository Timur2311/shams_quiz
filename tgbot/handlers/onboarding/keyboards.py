from telegram import ReplyKeyboardMarkup
from tgbot.handlers.onboarding.static_text import TEEST, CHALLENGE, LEADER, CONTACTUS


def make_keyboard_for_start_command() -> ReplyKeyboardMarkup:
    buttons = [
        [TEEST,CHALLENGE],
        [LEADER, CONTACTUS]
    ]

    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def make_keyboard_for_regions() -> ReplyKeyboardMarkup:
    buttons = [
        ["Andijon", "Farg'ona","Namangan"],
        ["Toshkent ", "Sirdaryo", "Jizzax"],
        ["Qashqadaryo", "Surxondaryo", "Samarqand"],
        ["Buxoro", "Navoiy", "Xorazm"],
        ["Qoraqalpog'iston Respublikasi", "Toshkent shahri"]
        
    ]
    
    

    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
