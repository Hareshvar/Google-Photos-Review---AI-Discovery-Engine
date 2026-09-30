import os
from dotenv import load_dotenv
load_dotenv()
from google import genai

def test_35_lite():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    try:
        resp = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents="Respond with 1 word."
        )
        print("SUCCESS with gemini-3.5-flash-lite:", resp.text.strip())
    except Exception as e:
        print("FAILED gemini-3.5-flash-lite:", e)

if __name__ == "__main__":
    test_35_lite()
