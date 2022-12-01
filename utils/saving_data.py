
import pandas as pd
import sys

from exam.models import Question

from group_challenge.models import Challenge


def saving_data():
    workbook = pd.read_excel(f'media/questions/test.xlsx', sheet_name="1")
    questions_list = workbook['question'].tolist()

    question_count = len(questions_list)

    name_list = workbook['name']
    stage_list = workbook['stage']
    tour_list = workbook['tour']

    if question_count > 0:
        for i in range(0, question_count, 5):
            if i+5 > len(questions_list):
                break
            exam_title = name_list[i]
            stage = int(float(stage_list[i]))
            tour = int(float(tour_list[i]))
            content = questions_list[i]
            incorrect1 = questions_list[i+1]
            incorrect2 = questions_list[i+2]
            correct = questions_list[i+3]
            true_definition = questions_list[i+4]


            question = Question.objects.create(
                content=content, stage=stage, tour=tour, true_definition=true_definition)
            question.create_exam(exam_title=exam_title)
            question.add_question_options(content=correct, is_correct=True)
            question.add_question_options(content=incorrect1)
            question.add_question_options(content=incorrect2)

            challenge_count = Challenge.objects.prefetch_related('questions__question_exams','questions__question_user_exams','questions__question_challenges','questions__question_user_challenges','questions__question_user_challenge_answers','questions__options','questions','questions').filter(stage=stage).count()

            if challenge_count == 0:
                challenge = Challenge.objects.create(stage=stage)
                challenge.questions.add(question)
            elif challenge_count > 0:
                challenge = Challenge.objects.prefetch_related('questions__question_exams','questions__question_user_exams','questions__question_challenges','questions__question_user_challenges','questions__question_user_challenge_answers','questions__options','questions','questions').get(stage=stage)
                challenge.questions.add(question)
