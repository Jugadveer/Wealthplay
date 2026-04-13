"""
API views for scenario quiz - returns JSON for React frontend
"""
import json 
import random 
from django .shortcuts import get_object_or_404 
from django .http import JsonResponse 
from django .views .decorators .csrf import csrf_exempt 
from django .contrib .auth .decorators import login_required 
from rest_framework .decorators import api_view ,permission_classes 
from rest_framework .permissions import IsAuthenticated 
from rest_framework .response import Response 
from .models import Scenario ,DecisionOption ,QuizRun ,UserScenarioAttempt 
from users .models import UserProfile ,ChallengeLeaderboard 
from django .utils import timezone 
from datetime import timedelta 


@api_view (['POST'])
@permission_classes ([IsAuthenticated ])
def start_quiz_api (request ):
    """Start a new quiz session - returns JSON with runId"""
    try :

        all_ids =list (Scenario .objects .values_list ('id',flat =True ))


        import threading 
        from .scenario_generator import generate_dynamic_scenario 
        threading .Thread (target =generate_dynamic_scenario ,args =(request .user ,),daemon =True ).start ()

        if len (all_ids )==0 :

            seed_scenarios =[
            {
            'title':'Emergency Fund Decision',
            'description':'You just received your first salary of ₹50,000. Your car needs urgent repair costing ₹15,000 and you have no emergency fund. What do you do?',
            'options':[
            {'text':'Pay from salary and start building an emergency fund with ₹5,000/month','decision_type':'SAVE','score':20 ,'balance_impact':-15000 ,'why_it_matters':'Building an emergency fund while handling immediate needs is the balanced approach.','mentor_feedback':'Great choice! Prioritizing both immediate needs and long-term safety.'},
            {'text':'Take a personal loan for the repair','decision_type':'INVEST','score':5 ,'balance_impact':0 ,'why_it_matters':'Taking a loan for a small expense adds interest burden unnecessarily.','mentor_feedback':'Avoid high-interest debt for small expenses when you have cash available.'},
            {'text':'Invest the full salary in stocks and delay the repair','decision_type':'INVEST','score':0 ,'balance_impact':0 ,'why_it_matters':'Ignoring urgent needs for investments is risky.','mentor_feedback':'Always handle urgent needs before investing. Safety first!'},
            ]
            },
            {
            'title':'SIP vs Lump Sum Investment',
            'description':'You have ₹2,00,000 saved up. The market has dropped 15% recently. Should you invest it all now or start a SIP?',
            'options':[
            {'text':'Start a SIP of ₹20,000/month over 10 months','decision_type':'INVEST','score':20 ,'balance_impact':-20000 ,'why_it_matters':'SIP averages out market volatility and reduces timing risk.','mentor_feedback':'Excellent! SIP is the safest way to enter a volatile market.'},
            {'text':'Invest the entire ₹2,00,000 as lump sum right now','decision_type':'INVEST','score':10 ,'balance_impact':-200000 ,'why_it_matters':'Lump sum can work in a falling market, but timing is very risky.','mentor_feedback':'Bold move! Historically, lump sum can outperform SIP if markets recover.'},
            {'text':'Keep the money in a savings account and wait','decision_type':'SAVE','score':5 ,'balance_impact':0 ,'why_it_matters':'Waiting too long means missing potential gains.','mentor_feedback':'Playing it safe is okay, but inflation erodes savings over time.'},
            ]
            },
            {
            'title':'Insurance vs Investment',
            'description':'An insurance agent offers you a ULIP plan promising 12% returns with life cover. Your friend suggests buying term insurance and investing separately. What do you choose?',
            'options':[
            {'text':'Buy term insurance + invest in index funds separately','decision_type':'INVEST','score':20 ,'balance_impact':-5000 ,'why_it_matters':'Separating insurance and investment gives better returns and coverage.','mentor_feedback':'Smart! This is what most financial advisors recommend.'},
            {'text':'Buy the ULIP plan','decision_type':'INVEST','score':5 ,'balance_impact':-15000 ,'why_it_matters':'ULIPs have high charges and returns are usually lower than promised.','mentor_feedback':'Be cautious of bundled products with high fees.'},
            {'text':'Skip both insurance and investment for now','decision_type':'SAVE','score':0 ,'balance_impact':0 ,'why_it_matters':'Having no insurance puts your family at financial risk.','mentor_feedback':'Life insurance is essential, especially if you have dependents.'},
            ]
            },
            ]

            for seed in seed_scenarios :
                scenario =Scenario .objects .create (
                title =seed ['title'],
                description =seed ['description'],
                starting_balance =50000 
                )
                for opt in seed ['options']:
                    DecisionOption .objects .create (
                    scenario =scenario ,
                    text =opt ['text'],
                    decision_type =opt ['decision_type'],
                    balance_impact =opt ['balance_impact'],
                    score =opt ['score'],
                    why_it_matters =opt ['why_it_matters'],
                    mentor_feedback =opt ['mentor_feedback']
                    )

            all_ids =list (Scenario .objects .values_list ('id',flat =True ))


        num_scenarios =random .randint (3 ,4 )
        if len (all_ids )<num_scenarios :
            selected_ids =all_ids 
        else :
            selected_ids =random .sample (list (all_ids ),num_scenarios )

        id_string =",".join (map (str ,selected_ids ))


        run =QuizRun .objects .create (
        user =request .user ,
        scenario_ids =id_string ,
        current_question_index =0 ,
        total_score =0 
        )

        return Response ({
        'success':True ,
        'runId':run .id ,
        'redirect':f'/scenario/quiz/{run .id }'
        })
    except Exception as e :
        import traceback 
        traceback .print_exc ()
        return Response ({'error':str (e )},status =500 )


