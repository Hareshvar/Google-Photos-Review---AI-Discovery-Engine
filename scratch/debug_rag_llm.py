import os
import json
from dotenv import load_dotenv
load_dotenv()

from backend.rag.rag_engine import RAGEngine

def debug_llm():
    engine = RAGEngine()
    print(f"Groq Client: {engine._groq_client != None}")
    print(f"Gemini Client: {engine._gemini_client != None}")
    
    with open("data/precomputed_stats.json", "r", encoding="utf-8") as f:
        precomputed = json.load(f)
        
    prompt = "what information do people remember while searching a photo?"
    
    # Try calling Gemini directly
    if engine._gemini_client:
        try:
            print(f"Calling Gemini model: {engine.gemini_model}...")
            resp = engine._gemini_client.models.generate_content(
                model=engine.gemini_model,
                contents="Hello, respond with 1 word."
            )
            print("Gemini response:", resp.text)
        except Exception as e:
            print("Gemini exception:", e)
            
            # Try gemini-1.5-flash or gemini-2.5-flash
            try:
                print("Trying gemini-1.5-flash...")
                resp = engine._gemini_client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents="Hello, respond with 1 word."
                )
                print("Gemini 1.5 flash response:", resp.text)
            except Exception as e2:
                print("Gemini 1.5 flash exception:", e2)

if __name__ == "__main__":
    debug_llm()
