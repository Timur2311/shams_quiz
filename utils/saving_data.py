
import pandas as pd
import sys

from exam.models import Question

from group_challenge.models import Challenge

def saving_data():
    for i in range(40):
        workbook = pd.read_excel('media/questions/test.xlsx',sheet_name = i)
        all_columns = workbook.columns.tolist()
        print(f"\n\n{i}----{all_columns}\n\n")
        
        name_list = workbook['name']
        stage_list = workbook['stage']
        tour_list = workbook['tour']
        
        # print(f"\n\nname----{name_list[0]},{name_list[1]},{name_list[2]}\nstage---{stage_list[0]}\ntour---{tour_list[0]}\n\n")
        
        
        # print(f"{i+1}-sheet====={len(workbook['question'])}")
    # print(workbook.head())
        questions_list = workbook['question'].tolist()

        
        
        if len(questions_list)>0:
            for i, question_object in enumerate(questions_list):   
                exam_title = name_list[i]
                stage = int(stage_list[i])
                tour = int(tour_list[i])             
                content = questions_list[i]
                incorrect1 = questions_list[i+1]
                incorrect2 = questions_list[i+2]
                correct = questions_list[i+3]            
                true_definition = questions_list[i+4]
                
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
                
                if i+6>=len(questions_list):
                    break
                
            
       