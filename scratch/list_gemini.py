import os
from dotenv import load_dotenv
load_dotenv()
from google import genai

def list_gemini():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    print("Testing Gemini models...")
    for m_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-3.6-flash"]:
        try:
            resp = client.models.generate_content(
                model=m_name,
                contents="Hello, 1 word response."
            )
            print(f"SUCCESS with '{m_name}': {resp.text.strip()}")
            return m_name
        except Exception as e:
            print(f"FAILED with '{m_name}': {e}")

if __name__ == "__main__":
    list_gemini()
