from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton


from exam.models import UserExamAnswer
from group_challenge.models import UserChallengeAnswer

def send_test(update, context, question, user_exam, user,type = "exam"):
    
    text= f"<b>Mavzu</b>: {question.examm.all()[0].title}\n\n"
    number_of_test = context.user_data["number_of_test"]

    if type == "exam":        
        user_exam_answer = UserExamAnswer.objects.get(user_exam = user_exam, question=question)
        user_exam_answer.number = str(number_of_test)
        user_exam_answer.save()
    elif type =="challenge":
        user_challenge_answer = UserChallengeAnswer.objects.get(user_challenge = user_exam, question=question, user = user)
        user_challenge_answer.number = str(number_of_test)
        user_challenge_answer.save()
        
        
        
    text += f"<b>Savol:</b> {question.content}\n"
    variants = ["A", "B", "C"]
    buttons = []
    
    

    for index, question_option in enumerate(question.options.order_by("?")):
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

def send_exam_poll(context, question, chat_id):
    # POLL OPTIONS
    options = []
    correct_option_id = 0
    for index, option, in enumerate(question.options.all().order_by("?")):
        options.append(option.content)
        if option.is_correct:
            correct_option_id = index

    message = context.bot.send_poll(chat_id,
                                    question.content, options, type="quiz", correct_option_id=correct_option_id)
    # SAVE POLL ID WITH CHAT ID
    context.bot_data.update({message.poll.id: message.chat.id})
    


def get_chat_id(update, context):
    chat_id = -1

    if update.message is not None:
        chat_id = update.message.chat.id
    elif update.callback_query is not None:
        chat_id = update.callback_query.message.chat.id
    elif update.poll is not None:
        chat_id = context.bot_data[update.poll.id]

    return chat_id
