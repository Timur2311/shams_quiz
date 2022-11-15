

from telegram import ParseMode, Update, ReplyKeyboardRemove, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from group_challenge.models import UserChallenge, UserChallengeAnswer
from tgbot import consts

from tgbot.handlers.exam import static_text
from users.models import User
from exam.models import Exam, QuestionOption, UserExam, UserExamAnswer

from tgbot.handlers.exam import keyboards
from tgbot.handlers.exam import helpers

from utils.check_subscription import check_subscription

from tgbot.handlers.onboarding.keyboards import make_keyboard_for_start_command


def exam_start(update: Update, context: CallbackContext) -> None:
    """
    TODO:
    - Pagination
    """
    exams = Exam.objects.prefetch_related('questions').all()
    inline_keyboard = keyboards.exam_keyboard(exams)

    if update.callback_query:
        update.callback_query.message.edit_text(
            text=static_text.exam_start, reply_markup=inline_keyboard,
            parse_mode=ParseMode.HTML
        )
    else:
        update.message.reply_text(
            text=static_text.exam_start, reply_markup=inline_keyboard)


def passing_test(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Quyidagi bosqichlardan birini tanlang", reply_markup=ReplyKeyboardMarkup([
        [consts.FIRST, consts.SECOND], [consts.THIRD,
                                        consts.FOURTH], [consts.FIFTH, consts.BACK]
    ], resize_keyboard=True))

    return consts.PASS_TEST


def stage_exams(update: Update, context: CallbackContext) -> None:
    u, _ = User.get_user_and_created(update, context)

    chat_member = context.bot.get_chat_member(
        consts.CHANNEL_USERNAME, u.user_id)
    if chat_member['status'] == "left":
        check_subscription(update, context, u)
    else:
        if update.callback_query:
            data = update.callback_query.data.split("-")
            stage = int(data[3])
        else:
            stage = update.message.text[0]

        exams = Exam.objects.prefetch_related('questions').filter(stage=stage)
        buttons = []
        for exam in exams:
            buttons.append([InlineKeyboardButton(
                f"{exam.tour}-tur savollari", callback_data=f"passing-test-{exam.id}-{u.user_id}")])
        buttons.append([InlineKeyboardButton(
            consts.BACK, callback_data=f"back-to-exam-stages-{u.user_id}")])
        if update.callback_query:
            update.callback_query.delete_message()
        exam_message = context.bot.send_message(
            chat_id=u.user_id, text="Quyidagi testlardan birini tanlang⬇️", reply_markup=InlineKeyboardMarkup(buttons))
        context.user_data["message_id"] = exam_message.message_id

    return consts.PASS_TEST


def back_to_exam_stage(update: Update, context: CallbackContext):

    data = update.callback_query.data.split("-")
    user_id = int(data[4])

    update.callback_query.message.delete()

    context.bot.send_message(chat_id=user_id, text="Quyidagilardan birini tanlang⬇️", reply_markup=ReplyKeyboardMarkup([
        [consts.FIRST, consts.SECOND], [consts.THIRD,
                                        consts.FOURTH], [consts.FIFTH, consts.BACK]
    ], resize_keyboard=True))


def exam_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = update.callback_query.data.split("-")
    exam_id = int(data[2])
    user_id = int(data[2])

    query.answer()
    exam = Exam.objects.prefetch_related('questions').get(id=exam_id)
    text = f"<b>{exam.title}</b> \n\n<b>Testni boshlaymizmi?</b>"
    context.bot.edit_message_text(
        text=text,
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboards.test_start_confirmation(exam, user_id))

    return consts.PASS_TEST


