"""
    Telegram event handlers
"""
import sys
import logging
from typing import Dict

import telegram.error
from telegram import Bot, Update, BotCommand
from telegram.ext import (
    Updater, Dispatcher, Filters,
    CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, InlineQueryHandler
)

from dtb.celery import app  # event processing in async mode
from dtb.settings import TELEGRAM_TOKEN, DEBUG

from tgbot.handlers.utils import error
from tgbot.handlers.onboarding import handlers as onboarding_handlers
from tgbot.handlers.exam import handlers as exam_handler
from tgbot.handlers.challenge import handlers as challenge_handlers

from tgbot import consts
from tgbot.handlers.onboarding import static_text as static_texts


def setup_dispatcher(dp):
    """
    Adding handlers for events from Telegram
    """

    # inline_mode
    dp.add_handler(InlineQueryHandler(challenge_handlers.inlinequery))
    dp.add_handler(CallbackQueryHandler(
        challenge_handlers.challenge_callback, pattern=r"received-"))
    dp.add_handler(CallbackQueryHandler(
        challenge_handlers.user_check, pattern=r"check-"))

    # handling errors
    dp.add_error_handler(error.send_stacktrace_to_tg_chat)

    selection_handlers = [
        MessageHandler(Filters.text(static_texts.TEEST),
                       exam_handler.passing_test),
        MessageHandler(Filters.text(static_texts.CHALLENGE),
                       challenge_handlers.challenges_list),
        MessageHandler(Filters.text(static_texts.LEADER),
                       challenge_handlers.leader),
        MessageHandler(Filters.text(static_texts.CONTACTUS),
                       onboarding_handlers.contactus),
        MessageHandler(Filters.text(consts.SET_SETTINGS) & ~Filters.command,
                                           onboarding_handlers.bot_settings),
        CallbackQueryHandler(
            onboarding_handlers.checking_subscription, pattern=r"checking-subscription-"),
        CallbackQueryHandler(
            onboarding_handlers.home_page, pattern=r"home-page"),
        CallbackQueryHandler(
            challenge_handlers.revansh, pattern=r"revansh-"),
        CallbackQueryHandler(
            challenge_handlers.challenge_confirmation, pattern=r"confirmation-"),
        CommandHandler(
            'start', onboarding_handlers.command_start),




    ]

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                'start', onboarding_handlers.command_start),
            CallbackQueryHandler(
                challenge_handlers.revansh, pattern=r"revansh-"),
            CallbackQueryHandler(
                onboarding_handlers.home_page, pattern=r"home-page"),
            CallbackQueryHandler(
                challenge_handlers.challenge_confirmation, pattern=r"confirmation-"),
            CallbackQueryHandler(
                exam_handler.answer, pattern=r"answer-"),
            CallbackQueryHandler(
                exam_handler.stage_exams, pattern=r"stage-exams-"),

        ],

        states={
            consts.SELECTING_ACTION: selection_handlers,
            consts.PASS_TEST: [
                MessageHandler(Filters.regex(
                    "[-bosqich]+$"), exam_handler.stage_exams),
                CallbackQueryHandler(
                    exam_handler.exam_callback, pattern=r"passing-test-"),
                CallbackQueryHandler(
                    exam_handler.exam_confirmation, pattern=r"test-confirmation-"),
                CallbackQueryHandler(
                    exam_handler.exam_handler, pattern=r"question-variant-"),
                CallbackQueryHandler(
                    onboarding_handlers.checking_subscription, pattern=r"checking-subscription-"),

                CallbackQueryHandler(
                    exam_handler.back_to_exam_stage, pattern=r"back-to-exam-stages-"),
                CallbackQueryHandler(
                    exam_handler.stage_exams, pattern=r"stage-exams-"),
                CallbackQueryHandler(
                    onboarding_handlers.home_page, pattern=r"home-page"),
                MessageHandler(Filters.text(consts.BACK),
                               onboarding_handlers.back_to_home_page),
                CallbackQueryHandler(
                    exam_handler.comments, pattern=r"comments-"),

                CallbackQueryHandler(
                    challenge_handlers.challenge_confirmation, pattern=r"confirmation-"),

                CallbackQueryHandler(
                    challenge_handlers.challenge_callback, pattern=r"received-"),
                CommandHandler(
                    'start', onboarding_handlers.command_start),

            ],
            consts.SHARING_CHALLENGE: [
                MessageHandler(Filters.regex(
                    "[-bosqich]+$"), challenge_handlers.stage_exams),
                CallbackQueryHandler(
                    challenge_handlers.revoke_challenge, pattern=r"revoke-challenge-"),
                CallbackQueryHandler(
                    challenge_handlers.random_opponent, pattern="^"+consts.RANDOM_OPPONENT),
                CallbackQueryHandler(
                    challenge_handlers.challenge_callback, pattern=r"received-"),
                CallbackQueryHandler(
                    challenge_handlers.challenge_confirmation, pattern=r"confirmation-"),
                CallbackQueryHandler(
                    challenge_handlers.challenge_handler, pattern=r"question-variant-"),
                MessageHandler(Filters.text(consts.BACK),
                               onboarding_handlers.back_to_home_page),
                MessageHandler(Filters.text(consts.HOME_PAGE),
                               onboarding_handlers.back_to_home_page),
                CallbackQueryHandler(
                    challenge_handlers.revansh, pattern=r"revansh-"),

                CallbackQueryHandler(
                    onboarding_handlers.checking_subscription, pattern=r"checking-subscription-"),
                CallbackQueryHandler(
                    onboarding_handlers.home_page, pattern=r"home-page"),
                CommandHandler(
                    'start', onboarding_handlers.command_start),

            ],
            consts.LEADERBOARD: [MessageHandler(Filters.text(consts.BACK),
                                                onboarding_handlers.back_to_home_page),
                                 CommandHandler(
                'start', onboarding_handlers.command_start), ],
            consts.CONTACTING: [MessageHandler(Filters.text(consts.BACK),
                                               onboarding_handlers.back_to_home_page),
                                CommandHandler(
                'start', onboarding_handlers.command_start), ],
            consts.NAME: [MessageHandler(Filters.text & ~Filters.command,
                                         onboarding_handlers.registration),
                          CommandHandler(
                'start', onboarding_handlers.command_start), ],
            consts.REGION: [MessageHandler(Filters.text & ~Filters.command,
                                           onboarding_handlers.region),
                            CommandHandler(
                'start', onboarding_handlers.command_start), ],
            consts.COMMENTS: [
                CallbackQueryHandler(
                exam_handler.comments, pattern=r"comments-"),
                CallbackQueryHandler(
                exam_handler.answer, pattern=r"answer-"),
                CallbackQueryHandler(
                exam_handler.challenge_answer, pattern=r"incorrects-"),
                CallbackQueryHandler(
                exam_handler.stage_exams, pattern=r"stage-exams-"),
                CommandHandler(
                'start', onboarding_handlers.command_start),
                CallbackQueryHandler(
                    challenge_handlers.revansh, pattern=r"revansh-"),
                CommandHandler(
                'start', onboarding_handlers.command_start),
                CallbackQueryHandler(
                    onboarding_handlers.home_page, pattern=r"home-page"),
                
            ],
            consts.SETTINGS:[
                MessageHandler(Filters.text(consts.SET_SETTINGS) & ~Filters.command,
                                           onboarding_handlers.bot_settings),
                MessageHandler(Filters.text(consts.CHANGE_NAME) & ~Filters.command,
                                           onboarding_handlers.change_name),
                MessageHandler(Filters.text(consts.CORRECTING) & ~Filters.command,
                                           onboarding_handlers.correct_settings),
                MessageHandler(Filters.text(consts.BACK),
                               onboarding_handlers.back_to_home_page),
                
                
                
                
                
                
                CommandHandler(
                'start', onboarding_handlers.command_start),
                
                MessageHandler(Filters.text & ~Filters.command,
                                         onboarding_handlers.set_name),
            ]
        },
        fallbacks=[
            CommandHandler(
                'start', onboarding_handlers.command_start),
            selection_handlers
        ],
    )

    dp.add_handler(conv_handler)

    return dp


