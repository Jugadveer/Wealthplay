"""
Course Mentor with Two-Layer Response System
1. Fixed Q&A (immediate authoritative answers)
2. Gemini LLM with course context (for additional queries)
"""
import json 
import os 
import difflib 
from django .conf import settings 




COURSES_JSON_PATH =os .path .join (settings .BASE_DIR ,'financial_course.json')


COURSES_DATA =None 

def transform_topic_to_course (topic ):
    """Transform a topic (from topics structure) to course format"""
    lessons =topic .get ('lessons',[])


    modules =[]
    for lesson in lessons :

        fixed_qna =[]
        messages =lesson .get ('messages',[])


        if isinstance (messages ,list ):
            for i ,msg in enumerate (messages ):
                text =msg .get ('text','')


                if 'Q:'in text or ('?'in text and len (text )>10 ):

                    if i +1 <len (messages ):
                        answer_text =messages [i +1 ].get ('text','')
                        if answer_text and len (answer_text )>5 :
                            fixed_qna .append ({
                            'q':text .replace ('Q:','').strip (),
                            'a':answer_text .replace ('A:','').strip ()
                            })


        if not isinstance (fixed_qna ,list ):
            fixed_qna =[]

        module ={
        'id':lesson .get ('id',''),
        'title':lesson .get ('title',''),
        'summary':lesson .get ('title',''),
        'fixed_qna':fixed_qna 
        }
        modules .append (module )


    duration_mins =len (lessons )*5 

    course ={
    'id':topic .get ('id',''),
    'title':topic .get ('title',''),
    'overview':topic .get ('summary',topic .get ('title','')),
    'duration_mins':duration_mins ,
    'source':'',
    'modules':modules 
    }

    return course 


def load_courses ():
    """Load courses from JSON file - use as-is, no transformation"""
    global COURSES_DATA 
    if COURSES_DATA is None :
        try :
            with open (COURSES_JSON_PATH ,'r',encoding ='utf-8')as f :
                data =json .load (f )


            if isinstance (data ,list ):

                COURSES_DATA =data 
                print (f"Mentor engine: Loaded {len (COURSES_DATA )} courses")
            elif isinstance (data ,dict ):

                if 'topics'in data and isinstance (data ['topics'],list ):

                    topics =data ['topics']
                    COURSES_DATA =[transform_topic_to_course (topic )for topic in topics ]
                    print (f"Mentor engine: Loaded {len (COURSES_DATA )} courses (transformed from topics)")
                elif 'courses'in data and isinstance (data ['courses'],list ):
                    COURSES_DATA =data ['courses']
                    print (f"Mentor engine: Loaded {len (COURSES_DATA )} courses")
                else :
                    print (f"Mentor engine: JSON structure not recognized. Keys: {list (data .keys ())}")
                    COURSES_DATA =[]
            else :
                print (f"Mentor engine: Unexpected JSON structure: {type (data )}")
                COURSES_DATA =[]
        except Exception as e :
            print (f"Mentor engine: Error loading courses: {e }")
            import traceback 
            traceback .print_exc ()
            COURSES_DATA =[]
    return COURSES_DATA 


def find_course (course_id ):
    """Find a course by ID"""
    courses =load_courses ()


    if not isinstance (courses ,list ):
        print (f"ERROR: Courses is not a list, type: {type (courses )}")
        return None 

    if not course_id :
        print (f"ERROR: course_id is empty")
        return None 

    print (f"Looking for course_id: '{course_id }' in {len (courses )} courses")

    for course in courses :
        if isinstance (course ,dict ):
            course_id_val =course .get ("id")
            print (f"  Checking course: '{course_id_val }' == '{course_id }'? {course_id_val ==course_id }")
            if course_id_val ==course_id :
                print (f"  FOUND course: {course .get ('title')}")
                return course 

    print (f"  Course '{course_id }' NOT FOUND")
    return None 


def find_module (course ,module_id =None ):
    """Find a module within a course"""
    if not course or not isinstance (course ,dict ):
        return None 

    modules =course .get ("modules",[])
    if not isinstance (modules ,list )or not modules :
        return None 

    if module_id :
        for module in modules :
            if isinstance (module ,dict )and module .get ("id")==module_id :
                return module 


    return modules [0 ]if modules else None 


def fuzzy_match_q (fixed_qna ,user_q ,cutoff =0.7 ):
    """
    Find best question match using fuzzy matching
    Returns the matching Q&A if found, None otherwise
    """
    if not fixed_qna :
        return None 

    best =None 
    best_score =0 

    for qa in fixed_qna :
        q =qa .get ("q","").lower ()
        score =difflib .SequenceMatcher (None ,q ,user_q .lower ()).ratio ()
        if score >best_score :
            best_score =score 
            best =qa 

    return best if best_score >=cutoff else None 


