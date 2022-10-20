import pandas as pd

from exam.models import Question

from group_challenge.models import Challenge

def saving_data():
    workbook = pd.read_excel('media/questions/test.xlsx')
    # print(workbook.head())
    questions_count = len(workbook['name'])
    if len(workbook['question'])>0:
        for i in range(questions_count):
            exam_title = workbook['name'].iloc[i]
            content = workbook['question'].iloc[i]
            stage = workbook['stage'].iloc[i]
            tour = workbook['tour'].iloc[i]
            true_definition = workbook['comment'].iloc[i]
            correct = workbook['correct'].iloc[i]            
            incorrect1 = workbook['incorrect1'].iloc[i]
            incorrect2 = workbook['incorrect2'].iloc[i]
             
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
                challenge = Challenge.objects.get(stage =stage)
                challenge.questions.add(question) 
                
        
                
            
       