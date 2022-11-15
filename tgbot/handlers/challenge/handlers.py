
from uuid import uuid4
from datetime import datetime
from telegram import ParseMode, Update, ReplyKeyboardRemove, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent, ParseMode
from telegram.ext import CallbackContext, ConversationHandler
from group_challenge.models import Challenge, UserChallenge, UserChallengeAnswer

from users.models import User
from exam.models import QuestionOption


from tgbot.handlers.exam import helpers

from tgbot import consts
from utils.check_subscription import check_subscription


def challenges_list(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Quyidagi bosqichlardan birini tanlang🔽", reply_markup=ReplyKeyboardMarkup([
        [consts.FIRST, consts.SECOND], [consts.THIRD,
                                        consts.FOURTH], [consts.FIFTH, consts.BACK]
    ], resize_keyboard=True))

    return consts.SHARING_CHALLENGE


def stage_exams(update: Update, context: CallbackContext):
    u = User.objects.get(user_id=update.message.from_user.id)

    chat_member = context.bot.get_chat_member(
        consts.CHANNEL_USERNAME, update.message.from_user.id)
    if chat_member['status'] == "left":
        check_subscription(update, context, u)
    else:
        stage = update.message.text[0]
        challenge = Challenge.objects.prefetch_related(
            'questions').get(stage=stage)

        user_challenge = challenge.create_user_challenge(u.user_id, challenge)

        challenge_stage = update.message.reply_text(f"Siz {stage}-bosqich savollaridan tashkil topgan bellashuvni yaratdingiz.\n\nQuyida keltirilgan usullardan birini tanlang, bunda:\n\n{consts.RANDOM_OPPONENT} - Tizimda siz tanlagan savollar bilan bellashuvni istagan qatnashchilardan tasodifiy biri tanlanib bellashuv tashkil etiladi.\n\n{consts.SHARE}  - Bu tugmani bosqanda sizdan o'z do'stingiz chatini tanlash so'raladi, tanlaganingizdan keyin u yerda sizga inline ko'rinishida taklif shakllantiriladi bunda siz uni tanlab do'stingizga yuborishingiz mumkin, agar do'stingiz siz bilan bellashishni xohlasa tugmani bosib sizga buni bildiradi.",
                                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text=consts.SHARE, switch_inline_query=f"{user_challenge.id}")], [InlineKeyboardButton(text=consts.RANDOM_OPPONENT, callback_data=f"{consts.RANDOM_OPPONENT}-{user_challenge.id}-{u.user_id}")], [InlineKeyboardButton(consts.REVOKE, callback_data=f"revoke-challenge-{u.user_id}-{user_challenge.id}")]]), parse_mode=ParseMode.HTML)
        user_challenge.created_challenge_message_id = str(
            challenge_stage.message_id)
        user_challenge.created_challenge_chat_id = str(challenge_stage.chat_id)
        user_challenge.save()

    return consts.SHARING_CHALLENGE


def inlinequery(update: Update, context: CallbackContext) -> None:

    query = update.inline_query.query

    if query == "":
        return

    user_challenge = UserChallenge.objects.prefetch_related('questions').prefetch_related(
        'users').select_related('user').select_related('opponent').select_related('challenge').get(id=int(query))

    text = f"Do'stingiz sizni {user_challenge.challenge.stage}-bosqich savollari bo'yicha bellashuvga taklif qilmoqda. Bellashuvga rozilik bildirganingizdan so'ng botga o'tib, bot orqali bellashuvni boshlashingiz mumkin "
    my_user_challenge = user_challenge

    results = []

    results.append(
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"{my_user_challenge.challenge.stage}-bosqich bellashuvi",
            input_message_content=InputTextMessageContent(
                message_text=text),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text=consts.ACCEPT, callback_data=f"received-challenge-{consts.ACCEPT}-{my_user_challenge.user.user_id}-{my_user_challenge.id}")],
                                               [InlineKeyboardButton(
                                                   text=consts.DECLINE, callback_data=f"received-challenge-{consts.DECLINE}-{my_user_challenge.user.user_id}-{my_user_challenge.id}")]
                                               ])
        )
    )

    update.inline_query.answer(results)


