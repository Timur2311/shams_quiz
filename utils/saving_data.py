import pandas as pd
import sys

from exam.models import Question

from group_challenge.models import Challenge

def saving_data():
    for i in range(40):
        workbook = pd.read_excel('media/questions/test.xlsx',sheet_name = i)
        exam_title = workbook['name'].iloc[0]
        stage = int(workbook['stage'].iloc[0])
        tour = int(workbook['tour'].iloc[0])
        print(f"{i+1}-sheet====={len(workbook['question'])}")
    # print(workbook.head())
        questions_count = len(workbook['question'])
        if questions_count%5==0:
            pass
        elif questions_count%5 !=0:
            questions_count=questions_count-1
        if questions_count>0:
            for i in range(0,questions_count,5):                
                content = workbook['question'].iloc[i]
                incorrect1 = workbook['question'].iloc[i+1]
                incorrect2 = workbook['question'].iloc[i+2]
                correct = workbook['question'].iloc[i+3]            
                true_definition = workbook['question'].iloc[i+4]
                
                # print(f"\n\ncontent--{content}\n incorrect1--{incorrect1}\n incorrect2--{incorrect2}\n correct--{correct} ")
                
                question  = Question.objects.create(content = content, stage = stage, tour = tour, true_definition=true_definition )    
                question.create_exam(exam_title=exam_title)
                question.add_question_options(content = correct, is_correct=True)
                question.add_question_options(content = incorrect1)
                question.add_question_options(content = incorrect2)
                
                
                challenge_count = Challenge.objects.filter(stage = stage).count()
                
                if challenge_count==0:
                    challenge = Challenge.objects.create(stage =stage)
                    challenge.questions.add(question) 
                elif challenge_count>0:
                    challenge = Challenge.objects.get(stage = stage)
                    challenge.questions.add(question) 
                
                if i+5>=questions_count:
                    break
                
            
       