@api_view (['GET'])
@permission_classes ([IsAuthenticated ])
def get_quiz_question (request ,run_id ):
    """Get current quiz question - returns JSON"""
    try :
        run =get_object_or_404 (QuizRun ,id =run_id ,user =request .user )

        if run .is_completed :
            return Response ({
            'completed':True ,
            'redirect':f'/scenario/quiz/{run_id }/result'
            })

        scenario_list =run .get_scenario_list ()


        if not scenario_list or len (scenario_list )==0 :
            run .is_completed =True 
            run .save ()
            return Response ({'error':'No scenarios in quiz','completed':True },status =400 )

        if run .current_question_index >=len (scenario_list ):
            run .is_completed =True 
            run .save ()
            return Response ({
            'completed':True ,
            'redirect':f'/scenario/quiz/{run_id }/result'
            })

        current_scenario_id =scenario_list [run .current_question_index ]
        scenario =get_object_or_404 (Scenario ,id =current_scenario_id )

        options_data =[]
        for option in scenario .options .all ():
            options_data .append ({
            'id':option .id ,
            'text':option .text ,
            'type':option .decision_type ,
            'score':option .score ,
            'impact':{
            'balance':float (option .balance_impact ),
            'confidence':option .confidence_delta ,
            'risk':option .risk_score_delta ,
            'growth_rate':float (option .future_growth_rate )
            },
            'content':{
            'why_matters':option .why_it_matters ,
            'mentor':option .mentor_feedback 
            }
            })

        return Response ({
        'run_id':run .id ,
        'scenario_ids':run .scenario_ids ,
        'scenario':{
        'id':scenario .id ,
        'title':scenario .title ,
        'description':scenario .description ,
        'starting_balance':float (scenario .starting_balance ),
        },
        'question_number':run .current_question_index +1 ,
        'total_questions':len (scenario_list ),
        'choices':options_data ,
        'total_score':run .total_score ,
        })
    except Exception as e :
        return Response ({'error':str (e )},status =500 )


