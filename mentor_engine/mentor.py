import os 
from django .conf import settings 


BASE_DIR =settings .BASE_DIR 
DB_DIR =os .path .join (BASE_DIR ,"vector_db")
TOP_K =4 
MODEL_NAME ="sentence-transformers/all-MiniLM-L6-v2"




collection =None 
embed_model =None 

try :
    import chromadb 
    from sentence_transformers import SentenceTransformer 

    client =chromadb .PersistentClient (path =DB_DIR )
    collection =client .get_collection ("wealthplay_mentor")
    embed_model =SentenceTransformer (MODEL_NAME )
except Exception as e :
    print (f"[Mentor] Vector retrieval disabled: {e }")


SYSTEM_PROMPT ="""
You are WEALTHPLAY — a friendly and calm financial mentor for beginners.

Response Style:
- Use bullet points.
- Use 3–7 bullets depending on how complex the question is.
- Keep each bullet short (one clear idea per point).
- Use simple, beginner-friendly language.
- Add emojis only when helpful (max 1 per response).
- If user sounds confused, reassure them gently.

Content Behavior:
- Encourage budgeting, emergency funds, SIPs, long-term investing and financial confidence.
- Avoid stock picking, crypto hype, or risky trading guidance.
- If user asks for deep explanation, then expand — still in bullet form.

Tone Examples:
• Feeling unsure is normal when starting.
• A SIP means investing a fixed amount regularly (example: ₹200–₹500 monthly).
• Starting small builds confidence and consistency.
• You don't need to know everything — just take small steps 💛

Goal:
Make finance feel simple, safe, and doable — never overwhelming.
"""



def generate_response (user_input ):

    retrieved_text =""
    if collection is not None and embed_model is not None :
        try :
            embedding =embed_model .encode (user_input ).tolist ()
            results =collection .query (
            query_embeddings =[embedding ],
            n_results =TOP_K 
            )
            retrieved_text ="\n\n".join (results .get ("documents",[[]])[0 ])
        except Exception as e :
            print (f"[Mentor] Retrieval failed, continuing without context: {e }")

    full_prompt =f"""
User question: {user_input }

Relevant knowledge:
{retrieved_text if retrieved_text else 'No retrieved context available.'}

Now answer as the mentor:
"""

    try :
        from mentor_engine .gemini_client import gemini_chat 
        return gemini_chat (full_prompt ,system_prompt =SYSTEM_PROMPT )
    except Exception as e :
        print (f"[Mentor] Gemini error: {e }")
        return "• I'm having trouble connecting to my brain right now.\n• Please try again in a moment.\n• In the meantime, keep learning and stay curious! 💛"