def generate_gemini_response (course ,module ,user_question ):
    """Generate response using Gemini API with course context."""
    from mentor_engine .gemini_client import gemini_chat 

    course_title =course .get ('title','Financial Education')
    module_title =module .get ('title','')
    module_summary =module .get ('summary','')

    system_prompt =f"""You are Nex, an empathetic and practical financial mentor from WealthPlay.
You're helping learners understand {course_title }.
- Warm, encouraging, and patient
- Practical and actionable
- Keep responses concise (2-4 short paragraphs)
- Avoid jargon unless the user asks for definitions

Current Course Context:
- Course: {course_title }
- Module: {module_title }
- Module Summary: {module_summary }"""

    context_parts =[]
    fixed_qna =module .get ("fixed_qna",[])
    if not fixed_qna :
        try :
            from courses .models import ModuleContent 
            full_module_id =f"{course .get ('id','')}_{module .get ('id','')}"
            try :
                module_content =ModuleContent .objects .get (module_id =full_module_id )
                qna_pairs =module_content .qna_pairs .all ()[:3 ]
                fixed_qna =[{"q":qa .question ,"a":qa .answer }for qa in qna_pairs ]
                if module_content .theory_text :
                    context_parts .append (f"Theory: {module_content .theory_text [:300 ]}")
            except :
                pass 
        except :
            pass 

    for qa in fixed_qna [:3 ]:
        if isinstance (qa ,dict ):
            context_parts .append (f"Example Q: {qa .get ('q','')}\nExample A: {qa .get ('a','')}")

    full_prompt =user_question 
    if context_parts :
        full_prompt ="Reference examples:\n"+"\n\n".join (context_parts )+f"\n\nUser question: {user_question }"

    answer =gemini_chat (full_prompt ,system_prompt =system_prompt ,max_tokens =500 )
    if not answer :
        raise Exception ("Empty response from Gemini")
    return answer 



def mentor_respond (course_id ,module_id =None ,question =""):
    """
    Main mentor response function with two-layer system:
    1. Check fixed Q&A (fuzzy match)
    2. If no match, use Gemini with context
    """
    if not question :
        return {
        "type":"error",
        "answer":"Please provide a question.",
        "confidence":0 
        }


    course =find_course (course_id )
    if not course :
        return {
        "type":"error",
        "answer":f"Course '{course_id }' not found.",
        "confidence":0 
        }

    module =find_module (course ,module_id )
    if not module :
        return {
        "type":"error",
        "answer":f"Module not found in course '{course_id }'.",
        "confidence":0 
        }


    fixed_qna =module .get ("fixed_qna",[])


    if not fixed_qna :
        try :
            from courses .models import ModuleContent 
            full_module_id =f"{course_id }_{module_id or ''}"
            try :
                module_content =ModuleContent .objects .get (module_id =full_module_id )
                qna_pairs =module_content .qna_pairs .all ()
                fixed_qna =[{"q":qa .question ,"a":qa .answer }for qa in qna_pairs ]
            except ModuleContent .DoesNotExist :
                pass 
        except Exception as e :
            print (f"Could not load Q&A from database: {e }")

    match =fuzzy_match_q (fixed_qna ,question ,cutoff =0.7 )

    if match :
        return {
        "type":"fixed_qna",
        "answer":match .get ("a",""),
        "source":course .get ("source",""),
        "confidence":0.99 ,
        "matched_question":match .get ("q","")
        }


    try :
        answer =generate_gemini_response (course ,module ,question )

        return {
        "type":"llm",
        "answer":answer ,
        "source":course .get ("source",""),
        "confidence":0.85 
        }
    except Exception as e :

        module_summary =module .get ("summary","")
        theory_text =module .get ("theory_text","")


        try :
            from courses .models import ModuleContent 
            full_module_id =f"{course_id }_{module_id or ''}"
            try :
                module_content =ModuleContent .objects .get (module_id =full_module_id )
                theory_text =module_content .theory_text or theory_text 
                module_summary =module_content .summary or module_summary 
            except ModuleContent .DoesNotExist :
                pass 
        except :
            pass 


        if theory_text :
            fallback_answer =f"Based on {module .get ('title','this module')}: {theory_text [:200 ]}..."
        elif module_summary :
            fallback_answer =f"{module_summary } This is educational content about {module .get ('title','this topic')}."
        else :
            fallback_answer =f"I can help explain {module .get ('title','this topic')}. Please verify Gemini API keys are configured, or refer to the module content above."

        return {
        "type":"fallback",
        "answer":fallback_answer +f"\n\nNote: Full AI responses require a working Gemini configuration. Error: {str (e )[:100 ]}",
        "source":course .get ("source",""),
        "confidence":0.6 
        }