@api_view (['POST'])
@permission_classes ([IsAuthenticated ])
def submit_answer_api (request ):
    """Submit quiz answer - tracks user attempt but doesn't award XP yet (awarded on result view)"""
    try :
        run_id =request .data .get ('run_id')
        score =request .data .get ('score')
        option_id =request .data .get ('option_id')

        if not run_id or score is None or not option_id :
            return Response ({'error':'Missing run_id, score, or option_id'},status =400 )

        try :
            run =QuizRun .objects .get (id =run_id ,user =request .user )
        except QuizRun .DoesNotExist :
            return Response ({
            'error':'QuizRun not found. Please start a new quiz.',
            'redirect':'/scenario'
            },status =404 )

        if not run .is_completed :

            scenario_list =run .get_scenario_list ()
            if run .current_question_index <len (scenario_list ):
                current_scenario_id =scenario_list [run .current_question_index ]
                scenario =get_object_or_404 (Scenario ,id =current_scenario_id )


                all_options =scenario .options .all ()
                max_score =max ((opt .score for opt in all_options ),default =0 )


                try :
                    option_id_int =int (option_id )
                except (ValueError ,TypeError ):
                    return Response ({
                    'error':f'Invalid option_id: {option_id }. Must be an integer.',
                    'debug':{
                    'option_id':option_id ,
                    'option_id_type':type (option_id ).__name__ ,
                    'scenario_id':current_scenario_id ,
                    'available_option_ids':[opt .id for opt in all_options ]
                    }
                    },status =400 )


                try :
                    selected_option =DecisionOption .objects .get (id =option_id_int )

                    if selected_option .scenario_id !=scenario .id :
                        return Response ({
                        'error':f'Option {option_id_int } does not belong to scenario {scenario .id }',
                        'debug':{
                        'option_scenario_id':selected_option .scenario_id ,
                        'current_scenario_id':scenario .id ,
                        'available_option_ids':[opt .id for opt in all_options ]
                        }
                        },status =400 )
                except DecisionOption .DoesNotExist :
                    return Response ({
                    'error':f'DecisionOption with id {option_id_int } does not exist',
                    'debug':{
                    'option_id':option_id_int ,
                    'scenario_id':current_scenario_id ,
                    'available_option_ids':[opt .id for opt in all_options ]
                    }
                    },status =404 )
                score_value =int (score )if score else selected_option .score 





                is_correct =score_value >=max_score and score_value >0 

                if is_correct :

                    run .total_score +=score_value 
                    run .save ()
                elif score_value >0 :



                    if score_value >=max_score /2 :
                        partial_score =10 
                    else :
                        partial_score =5 
                    run .total_score +=partial_score 
                    run .save ()
                    score_value =partial_score 
                else :

                    score_value =0 


                attempt ,created =UserScenarioAttempt .objects .update_or_create (
                user =request .user ,
                scenario =scenario ,
                quiz_run =run ,
                defaults ={
                'chosen_option':selected_option ,
                'score_earned':score_value ,
                'is_correct':is_correct ,
                'xp_awarded':0 ,
                }
                )
            else :

                is_correct =False 
                score_value =0 
        else :
            is_correct =False 
            score_value =0 

        run .refresh_from_db ()


        scenario_list =run .get_scenario_list ()
        has_more =run .current_question_index +1 <len (scenario_list )




        return Response ({
        'success':True ,
        'total_score':run .total_score ,
        'score_added':score_value ,
        'is_correct':is_correct ,
        'has_more':has_more ,
        'current_question_index':run .current_question_index ,
        'next_url':f'/scenario/quiz/{run_id }'if has_more else f'/scenario/quiz/{run_id }/result',
        })
    except Exception as e :
        import traceback 
        print (f"Error in submit_answer_api: {e }")
        print (traceback .format_exc ())
        return Response ({'error':str (e )},status =500 )


@api_view (['POST'])
@permission_classes ([IsAuthenticated ])
def next_question_api (request ,run_id ):
    """Move to next question - returns JSON"""
    try :
        run =get_object_or_404 (QuizRun ,id =run_id ,user =request .user )
        scenario_list =run .get_scenario_list ()

        if run .current_question_index +1 >=len (scenario_list ):
            run .is_completed =True 
            run .save ()
            return Response ({
            'completed':True ,
            'redirect':f'/scenario/quiz/{run_id }/result'
            })

        run .current_question_index +=1 
        run .save ()

        return Response ({
        'success':True ,
        'redirect':f'/scenario/quiz/{run_id }'
        })
    except Exception as e :
        return Response ({'error':str (e )},status =500 )


@api_view (['GET'])
@permission_classes ([IsAuthenticated ])
def get_scenarios_list (request ):
    """Get list of all available scenarios"""
    try :
        scenarios =Scenario .objects .all ()
        scenarios_data =[]
        for scenario in scenarios :
            scenarios_data .append ({
            'id':scenario .id ,
            'title':scenario .title ,
            'description':scenario .description ,
            'starting_balance':float (scenario .starting_balance ),
            })
        return Response (scenarios_data )
    except Exception as e :
        return Response ({'error':str (e )},status =500 )


@api_view (['GET'])
@permission_classes ([IsAuthenticated ])
def get_scenario_detail (request ,scenario_id ):
    """Get a single scenario with all its options"""
    try :
        scenario =get_object_or_404 (Scenario ,id =scenario_id )
        options_data =[]
        for option in scenario .options .all ():
            options_data .append ({
            'id':option .id ,
            'text':option .text ,
            'type':option .decision_type ,
            'score':option .score ,
            'impact':{
            'balance':float (option .balance_impact ),
            'confidence':option .confidence_delta ,
            'risk':option .risk_score_delta ,
            'growth_rate':float (option .future_growth_rate )
            },
            'content':{
            'why_matters':option .why_it_matters ,
            'mentor':option .mentor_feedback 
            }
            })

        return Response ({
        'id':scenario .id ,
        'title':scenario .title ,
        'description':scenario .description ,
        'starting_balance':float (scenario .starting_balance ),
        'choices':options_data ,
        })
    except Exception as e :
        return Response ({'error':str (e )},status =500 )


