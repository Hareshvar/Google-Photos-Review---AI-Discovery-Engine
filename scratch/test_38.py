import os
from dotenv import load_dotenv
load_dotenv()
from google import genai

def test_38():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    for m in ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-2.5-flash"]:
        try:
            resp = client.models.generate_content(
                model=m,
                contents="Hello, respond with 1 word."
            )
            print(f"SUCCESS with {m}: {resp.text.strip()}")
            return m
        except Exception as e:
            print(f"FAILED with {m}: {e}")

if __name__ == "__main__":
    test_38()