def random_opponent(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split("-")

    user_challenge_id = int(data[1])
    from_user_id = int(data[2])
    created_user_challenge = UserChallenge.objects.prefetch_related('questions').prefetch_related(
        'users').select_related('user').select_related('opponent').select_related('challenge').get(id=user_challenge_id)

    user_random_challenges = UserChallenge.objects.prefetch_related('questions').prefetch_related('users').select_related('user').select_related(
        'opponent').select_related('challenge').filter(user__user_id=from_user_id, challenge__stage=created_user_challenge.challenge.stage, is_active=True, opponent=None).exclude(id=created_user_challenge.id)

    possible_challenges = UserChallenge.objects.prefetch_related('questions').prefetch_related('users').select_related('user').select_related('opponent').select_related('challenge').filter(
        is_active=True).filter(is_random_opponent=True).filter(opponent=None).exclude(user=User.objects.get(user_id=from_user_id)).exclude(in_proccecc=True)

    if possible_challenges.count() == 0:

        created_user_challenge.is_random_opponent = True
        created_user_challenge.save()
        if user_random_challenges.count() == 0:
            my_message = update.callback_query.edit_message_text(f"Hozircha siz uchun raqib yo'q. Raqib topilishi bilan sizga xabar jo'natamiz.\n\n⚠️Raqib topilishini kutishni xohlamasangiz <b>\"{consts.REVOKE}\"</b> tugmasini bosing, aks holda <b>\"Bosh Sahifa\"</b> tugmasi orqali botdan foydalanishda davom etishingiz mumkin.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Bosh Sahifa", callback_data=f"home-page-{from_user_id}")], [InlineKeyboardButton(consts.REVOKE, callback_data=f"revoke-challenge-{from_user_id}-{created_user_challenge.id}-random")]]), parse_mode=ParseMode.HTML)
            context.user_data["message_id"] = my_message.message_id
        elif user_random_challenges.count() == 1:
            created_user_challenge.delete()
            my_message = update.callback_query.edit_message_text(f"{created_user_challenge.challenge.stage} - bosqich savollari bo'yicha sizga raqib qidirilmoqda, biror raqib ushbu bosqich savollari bo'yicha bellashishni istashi bilan sizga xabar beramiz.\n\n ⚠️Agar kutishni xohlamasangiz <b>\"{consts.REVOKE}\"</b> tugmasi orqali bellashuvni bekor qilishingiz mumkin,aks holda <b>\"Bosh Sahifa\"</b> tugmasi orqali botdan foydalanishda davom etishingiz mumkin.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Bosh Sahifa", callback_data=f"home-page-{from_user_id}")], [InlineKeyboardButton(consts.REVOKE, callback_data=f"revoke-challenge-{from_user_id}-{user_random_challenges.first().id}-random")]]), parse_mode=ParseMode.HTML)
            context.user_data["message_id"] = my_message.message_id

    elif possible_challenges.count() >= 1:
        possible_challenge = possible_challenges.first()
        user = User.objects.get(user_id=possible_challenge.user.user_id)
        opponent = User.objects.get(user_id=from_user_id)
        created_user_challenge.delete()
        possible_challenge = possible_challenges.first()
        possible_challenge.opponent = opponent
        possible_challenge.users.add(opponent)
        possible_challenge.save()

        if possible_challenge.user.is_busy:
            possible_challenge.in_proccecc = True
            possible_challenge.save()
            possible_challenge.user.is_random_opponent_waites = True
            possible_challenge.user.challenge_id = str(possible_challenge.id)
            possible_challenge.user.save()

        query.edit_message_text(f"Sizga tasodifiy raqib topildi. Sizga <a href='tg://user?id={user.user_id}'>{user.name}</a> raqiblik qiladi .Bellashuvni boshlash uchun \"Boshlash\" tugmasini bosing ", reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Boshlash", callback_data=f"confirmation-challenge-{possible_challenge.id}-start-opponent-{opponent.user_id}")]]), parse_mode=ParseMode.HTML)

        created_user_message = context.bot.send_message(chat_id=user.user_id, text=f"Sizga tasodifiy raqib topildi. Sizga <a href='tg://user?id={opponent.user_id}'>{opponent.name}</a> raqiblik qiladi .Bellashuvni boshlash uchun \"Boshlash\" tugmasini bosing ",
                                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Boshlash", callback_data=f"confirmation-challenge-{possible_challenge.id}-start-user-{user.user_id}")]]), parse_mode=ParseMode.HTML)

        possible_challenge.user_chat_id = created_user_message.chat_id
        possible_challenge.user_message_id = created_user_message.message_id

        possible_challenge.save()

    return consts.SHARING_CHALLENGE


def challenge_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = update.callback_query.data.split("-")

    type_of_challenge = data[1]

    received_type = data[2]
    challenge_owner_id = int(data[3])

    user_challenge_id = int(data[4])

    user_challenge = UserChallenge.objects.prefetch_related('questions').prefetch_related('users').select_related(
        'user').select_related('opponent').select_related('challenge').get(id=user_challenge_id)

    user, _ = User.get_user_and_created(update, context)

    # user.user_id = str(query.from_user.id)

    if user.name == "IsmiGul":
        context.user_data[consts.FROM_CHAT] = True
        if user.user_id != challenge_owner_id:
            query.edit_message_text(f"Siz https://t.me/shamsquizbot botimizda \"IsmiGul\" bo'lib qolib ketibsiz, iltimos botga o'tib ro'yxatdan o'ting. Ro'xatdan o'tib bo'lgach \"Tekshirish\" tugmasini bosing", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Tekshirish", callback_data=f"check-{user_challenge.id}-{challenge_owner_id}-{user.user_id}-{received_type}")]]))

    elif received_type == consts.ACCEPT:

        if user.user_id != challenge_owner_id:

            if type_of_challenge == "revansh":
                user_challenge.users.add(user)
                user_challenge.opponent = user
                user_challenge.users.add(user)
                user_challenge.save()
                context.bot.send_message(chat_id=challenge_owner_id, text=f"<a href='tg://user?id={user.user_id}'>{user.name}</a> qayta bellashuvga rozi bo'ldi.Bellashuvni boshlash uchun \"Boshlash\" tugmasini bosing ", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Boshlash", callback_data=f"confirmation-challenge-{user_challenge.id}-start-user-{challenge_owner_id}")]]), parse_mode=ParseMode.HTML)

                query.edit_message_text(text="Siz qayta bellashuvga rozi bo'ldingiz. Bellashuvni boshlash uchun \"Boshlash\" tugmasini bosing ",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Boshlash", callback_data=f"confirmation-challenge-{user_challenge.id}-start-opponent-{user.user_id}")]]), parse_mode=ParseMode.HTML)
            elif type_of_challenge == "challenge":
                if user_challenge.opponent is not None:
                    query.edit_message_text(
                        "Afsuski do'stingiz boshqasi bilan bellashmoqda. https://t.me/shamsquizbot botimiz orqali bellashuv yaratishingiz hamda do'stingiz bilan bellashishingiz mumkin.")
                    return
                else:
                    user_challenge.users.add(user)
                    user_challenge.opponent = user
                    user_challenge.users.add(user)

                    user_challenge.save()
                query.edit_message_text(
                    text=f"<a href='tg://user?id={query.from_user.id}'>{user.name}</a> bellashuvni qabul qildi.", parse_mode=ParseMode.HTML)
                message_id = user_challenge.created_challenge_message_id
                chat_id = user_challenge.created_challenge_chat_id
                context.bot.delete_message(
                    chat_id=chat_id, message_id=message_id)
                context.bot.send_message(chat_id=challenge_owner_id, text=f"<a href='tg://user?id={user.user_id}'>{user.name}</a> bellashuvga rozi bo'ldi.Bellashuvni boshlash uchun \"Boshlash\" tugmasini bosing ", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Boshlash", callback_data=f"confirmation-challenge-{user_challenge.id}-start-user-{challenge_owner_id}")]]), parse_mode=ParseMode.HTML)
                context.bot.send_message(chat_id=user.user_id, text="Siz bellashuvga rozi bo'ldingiz. Bellashuvni boshlash uchun \"Boshlash\" tugmasini bosing ",
                                         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Boshlash", callback_data=f"confirmation-challenge-{user_challenge.id}-start-opponent-{user.user_id}")]]), parse_mode=ParseMode.HTML)
    elif received_type == consts.DECLINE:
        if user.user_id != challenge_owner_id:
            if type_of_challenge == "revansh":
                query.edit_message_text(
                    f" Siz qayta bellashishni rad etdingiz.", reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Bosh Sahifa", callback_data=f"home-page-{user.user_id}")]]), parse_mode=ParseMode.HTML)
                context.bot.send_message(chat_id=challenge_owner_id, text=f" <a href='tg://user?id={query.from_user.id}'>{user.name}</a> qayta bellashishga rozilik bildirmadi.", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Bosh Sahifa", callback_data=f"home-page-{user_challenge.user.user_id}")]]), parse_mode=ParseMode.HTML)

            else:
                query.edit_message_text(
                    f" <a href='tg://user?id={query.from_user.id}'>{user.name}</a> bellashuvga qatnashishni rad etdi.", parse_mode=ParseMode.HTML)


def user_check(update: Update, context: CallbackContext):
    query = update.callback_query
    data = update.callback_query.data.split("-")
    user_challenge_id = data[1]
    user_challenge_id = int(user_challenge_id)

    user_challenge = UserChallenge.objects.prefetch_related('questions').prefetch_related('users').select_related(
        'user').select_related('opponent').select_related('challenge').get(id=user_challenge_id)
    challenge_owner_id = data[2]
    challenge_owner_id = int(challenge_owner_id)

    user_id = data[3]
    user_id = int(user_id)
    received_type = data[4]
    user, _ = User.get_user_and_created(update, context)

    user.user_id = str(query.from_user.id)

    if user.name == "IsmiGul":
        if user.user_id != challenge_owner_id:
            query.edit_message_text(f"Siz https://t.me/shamsquizbot botimizda hali ham \"IsmiGul\" bo'lib qolib ketibsiz, iltimos botga o'tib ro'yxatdan o'ting. Ro'yxatdan o'tib bo'lgach \"Tekshirish\" tugmasini bosing", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Tekshirish", callback_data=f"check-{user_challenge_id}-{challenge_owner_id}-{user_id}-{received_type}")]]), parse_mode=ParseMode.HTML)

    elif received_type == consts.ACCEPT:
        if user.user_id != challenge_owner_id:
            user_challenge.users.add(user)
            user_challenge.opponent = user
            user_challenge.save()
            query.edit_message_text(
                f"<a href='tg://user?id={query.from_user.id}'>{user.name}</a> bellashuvga rozilik bildirdi.", parse_mode=ParseMode.HTML)
            message_id = user_challenge.created_challenge_message_id
            chat_id = user_challenge.created_challenge_chat_id
            context.bot.delete_message(
                chat_id=chat_id, message_id=message_id)
            context.bot.send_message(chat_id=challenge_owner_id, text=f"<a href='tg://user?id={user.user_id}'>{user.name}</a> bellashuvga rozi bo'ldi.Bellashuvni boshlash uchun \"Boshlash\" tugmasini bosing ", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Boshlash", callback_data=f"confirmation-challenge-{user_challenge.id}-start-user-{challenge_owner_id}")]]), parse_mode=ParseMode.HTML)
            context.bot.send_message(chat_id=user.user_id, text="Siz bellashuvga rozi bo'ldingiz. Bellashuvni boshlash uchun \"Boshlash\" tugmasini bosing ",
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Boshlash", callback_data=f"confirmation-challenge-{user_challenge.id}-start-opponent-{user.user_id}")]]))
    elif received_type == consts.DECLINE:
        if user.user_id != challenge_owner_id:
            query.edit_message_text(
                f"<a href='tg://user?id={query.from_user.id}'>{user.name}</a> bellashuvni rad etdi.", parse_mode=ParseMode.HTML)


def challenge_confirmation(update: Update, context: CallbackContext) -> None:

    query = update.callback_query
    data = update.callback_query.data.split("-")
    user_challenge_id = int(data[2])
    user_type = data[4]
    user_id = int(data[5])

    user = User.objects.get(user_id=user_id)
    user_challenge = UserChallenge.objects.prefetch_related('questions').prefetch_related('users').select_related(
        'user').select_related('opponent').select_related('challenge').get(id=user_challenge_id)

    query.answer()

    if user_type == "user":
        now = datetime.now()
        user_challenge.user_started_at = now
        user_challenge.user.is_busy = True
        user_challenge.user.save()
        user_challenge.save()

        context.user_data["number_of_test"] = 1

        user_challenge.create_user_answers()
        question = user_challenge.last_unanswered_question(user_challenge.user)
        query.delete_message()
        del_message = query.message.reply_text(
            f"Test boshlandi!\n\n Testlar soni: 10 ta", reply_markup=ReplyKeyboardRemove())
        context.user_data["message_id"] = del_message.message_id
        context.user_data["chat_id"] = update.callback_query.message.chat_id

        helpers.send_test(update=update, context=context,
                          question=question, user_exam=user_challenge, user=user, type="challenge")

    elif user_type == "opponent":
        now = datetime.now()
        user_challenge.opponent_started_at = now
        user_challenge.opponent.is_busy = True
        user_challenge.opponent.save()
        user_challenge.save()
        context.user_data["number_of_test"] = 1

        user_challenge.create_opponent_answers()
        question = user_challenge.last_unanswered_question(
            user_challenge.opponent)
        query.delete_message()
        del_message = query.message.reply_text(
            f"Test boshlandi!\n\n Testlar soni: 10 ta", reply_markup=ReplyKeyboardRemove())
        context.user_data["message_id"] = del_message.message_id
        context.user_data["chat_id"] = update.callback_query.message.chat_id
        helpers.send_test(update=update, context=context,
                          question=question, user_exam=user_challenge, user=user, type="challenge")

    return consts.SHARING_CHALLENGE


def challenge_handler(update: Update, context: CallbackContext):
    data = update.callback_query.data.split("-")
    question_id = int(data[2])

    question_option_id = int(data[3])

    user_challenge_id = int(data[4])

    from_user_id = int(data[5])

    user = User.objects.get(user_id=from_user_id)

    question_option = QuestionOption.objects.select_related(
        'question').get(id=question_option_id)

    user_challenge_answers = UserChallengeAnswer.objects.select_related('user_challenge', 'user', 'question').filter(
        user_challenge__id=user_challenge_id).filter(question__id=question_id).filter(user=user)
    user_challenge_answer = user_challenge_answers[0]

    user_challenge = UserChallenge.objects.prefetch_related('questions').prefetch_related('users').select_related(
        'user').select_related('opponent').select_related('challenge').get(id=user_challenge_id)

    text = f"<b>Bellashuv turi:</b> {user_challenge.challenge.stage}-bosqich savollari. "

    user_challenge_answer.is_correct = question_option.is_correct
    user_challenge_answer.option_id = question_option.id
    user_challenge_answer.answered = True
    user_challenge_answer.save()

    question = user_challenge.last_unanswered_question(user)
    if question:
        helpers.send_test(update=update, context=context,
                          question=question, user_exam=user_challenge, user=user, type="challenge")

    else:
        now = datetime.now()
        update.callback_query.delete_message()
        context.bot.delete_message(
            chat_id=context.user_data['chat_id'], message_id=context.user_data["message_id"])
        if user.user_id == user_challenge.user.user_id:  # user ekan
            user_challenge.update_score("user")
            user_challenge.user_finished_at = now
            user_challenge.is_user_finished = True
            user_challenge.is_random_opponent = False
            user_challenge.save()
            if user_challenge.is_opponent_finished:
                user.is_busy = False
                user.save()
                user_duration = user_challenge.user_duration()
                opponent_duration = user_challenge.opponent_duration()
                user_time = helpers.get_duration(user_duration)
                opponent_time = helpers.get_duration(opponent_duration)
                message_id = user_challenge.opponent_message_id
                chat_id = user_challenge.opponent_chat_id
                context.bot.delete_message(
                    chat_id=chat_id, message_id=message_id)
                user_challenge.is_active = False
                user_challenge.user_timer = user_time
                user_challenge.opponent_timer = opponent_time
                user_challenge.save()

                if user_challenge.user_score > user_challenge.opponent_score:
                    user_challenge.winner = user_challenge.user
                    text += f"\n<a href='tg://user?id={user_challenge.user.user_id}'>{user_challenge.user.name}</a>:👑{user_challenge.user_score}/10  ⏳{user_time}\n<a href='tg://user?id={user_challenge.opponent.user_id}'>{user_challenge.opponent.name}</a>:😭{user_challenge.opponent_score}/10  ⏳{opponent_time}"
                elif user_challenge.user_score < user_challenge.opponent_score:
                    user_challenge.winner = user_challenge.opponent
                    text += f"\n<a href='tg://user?id={user_challenge.opponent.user_id}'>{user_challenge.opponent.name}</a>:👑{user_challenge.opponent_score}/10  ⏳{opponent_time}\n<a href='tg://user?id={user_challenge.user.user_id}'>{user_challenge.user.name}</a>:😭{user_challenge.user_score}/10  ⏳{user_time}"
                elif user_challenge.user_score == user_challenge.opponent_score:
                    if user_duration < opponent_duration:
                        user_challenge.winner = user_challenge.user
                        text += f"\n<a href='tg://user?id={user_challenge.user.user_id}'>{user_challenge.user.name}</a>:👑{user_challenge.user_score}/10  ⏳{user_time}\n<a href='tg://user?id={user_challenge.opponent.user_id}'>{user_challenge.opponent.name}</a>:😭{user_challenge.opponent_score}/10  ⏳{opponent_time}"
                    elif user_duration > opponent_duration:
                        user_challenge.winner = user_challenge.opponent
                        text += f"\n<a href='tg://user?id={user_challenge.opponent.user_id}'>{user_challenge.opponent.name}</a>:👑{user_challenge.opponent_score}/10  ⏳{opponent_time}\n<a href='tg://user?id={user_challenge.user.user_id}'>{user_challenge.user.name}</a>:😭{user_challenge.user_score}/10  ⏳{user_time}"

                text += "\n⚠️Raqib bilan qayta bellashish uchun \"Qayta bellashish\" tugmasini bosing\nBellashuvdagi yo'l qo'ygan xatolaringizni bilish uchun esa \"Noto'g'ri javoblar\" tugmasini bosing."
                # sending challenge results
                user_message = context.bot.send_message(
                    chat_id=user_challenge.user.user_id, text=text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Qayta bellashish", callback_data=f"revansh-{user_challenge.id}-{user_challenge.user.user_id}-{user_challenge.opponent.user_id}")], [InlineKeyboardButton("Noto'g'ri javoblar", callback_data=f"comments-challenge-{user_challenge.id}-{user.user_id}")], [InlineKeyboardButton("Bosh Sahifa", callback_data=f"home-page-{user_challenge.user.user_id}")], ]), parse_mode=ParseMode.HTML)
                if user_challenge.opponent.is_busy:
                    user_challenge.opponent.is_ended_challenge_waites = True
                    user_challenge.opponent.save()
                    user_challenge.is_waited_challenge = True
                    user_challenge.save()
                else:
                    opponent_message = context.bot.send_message(
                        chat_id=user_challenge.opponent.user_id, text=text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Qayta bellashish", callback_data=f"revansh-{user_challenge.id}-{user_challenge.opponent.user_id}-{user_challenge.user.user_id}")], [InlineKeyboardButton("Noto'g'ri javoblar", callback_data=f"comments-challenge-{user_challenge.id}-{user.user_id}")], [InlineKeyboardButton("Bosh Sahifa", callback_data=f"home-page-{user_challenge.opponent.user_id}-")]]), parse_mode=ParseMode.HTML)
                    user_challenge.opponent_message_id = opponent_message.message_id
                    user_challenge.opponent_chat_id = opponent_message.chat_id

                user_challenge.user_message_id = user_message.message_id
                user_challenge.user_chat_id = user_message.chat_id

                user_challenge.save()
                user.is_busy = False
                user.save()
                if user.is_ended_challenge_waites:
                    ended_challenges = UserChallenge.objects.prefetch_related('questions').prefetch_related('users').select_related(
                        'user').select_related('opponent').select_related('challenge').filter(users=user, is_active=False).filter(is_waited_challenge=True)
                    for ended_challenge in ended_challenges:
                        opponent = ended_challenge.user
                        if ended_challenge.user.user_id == user.user_id:
                            opponent = ended_challenge.opponent

                        text = f"Avvalroq {ended_challenge.challenge.stage}-bosqich bo'yicha <a href='tg://user?id={opponent.user_id}'>{opponent.name}</a>  bilan bellashuvingiz natijasi:\n\n"
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
                    user_challenge = UserChallenge.objects.prefetch_related('questions').prefetch_related(
        'users').select_related('user').select_related('opponent').select_related('challenge').get(
                        id=int(user.challenge_id))
                    context.bot.send_message(user.user_id, f"Sizga {user_challenge.challenge.stage}-bosqich savollari bo'yicha tasodifiy raqib topildi. Bellashish uchun \"Boshlash\" tugmasini bosing. ", reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Boshlash", callback_data=f"confirmation-random-{user_challenge.id}-start-user-{user.user_id}")]]), parse_mode=ParseMode.HTML)

                return ConversationHandler.END
            else:
                text += f"\nRaqibingiz hali tugatmadi. Raqibingiz tugatishi bilanoq sizga bellashuv natijalarini jo'natamiz.\n\nRaqibingiz tugatishini kutib o'tirmaslik uchun quyidagi \"{consts.HOME_PAGE}\" tugmasi orqali botdan foydalanishni davom ettirishingiz mumkin."
                not_finished_text = context.bot.send_message(
                    user.user_id, text=text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Bosh Sahifa", callback_data=f"home-page-{user_challenge.user.user_id}-challenge")]]), parse_mode=ParseMode.HTML)
                user_challenge.opponent.is_ended_challenge_waites = True
                user_challenge.user_message_id = not_finished_text.message_id
                user_challenge.user_chat_id = not_finished_text.chat_id
                user_challenge.save()

        elif user.user_id == user_challenge.opponent.user_id:  # opponent ekan
            user_challenge.update_score("opponent")
            user_challenge.opponent_finished_at = now
            user_challenge.is_opponent_finished = True
            user_challenge.is_random_opponent = False
            user_challenge.save()

            if user_challenge.is_user_finished:
                user.is_busy = False
                user.save()
                user_duration = user_challenge.user_duration()
                opponent_duration = user_challenge.opponent_duration()
                user_time = helpers.get_duration(user_duration)
                opponent_time = helpers.get_duration(opponent_duration)
                message_id = user_challenge.user_message_id
                chat_id = user_challenge.user_chat_id
                context.bot.delete_message(
                    chat_id=chat_id, message_id=message_id)
                user_challenge.is_active = False
                user_challenge.user_timer = user_time
                user_challenge.opponent_timer = opponent_time
                user_challenge.save()

                if user_challenge.user_score > user_challenge.opponent_score:
                    user_challenge.winner = user_challenge.user
                    text += f"\n<a href='tg://user?id={user_challenge.user.user_id}'>{user_challenge.user.name}</a>:👑{user_challenge.user_score}/10  ⏳{user_time}\n<a href='tg://user?id={user_challenge.opponent.user_id}'>{user_challenge.opponent.name}</a>:😭{user_challenge.opponent_score}/10  ⏳{opponent_time}"
                elif user_challenge.user_score < user_challenge.opponent_score:
                    user_challenge.winner = user_challenge.opponent
                    text += f"\n<a href='tg://user?id={user_challenge.opponent.user_id}'>{user_challenge.opponent.name}</a>:👑{user_challenge.opponent_score}/10  ⏳{opponent_time}\n<a href='tg://user?id={user_challenge.user.user_id}'>{user_challenge.user.name}</a>:😭{user_challenge.user_score}/10  ⏳{user_time}"
                elif user_challenge.user_score == user_challenge.opponent_score:
                    if user_duration < opponent_duration:
                        user_challenge.winner = user_challenge.user
                        text += f"\n<a href='tg://user?id={user_challenge.user.user_id}'>{user_challenge.user.name}</a>:👑{user_challenge.user_score}/10  ⏳{user_time}\n<a href='tg://user?id={user_challenge.opponent.user_id}'>{user_challenge.opponent.name}</a>:😭{user_challenge.opponent_score}/10  ⏳{opponent_time}"
                    elif user_duration > opponent_duration:
                        user_challenge.winner = user_challenge.opponent
                        text += f"\n<a href='tg://user?id={user_challenge.opponent.user_id}'>{user_challenge.opponent.name}</a>:👑{user_challenge.opponent_score}/10  ⏳{opponent_time}\n<a href='tg://user?id={user_challenge.user.user_id}'>{user_challenge.user.name}</a>:😭{user_challenge.user_score}/10  ⏳{user_time}"

                text += "\n⚠️Raqib bilan qayta bellashish uchun \"Qayta bellashish\" tugmasini bosing\nBellashuvdagi yo'l qo'ygan xatolaringizni bilish uchun esa \"Noto'g'ri javoblar\" tugmasini bosing."
                # sending challenge results
                opponent_message = context.bot.send_message(
                    chat_id=user_challenge.opponent.user_id, text=text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Qayta bellashish", callback_data=f"revansh-{user_challenge.id}-{user_challenge.opponent.user_id}-{user_challenge.user.user_id}")], [InlineKeyboardButton("Noto'g'ri javoblar", callback_data=f"comments-challenge-{user_challenge.id}-{user.user_id}")], [InlineKeyboardButton("Bosh Sahifa", callback_data=f"home-page-{user_challenge.opponent.user_id}-{user_challenge.id}")]]), parse_mode=ParseMode.HTML)
                if user_challenge.user.is_busy:
                    user_challenge.user.is_ended_challenge_waites = True
                    user_challenge.user.save()
                    user_challenge.is_waited_challenge = True
                    user_challenge.save()
                else:
                    user_message = context.bot.send_message(
                        chat_id=user_challenge.user.user_id, text=text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Qayta bellashish", callback_data=f"revansh-{user_challenge.id}-{user_challenge.user.user_id}-{user_challenge.opponent.user_id}")], [InlineKeyboardButton("Noto'g'ri javoblar", callback_data=f"comments-challenge-{user_challenge.id}-{user.user_id}")], [InlineKeyboardButton("Bosh Sahifa", callback_data=f"home-page-{user_challenge.user.user_id}-{user_challenge.id}")]]), parse_mode=ParseMode.HTML)
                    user_challenge.user_message_id = user_message.message_id
                    user_challenge.user_chat_id = update.callback_query.message.chat_id

                user_challenge.opponent_message_id = opponent_message.message_id
                user_challenge.opponent_chat_id = update.callback_query.message.chat_id
                user_challenge.save()

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
                    user_challenge = UserChallenge.objects.prefetch_related('questions').prefetch_related(
        'users').select_related('user').select_related('opponent').select_related('challenge').get(
                        id=int(user.challenge_id))
                    context.bot.send_message(user.user_id, f"Sizga {user_challenge.challenge.stage}-bosqich savollari bo'yicha tasodifiy raqib topildi. Bellashish uchun \"Boshlash\" tugmasini bosing. ", reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Boshlash", callback_data=f"confirmation-random-{user_challenge.id}-start-user-{user.user_id}")]]), parse_mode=ParseMode.HTML)    
                return ConversationHandler.END

            else:
                text += f"\nRaqibingiz hali tugatmadi. Raqibingiz tugatishi bilanoq sizga test natijalarini jo'natamiz.\n\nRaqibingiz tugatishini kutib o'tirmaslik uchun quyidagi \"{consts.HOME_PAGE}\" tugmasi orqali botdan foydalanishni davom ettirishingiz mumkin"
                not_finished_text = context.bot.send_message(
                    user.user_id, text=text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Bosh Sahifa", callback_data=f"home-page-{user_challenge.opponent.user_id}-challenge")]]), parse_mode=ParseMode.HTML)
                user_challenge.user.is_ended_challenge_waites = True
                user_challenge.opponent_message_id = not_finished_text.message_id
                user_challenge.opponent_chat_id = update.callback_query.message.chat_id
                user_challenge.save()

    return consts.SHARING_CHALLENGE


def revoke_challenge(update: Update, context: CallbackContext):
    data = update.callback_query.data.split("-")
    user_challenge_id = int(data[3])

    user_id = int(data[2])

    user_challenge = UserChallenge.objects.prefetch_related('questions').prefetch_related('users').select_related(
        'user').select_related('opponent').select_related('challenge').get(id=user_challenge_id)
    message_id = user_challenge.created_challenge_message_id
    chat_id = user_challenge.created_challenge_chat_id
    user_challenge.delete()

    if data[4] == "random":
        pass
    else:
        context.bot.delete_message(
            chat_id=chat_id, message_id=message_id)

    context.bot.send_message(chat_id=user_id, text="Yangi bellashuv yaratish uchun quyidagi bosqichlardan birini tanlang🔽", reply_markup=ReplyKeyboardMarkup([
        [consts.FIRST, consts.SECOND], [consts.THIRD,
                                        consts.FOURTH], [consts.FIFTH, consts.BACK]
    ], resize_keyboard=True))

    return consts.SHARING_CHALLENGE


def leader(update: Update, context: CallbackContext) -> None:
    u, _ = User.get_user_and_created(update, context)

    users = User.objects.all().order_by('-score')
    text = "Top foydalanuvchilar:\n"
    simple_user_text = ""
    for user in users:
        user.set_user_score()

    leader_users = []
    for leader in users[:10]:
        leader_users.append(leader)

    for index, leader_user in enumerate(leader_users):

        if u.user_id == leader_user.user_id:
            text += f"\n{index+1})✅<b>{leader_user.name}</b>: \nUmumiy to'plangan ball🧮 - {leader_user.score}\nUmumiy bellashuvlar soni⚔️: {leader_user.challenges_count}\n"
        else:
            text += f"\n{index+1}) <b>{leader_user.name}</b>: \nUmumiy to'plangan ball🧮 - {leader_user.score}\nUmumiy bellashuvlar soni⚔️: {leader_user.challenges_count}\n"

    for number, user in enumerate(users):
        if u.user_id == user.user_id and u not in leader_users:
            simple_user_text = f"\n\n{number})✅ <b>{user.name}</b>: \nUmumiy to'plangan ball🧮 - {u.score}\nUmumiy bellashuvlar soni⚔️: {u.challenges_count}\n"

    text += simple_user_text
    update.message.reply_text(text=text, reply_markup=ReplyKeyboardMarkup(
        [[consts.BACK]], resize_keyboard=True), parse_mode=ParseMode.HTML)

    return consts.LEADERBOARD


def revansh(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split("-")

    user_challenge_id = int(data[1])

    from_user_id = int(data[2])

    to_user_id = int(data[3])

    user_challenge = UserChallenge.objects.prefetch_related('questions').prefetch_related('users').select_related(
        'user').select_related('opponent').select_related('challenge').get(id=user_challenge_id)

    if user_challenge.user.user_id == to_user_id:
        context.bot.delete_message(
            chat_id=user_challenge.user_chat_id, message_id=user_challenge.user_message_id)
    elif user_challenge.opponent.user_id == to_user_id:
        context.bot.delete_message(
            chat_id=user_challenge.opponent_chat_id, message_id=user_challenge.opponent_message_id)

    opponent = User.objects.get(user_id=to_user_id)
    challenge = Challenge.objects.prefetch_related(
        'questions').get(id=user_challenge.challenge.id)

    context.bot.answer_callback_query(
        callback_query_id=query.id, text="Qayta bellashuv haqidagi so'rovingiz raqibingizga jo'natildi", show_alert=True)
    query.delete_message()

    user_challenge = challenge.create_user_challenge(from_user_id, challenge)
    user_challenge.opponent = opponent
    user_challenge.save()

    context.bot.send_message(chat_id=to_user_id, text=f"<a href='tg://user?id={user_challenge.user.user_id}'>{user_challenge.user.name}</a> siz bilan {user_challenge.challenge.stage}-bosqich savollarida qayta bellashmoqchi. Bellashuvni qabul qilasizmi ?", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text=consts.ACCEPT, callback_data=f"received-revansh-{consts.ACCEPT}-{user_challenge.user.user_id}-{user_challenge.id}")],
                                                                                                                                                                                                                                                                                                   [InlineKeyboardButton(
                                                                                                                                                                                                                                                                                                       text=consts.DECLINE, callback_data=f"received-revansh-{consts.DECLINE}-{user_challenge.user.user_id}-{user_challenge.id}")]
                                                                                                                                                                                                                                                                                                   ]), parse_mode=ParseMode.HTML)
    return consts.SHARING_CHALLENGE
