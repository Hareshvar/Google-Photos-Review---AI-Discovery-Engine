import os
import json
from dotenv import load_dotenv
load_dotenv()
from google import genai
from groq import Groq

def test_llm_call():
    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    with open("data/precomputed_stats.json", "r", encoding="utf-8") as f:
        precomputed = json.load(f)
        
    from backend.rag.rag_engine import RAGEngine
    engine = RAGEngine()
    
    matches = engine.vector_store.query_similar("what information do people remember while searching a photo?", n_results=10)
    total_relevant = 916
    key_insights_summary = engine._build_key_insights_summary(precomputed)
    
    from backend.rag.rag_engine import RAG_PROMPT_TEMPLATE
    prompt_input = RAG_PROMPT_TEMPLATE.format(
        prompt="what information do people remember while searching a photo?",
        chat_history_context="None",
        retrieved_context="\n".join([f"[{i+1}] Quote: {m['quote']}" for i, m in enumerate(matches[:5])]),
        total_relevant=total_relevant,
        key_insights_summary=key_insights_summary,
        themes_summary="Face rec failure 18.45%",
        situations_summary="Retrieving Person 11.24%"
    )
    
    print("Trying Gemini model...")
    try:
        g_client = genai.Client(api_key=gemini_key)
        resp = g_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt_input
        )
        print("\n=== GEMINI ANSWER ===")
        print(resp.text)
    except Exception as e:
        print("Gemini failed:", e)

    print("\nTrying Groq model...")
    try:
        gr_client = Groq(api_key=groq_key)
        resp = gr_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt_input}]
        )
        print("\n=== GROQ ANSWER ===")
        print(resp.choices[0].message.content)
    except Exception as e:
        print("Groq failed:", e)

if __name__ == "__main__":
    test_llm_call()