def exam_confirmation(update: Update, context: CallbackContext) -> None:
    user, _ = User.get_user_and_created(update, context)

    query = update.callback_query
    data = update.callback_query.data.split("-")
    exam_id = int(data[2])
    action_type = data[3]

    query.answer()
    if action_type == "start":

        if len(data) == 5:
            again = data[4]
        else:
            again = None
        exam = Exam.objects.prefetch_related('questions').get(id=exam_id)
        user_exam, counter = exam.create_user_exam(user, again)

        context.user_data["number_of_test"] = 1
        context.user_data["questions_count"] = counter

        if counter > 0:
            user_exam.create_answers()
            question = user_exam.last_unanswered_question()
            query.delete_message()

            # user is starting pass test
            user.is_busy = True
            user.save()

            query.message.reply_text(
                f"<b>Test boshlandi!</b>\n\n <b>Testlar soni:</b> {counter} ta", reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)

            helpers.send_test(update=update, context=context,
                              question=question, user_exam=user_exam, user=user)

        elif counter == 0:
            query.delete_message()
            user_message = context.bot.send_message(chat_id=user.user_id, text="Ushbu testdagi hamma savollarga to'g'ri javob bergansiz🤩 Bilimingizni mustahkamlash uchun testlarni qaytadan ishlashni xohlasangiz \"Qayta ishlash\" tugmasini bosing.", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Qayta ishlash", callback_data=f"test-confirmation-{exam.id}-start-again")], [InlineKeyboardButton("Testlarga qaytish📚", callback_data=f"stage-exams-{user.user_id}-{exam.stage}")], [InlineKeyboardButton("Bosh Sahifa", callback_data=f"home-page-{user.user_id}")], [InlineKeyboardButton("Bosqich tanlashga qaytish", callback_data=f"back-to-exam-stages-{user.user_id}")]]))
            context.user_data["message_id"] = user_message.message_id

    elif action_type == "back":
        exam_start(update, context)

    return consts.PASS_TEST


def exam_handler(update: Update, context: CallbackContext):
    data = update.callback_query.data.split("-")
    question_id = int(data[2])
    question_option_id = int(data[3])
    user_exam_id = int(data[4])

    user, _ = User.get_user_and_created(update, context)
    question_option = QuestionOption.objects.select_related(
        'question').get(id=question_option_id)
    user_exam_answer = UserExamAnswer.objects.select_related('user_exam').select_related('question').get(
        user_exam__id=user_exam_id, question__id=question_id)
    user_exam = UserExam.objects.prefetch_related(
        'questions').get(id=user_exam_id)

    user_exam_answer.is_correct = question_option.is_correct
    user_exam_answer.option_id = question_option.id
    user_exam_answer.answered = True
    user_exam_answer.save()

    question = user_exam.last_unanswered_question()
    if question:
        helpers.send_test(update=update, context=context,
                          question=question, user_exam=user_exam, user=user)

    else:
        score = user_exam.update_score()
        user_exam.is_finished = True
        user_exam.save()
        update.callback_query.delete_message()

        context.bot.send_message(
            user.user_id, f"<b>Imtihon tugadi🏁</b>\n\n<b>To'g'ri javoblar soni✅:</b> {score} ta\n\nNoto'g'ri berilgan javoblaringizning izohlarini ko'rish uchun \"Izoh💬\" tugmasini bosing yoki \"Testlarga qaytish📚\" tugmasi orqali bilimingizni oshirishda davom eting!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Testlarga qaytish📚", callback_data=f"stage-exams-{user.user_id}-{user_exam.exam.stage}")], [InlineKeyboardButton("Izoh💬", callback_data=f"comments-exam-{user_exam.id}-{user_exam.user.user_id}")]]), parse_mode=ParseMode.HTML)

        user.is_busy = False
        user.save()
        
        if user.is_ended_challenge_waites:
            ended_challenges = UserChallenge.objects.prefetch_related('questions').prefetch_related('users').select_related(
                'user').select_related('opponent').select_related('challenge').filter(users=user, is_active=False).filter(is_waited_challenge=True)
            for ended_challenge in ended_challenges:
                opponent = ended_challenge.user
                if ended_challenge.user.user_id == user.user_id:
                    opponent = ended_challenge.opponent

                text = f"Avvalroq {ended_challenge.challenge.stage}-bosqich bo'yicha <a href='tg://user?id={opponent.user_id}'>{opponent.name}</a> bilan bellashuvingiz natijasi:\n\n"
                if ended_challenge.winner.user_id == user.user_id:
                    text += f"\n<a href='tg://user?id={user.user_id}'>{user.name}</a>:👑{ended_challenge.user_score}/10  ⏳{ended_challenge.user_timer}\n<a href='tg://user?id={opponent.user_id}'>{opponent.name}</a>:😭{ended_challenge.opponent_score}/10  ⏳{ended_challenge.opponent_timer}"
                else:
                    text += f"\n<a href='tg://user?id={opponent.user_id}'>{opponent.name}</a>:👑{ended_challenge.opponent_score}/10  ⏳{ended_challenge.opponent_timer}\n<a href='tg://user?id={user.user_id}'>{user.name}</a>:😭{ended_challenge.user_score}/10  ⏳{ended_challenge.user_timer}"

                text += "\n⚠️Raqib bilan qayta bellashish uchun \"Qayta bellashish\" tugmasini bosing\nBellashuvdagi yo'l qo'ygan xatolaringizni bilish uchun esa \"Noto'g'ri javoblar\" tugmasini bosing.\n Ushbu xabarni o'chirish uchun \"Yashirish\" tugmasini bosing."

                context.bot.send_message(chat_id=user.user_id, text=text, reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Qayta bellashish", callback_data=f"revansh-{ended_challenge.id}-{user.user_id}-{opponent.user_id}")], [InlineKeyboardButton("Noto'g'ri javoblar", callback_data=f"comments-challenge-{ended_challenge.id}-{user.user_id}")], [InlineKeyboardButton("Yashirish", callback_data=f"hide-{user.user_id}")]]), parse_mode=ParseMode.HTML)
                ended_challenge.is_waited_challenge = False
                ended_challenge.save()
                user.is_ended_challenge_waites = False
                user.save()
            return consts.COMMENTS
        if user.is_random_opponent_waites:
            user_challenge = UserChallenge.objects.prefetch_related('questions').prefetch_related('users').select_related(
                'user').select_related('opponent').select_related('challenge').get(
                id=int(user.challenge_id))
            context.bot.send_message(user.user_id, f"Sizga {user_challenge.challenge.stage}-bosqich savollari bo'yicha tasodifiy raqib topildi. Bellashish uchun \"Boshlash\" tugmasini bosing. ", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Boshlash", callback_data=f"confirmation-random-{user_challenge.id}-start-user-{user.user_id}")]]), parse_mode=ParseMode.HTML)
    return consts.PASS_TEST


def comments(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split("-")
    type = data[1]
    if type == "exam":
        user_exam_id = int(data[2])

        user_id = int(data[3])

        user_exam = UserExam.objects.prefetch_related(
            'questions').get(id=user_exam_id)

        user_exam_answers = UserExamAnswer.objects.select_related('user_exam').select_related('question').filter(
            user_exam__id=user_exam_id).filter(is_correct=False)

        buttons = []

        for user_exam_answer in user_exam_answers:
            buttons.append([InlineKeyboardButton(
                f"{user_exam_answer.number}-savol", callback_data=f"answer-{user_exam_answer.id}-{user_id}-{user_exam_id}")])

        buttons.append([InlineKeyboardButton("Testlarga qaytish📚",
                                             callback_data=f"stage-exams-{user_id}-{user_exam.exam.stage}")])

        query.edit_message_text("Noto'g'ri javob berilgan savollar ro'yxati: ",
                                reply_markup=InlineKeyboardMarkup(buttons))
    elif type == "challenge":
        # here
        user_challenge_id = int(data[2])

        user_id = int(data[3])

        user_challenge_answers = UserChallengeAnswer.objects.select_related('user_challenge', 'user', 'question').filter(
            user_challenge__id=user_challenge_id).filter(user_challenge__id=user_challenge_id, user__user_id=user_id, is_correct=False)

        buttons = []

        for user_challenge_answer in user_challenge_answers:
            buttons.append([InlineKeyboardButton(
                f"{user_challenge_answer.number}-savol", callback_data=f"incorrects-{user_challenge_answer.id}-{user_id}-{user_challenge_id}")])

        buttons.append([InlineKeyboardButton(
            "Bosh Sahifa", callback_data=f"home-page-{user_id}")])

        query.edit_message_text("Noto'g'ri javob berilgan savollar ro'yxati: ",
                                reply_markup=InlineKeyboardMarkup(buttons))

    return consts.COMMENTS


def challenge_answer(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split("-")
    user_challenge_answer_id = int(data[1])
    user_id = int(data[2])
    user_challenge_id = int(data[3])
    user_challenge = UserChallenge.objects.prefetch_related('questions').prefetch_related(
        'users').select_related('user').select_related('opponent').select_related('challenge').get(id=user_challenge_id)

    user_challenge_answer = UserChallengeAnswer.objects.select_related(
        'user_challenge', 'user', 'question').get(id=user_challenge_answer_id)
    question_option = QuestionOption.objects.select_related(
        'question').get(id=user_challenge_answer.option_id)
    question = user_challenge_answer.question

    query.edit_message_text(f"<b>Savol:</b> {question.content} \n\n<b>Siz bergan javob❌:</b> {question_option.content}  ", reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton(consts.BACK, callback_data=f"comments-challenge-{user_challenge_id}-{user_challenge.user.user_id}")]]), parse_mode=ParseMode.HTML)

    return consts.COMMENTS


def answer(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split("-")
    user_exam_answer_id = int(data[1])
    user_id = int(data[2])
    user_exam_id = int(data[3])
    user_exam = UserExam.objects.prefetch_related(
        'questions').get(id=user_exam_id)

    user_exam_answer = UserExamAnswer.objects.select_related(
        'user_exam').select_related('question').get(id=user_exam_answer_id)
    question_option = QuestionOption.objects.select_related(
        'question').get(id=user_exam_answer.option_id)
    question = user_exam_answer.question
    true_answer = QuestionOption.objects.select_related(
        'question').filter(question=question).get(is_correct=True)

    query.edit_message_text(f"<b>Savol:</b> {question.content} \n\n<b>Siz bergan javob❌:</b> {question_option.content} \n\n <b>To'g'ri javob✅:</b> {true_answer.content} \n\n <b>Izoh💬: </b>{question.true_definition} ", reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton(consts.BACK, callback_data=f"comments-exam-{user_exam_id}-{user_exam.user.user_id}")], [InlineKeyboardButton("Testlarga qaytish📚", callback_data=f"stage-exams-{user_id}-{user_exam.exam.stage}")]]), parse_mode=ParseMode.HTML)

    return consts.COMMENTS
