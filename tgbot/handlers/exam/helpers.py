from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton


from exam.models import UserExamAnswer, Exam, QuestionOption
from group_challenge.models import UserChallengeAnswer

def send_test(update, context, question, user_exam, user,type = "exam"):
    question_theme = Exam.objects.prefetch_related('questions').filter(questions = question)
    text= f"<b>Mavzu</b>: {question_theme[0].title}\n\n"
    number_of_test = context.user_data["number_of_test"]

    if type == "exam":        
        user_exam_answer = UserExamAnswer.objects.select_related('user_exam','question','user_exam__exam','user_exam__user').prefetch_related('user_exam__questions','user_exam__exam__questions').get(user_exam = user_exam, question=question)
        user_exam_answer.number = str(number_of_test)
        user_exam_answer.save()
    elif type =="challenge":
        user_challenge_answers = UserChallengeAnswer.objects.select_related('user_challenge','user','question','user_challenge__user','user_challenge__opponent','user_challenge__challenge','user_challenge__winner').prefetch_related('user_challenge__users','user_challenge__questions','user_challenge__challenge__questions').filter(user_challenge =user_exam, question=question,user=user)
        user_challenge_answer = user_challenge_answers.first()
        user_challenge_answer.number = str(number_of_test)
        user_challenge_answer.save()
        
        
        
    text += f"<b>Savol:</b> {question.content}\n"
    variants = ["A", "B", "C"]
    buttons = []
    
    question_options = QuestionOption.objects.select_related(
        'question').filter(question=question).order_by("?")

    for index, question_option in enumerate(question_options):
            text += f"\n<b>{variants[index]}</b>) {question_option.content}"
            buttons.append([InlineKeyboardButton(f"{variants[index]}", callback_data=f"question-variant-{question.id}-{question_option.id}-{user_exam.id}-{user.user_id}")])
            
    if number_of_test==1:
        context.bot.send_message(chat_id = user.user_id,text=text, reply_markup = InlineKeyboardMarkup(buttons), parse_mode = ParseMode.HTML)
        context.user_data["number_of_test"]+=1
    else:      
        update.callback_query.edit_message_text(text = text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)
        context.user_data["number_of_test"]+=1
    
def get_duration(duration):
    text = ""
    if duration//60==0:
            minutes = 0
            seconds = duration
            text = f"{seconds} sekund"
    elif duration//60>0:
            minutes = duration//60
            seconds = duration%60
            text = f"{minutes} daqiqayu {seconds} sekund"

    return text


def get_chat_id(update, context):
    chat_id = -1

    if update.message is not None:
        chat_id = update.message.chat.id
    elif update.callback_query is not None:
        chat_id = update.callback_query.message.chat.id
    elif update.poll is not None:
        chat_id = context.bot_data[update.poll.id]

    return chat_id
