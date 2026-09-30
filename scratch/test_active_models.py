import os
from dotenv import load_dotenv
load_dotenv()
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

test_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash", "gemini-3.8-flash", "gemini-3.6-flash"]

for m in test_models:
    try:
        resp = client.models.generate_content(model=m, contents="Say hello")
        print(f"SUCCESS with model '{m}':", resp.text.strip())
        break
    except Exception as e:
        print(f"FAILED model '{m}':", e)
