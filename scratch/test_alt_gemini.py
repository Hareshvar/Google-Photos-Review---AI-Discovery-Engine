import os
from dotenv import load_dotenv
load_dotenv()
from google import genai

def test_models():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    models = ["gemini-2.0-flash-exp", "gemini-1.5-flash-8b", "gemini-2.5-flash-lite", "gemini-2.0-flash"]
    for m in models:
        try:
            resp = client.models.generate_content(
                model=m,
                contents="Respond with 1 word."
            )
            print(f"SUCCESS with {m}: {resp.text.strip()}")
            return m
        except Exception as e:
            print(f"FAILED {m}: {e}")

if __name__ == "__main__":
    test_models()
