import os
import json
import traceback
from dotenv import load_dotenv
load_dotenv()

from google import genai
from groq import Groq
from backend.rag.rag_engine import RAGEngine, RAG_PROMPT_TEMPLATE

def test_raw_errors():
    engine = RAGEngine()
    query = "what information do people remember while searching a photo?"
    
    with open("data/precomputed_stats.json", "r", encoding="utf-8") as f:
        precomputed = json.load(f)
        
    matches = engine.vector_store.query_similar(query, n_results=10)
    total_relevant = 916
    key_insights_summary = engine._build_key_insights_summary(precomputed)
    
    context_snippets = []
    for idx, m in enumerate(matches[:5], 1):
        context_snippets.append(f"[{idx}] Source: {m['source']} | Quote: \"{m.get('quote')}\" | Text: {m['matched_text'][:200]}")
    retrieved_context_str = "\n".join(context_snippets)
    
    prompt_input = RAG_PROMPT_TEMPLATE.format(
        prompt=query,
        chat_history_context="None",
        retrieved_context=retrieved_context_str,
        total_relevant=total_relevant,
        key_insights_summary=key_insights_summary,
        themes_summary="Themes summary test",
        situations_summary="Situations summary test"
    )

    print("================================================================================")
    print("1. CALLING GEMINI API (gemini-3.6-flash)...")
    print("================================================================================")
    try:
        g_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        resp = g_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt_input
        )
        print("GEMINI SUCCESS! Response snippet:", resp.text[:150])
    except Exception as e:
        print("GEMINI RAW EXCEPTION:")
        print(type(e).__name__, ":", str(e))
        print("\nFULL TRACEBACK:")
        traceback.print_exc()

    print("\n================================================================================")
    print("2. CALLING GEMINI API (gemini-3.8-flash)...")
    print("================================================================================")
    try:
        g_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        resp = g_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt_input
        )
        print("GEMINI 3.8 SUCCESS! Response snippet:", resp.text[:150])
    except Exception as e:
        print("GEMINI 3.8 RAW EXCEPTION:")
        print(type(e).__name__, ":", str(e))
        print("\nFULL TRACEBACK:")
        traceback.print_exc()

    print("\n================================================================================")
    print("3. CALLING GROQ API (openai/gpt-oss-20b)...")
    print("================================================================================")
    try:
        gr_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = gr_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt_input}]
        )
        print("GROQ SUCCESS! Response snippet:", resp.choices[0].message.content[:150])
    except Exception as e:
        print("GROQ RAW EXCEPTION:")
        print(type(e).__name__, ":", str(e))
        print("\nFULL TRACEBACK:")
        traceback.print_exc()

    print("\n================================================================================")
    print("4. CALLING GROQ API (openai/gpt-oss-120b)...")
    print("================================================================================")
    try:
        gr_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = gr_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt_input}]
        )
        print("GROQ 120B SUCCESS! Response snippet:", resp.choices[0].message.content[:150])
    except Exception as e:
        print("GROQ 120B RAW EXCEPTION:")
        print(type(e).__name__, ":", str(e))
        print("\nFULL TRACEBACK:")
        traceback.print_exc()

if __name__ == "__main__":
    test_raw_errors()
