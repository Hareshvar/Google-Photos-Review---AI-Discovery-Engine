import os
from dotenv import load_dotenv
load_dotenv()

from groq import Groq

def test_groq_models():
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    models_to_try = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"]
    
    for m in models_to_try:
        try:
            resp = client.chat.completions.create(
                model=m,
                messages=[{"role": "user", "content": "Hello, respond with 1 word."}],
                temperature=0.1
            )
            print(f"SUCCESS with model '{m}': {resp.choices[0].message.content.strip()}")
            return m
        except Exception as e:
            print(f"FAILED model '{m}': {e}")
            
if __name__ == "__main__":
    test_groq_models()