def run_pooling():
    """ Run bot in pooling mode """
    updater = Updater(TELEGRAM_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp = setup_dispatcher(dp)

    bot_info = Bot(TELEGRAM_TOKEN).get_me()
    bot_link = f"https://t.me/" + bot_info["username"]

    print(f"Pooling of '{bot_link}' started")
    # it is really useful to send '👋' emoji to developer
    # when you run local test
    # bot.send_message(text='👋', chat_id=<YOUR TELEGRAM ID>)

    updater.start_polling()
    updater.idle()


# Global variable - best way I found to init Telegram bot
bot = Bot(TELEGRAM_TOKEN)
try:
    TELEGRAM_BOT_USERNAME = bot.get_me()["username"]
except telegram.error.Unauthorized:
    logging.error(f"Invalid TELEGRAM_TOKEN.")
    sys.exit(1)


@app.task(ignore_result=True)
def process_telegram_event(update_json):
    update = Update.de_json(update_json, bot)
    dispatcher.process_update(update)


def set_up_commands(bot_instance: Bot) -> None:
    langs_with_commands: Dict[str, Dict[str, str]] = {
        'en': {
            'start': 'Botni ishga tushirish'
        },
        'ru': {
            'start': 'Запустить django бота 🚀',

        }
    }

    bot_instance.delete_my_commands()
    for language_code in langs_with_commands:
        bot_instance.set_my_commands(
            language_code=language_code,
            commands=[
                BotCommand(command, description) for command, description in langs_with_commands[language_code].items()
            ]
        )


# WARNING: it's better to comment the line below in DEBUG mode.
# Likely, you'll get a flood limit control error, when restarting bot too often
set_up_commands(bot)

n_workers = 0 if DEBUG else 4
dispatcher = setup_dispatcher(Dispatcher(
    bot, update_queue=None, workers=n_workers, use_context=True))
