import json 

from mentor_engine .gemini_client import gemini_chat_json 


def generate_dynamic_course (ticker ):
    """Generate a dynamic course module (Flashcards, MCQs, QnA) based on a ticker/topic."""
    try :
        prompt =f"""
        Generate an educational micro-course about the stock ticker/topic: {ticker }.
        Return a raw JSON object only, no markdown and no extra text.
        Required structure:
        {{
            "title": "Understanding {ticker }",
            "summary": "A brief 2 sentence summary of this asset.",
            "flash_cards": [
                {{"topic": "Concept 1", "theory_title": "Title 1", "theory_content": "2 sentences explaining."}},
                {{"topic": "Concept 2", "theory_title": "Title 2", "theory_content": "2 sentences explaining."}},
                {{"topic": "Concept 3", "theory_title": "Title 3", "theory_content": "2 sentences explaining."}}
            ],
            "mcqs": [
                {{"id": 1, "question": "Question 1?", "options": ["A", "B", "C", "D"], "correct_answer": 0, "explanation": "Why A is correct"}},
                {{"id": 2, "question": "Question 2?", "options": ["A", "B", "C", "D"], "correct_answer": 1, "explanation": "Why B is correct"}}
            ],
            "qna": [
                {{"q": "Common question about {ticker }?", "a": "Clear answer.", "explanation": "Additional context."}}
            ]
        }}
        """

        data =gemini_chat_json (prompt ,temperature =0.7 )
        return data if isinstance (data ,dict )else _get_fallback_data (ticker )
    except Exception as e :
        print (f"Error generating dynamic course with Gemini: {e }")
        return _get_fallback_data (ticker )


def _get_fallback_data (ticker ):
    return {
    "title":f"Understanding {ticker .upper ()}",
    "summary":f"An overview of {ticker .upper ()} fundamentals and market behavior.",
    "flash_cards":[
    {
    "topic":"Company Overview",
    "theory_title":"What is it?",
    "theory_content":f"{ticker .upper ()} represents a key asset in its sector. Studying its fundamentals gives insight into market trends.",
    }
    ],
    "mcqs":[
    {
    "id":1 ,
    "question":f"Why study {ticker .upper ()}?",
    "options":["To lose money","To understand market trends","To ignore news","Because it's random"],
    "correct_answer":1 ,
    "explanation":"Understanding major assets helps predict broader market movements.",
    }
    ],
    "qna":[
    {
    "q":f"What moves {ticker .upper ()}'s price?",
    "a":"Earnings reports, sector news, and macroeconomic factors.",
    "explanation":"Like any asset, supply and demand dictate price action.",
    }
    ],
    }
