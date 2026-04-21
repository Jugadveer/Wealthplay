import os
from django.conf import settings


BASE_DIR = settings.BASE_DIR
DB_DIR = os.path.join(BASE_DIR, "vector_db")
TOP_K = 4
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


collection = None
embed_model = None

def get_mentor_resources():
    """Lazy load ChromaDB and SentenceTransformer to prevent startup hangs"""
    global collection, embed_model
    if collection is not None and embed_model is not None:
        return collection, embed_model
        
    # Skip loading during migrations
    import sys
    if any(cmd in sys.argv for cmd in ['makemigrations', 'migrate', 'check', 'showmigrations']):
        return None, None

    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        if collection is None:
            client = chromadb.PersistentClient(path=DB_DIR)
            try:
                collection = client.get_collection("wealthplay_mentor")
            except:
                print("[Mentor] Collection not found, creating dummy...")
                collection = client.get_or_create_collection("wealthplay_mentor")
                
        if embed_model is None:
            print("[Mentor] Loading sentence transformer...")
            embed_model = SentenceTransformer(MODEL_NAME)
            
        return collection, embed_model
    except Exception as e:
        print(f"[Mentor] Resources load failed: {e}")
        return None, None


SYSTEM_PROMPT = """
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


def generate_response(user_input):

    retrieved_text = ""
    col, model = get_mentor_resources()
    if col is not None and model is not None:
        try:
            embedding = model.encode(user_input).tolist()
            results = col.query(
                query_embeddings=[embedding],
                n_results=TOP_K
            )
            retrieved_text = "\n\n".join(results.get("documents", [[]])[0])
        except Exception as e:
            print(f"[Mentor] Retrieval failed, continuing without context: {e}")

    full_prompt = f"""
User question: {user_input}

Relevant knowledge:
{retrieved_text if retrieved_text else 'No retrieved context available.'}

Now answer as the mentor:
"""

    try:
        from mentor_engine.gemini_client import gemini_chat
        return gemini_chat(full_prompt, system_prompt=SYSTEM_PROMPT)
    except Exception as e:
        print(f"[Mentor] Gemini error: {e}")
        return "• I’m offline right now, but I can still help with basic finance questions.\n• Try asking about budgeting, emergency funds, SIPs, or diversification.\n• If you want, I can also help you think through one next money step."