@api_view (['GET'])
@permission_classes ([IsAuthenticated ])
def get_quiz_result (request ,run_id ):
    """Get quiz result and check for achievements"""
    """Get quiz result - awards XP and updates streaks when viewing results"""
    try :
        run =get_object_or_404 (QuizRun ,id =run_id ,user =request .user )
        scenario_list =run .get_scenario_list ()
        total_possible_score =len (scenario_list )*20 

        if total_possible_score ==0 :
            percentage =0 
        else :
            percentage =(run .total_score /total_possible_score )*100 

        badge ="Financial Novice"
        badge_color ="gray"
        xp_awarded =0 


        if not run .xp_awarded :

            attempts =UserScenarioAttempt .objects .filter (
            user =request .user ,
            quiz_run =run ,
            xp_awarded =0 
            )

            total_xp =0 
            correct_count =0 

            for attempt in attempts :

                xp_for_attempt =min (attempt .score_earned ,20 )
                attempt .xp_awarded =xp_for_attempt 
                attempt .save ()
                total_xp +=xp_for_attempt 

                if attempt .is_correct :
                    correct_count +=1 


            if percentage >=80 :
                badge ="Wealth Master"
                badge_color ="gold"
                bonus_xp =100 
            elif percentage >=50 :
                badge ="Smart Saver"
                badge_color ="silver"
                bonus_xp =50 
            elif percentage >=30 :
                badge ="Budding Investor"
                badge_color ="bronze"
                bonus_xp =25 
            else :
                bonus_xp =10 

            total_xp +=bonus_xp 
            xp_awarded =total_xp 


            try :
                profile ,_ =UserProfile .objects .get_or_create (user =request .user )
                profile .xp +=total_xp 
                profile .save ()
            except Exception as e :
                print (f"Error updating user profile XP: {e }")


            try :
                leaderboard ,_ =ChallengeLeaderboard .objects .get_or_create (user =request .user )



                if correct_count >0 :

                    last_attempt =UserScenarioAttempt .objects .filter (
                    user =request .user 
                    ).exclude (quiz_run =run ).order_by ('-attempted_at').first ()

                    if last_attempt :

                        time_diff =timezone .now ()-last_attempt .attempted_at 
                        if time_diff <=timedelta (days =1 ):

                            leaderboard .current_streak +=1 
                        else :

                            leaderboard .current_streak =1 
                    else :

                        leaderboard .current_streak =1 


                    if leaderboard .current_streak >leaderboard .best_streak :
                        leaderboard .best_streak =leaderboard .current_streak 
                else :

                    leaderboard .current_streak =0 


                leaderboard .total_score +=run .total_score 
                leaderboard .total_predictions +=len (scenario_list )
                leaderboard .correct_predictions +=correct_count 
                leaderboard .save ()
            except Exception as e :
                print (f"Error updating leaderboard: {e }")


            run .xp_awarded =True 
            run .save ()


        try :
            leaderboard =ChallengeLeaderboard .objects .get (user =request .user )
            streak =leaderboard .current_streak 
        except ChallengeLeaderboard .DoesNotExist :
            streak =0 

        return Response ({
        'run_id':run .id ,
        'total_score':run .total_score ,
        'max_score':total_possible_score ,
        'percentage':int (percentage ),
        'badge':badge ,
        'badge_color':badge_color ,
        'total_questions':len (scenario_list ),
        'xp_awarded':xp_awarded ,
        'streak':streak ,
        })
    except Exception as e :
        import traceback 
        print (f"Error in get_quiz_result: {e }")
        print (traceback .format_exc ())
        return Response ({'error':str (e )},status =500 )

@api_view (['POST'])
@permission_classes ([IsAuthenticated ])
def complete_quiz_api (request ,run_id ):
    """Mark quiz as completed - rewards are already handled by result view but this is for status"""
    try :
        run =get_object_or_404 (QuizRun ,id =run_id ,user =request .user )
        run .is_completed =True 
        run .save ()
        return Response ({'success':True })
    except Exception as e :
        return Response ({'error':str (e )},status =500 )
