import os
from groq import Groq

with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

groq_key = os.environ.get('GROQ_API_KEY')
print("Groq Key:", groq_key[:15] if groq_key else "None")

client = Groq(api_key=groq_key)
try:
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Respond with JSON: {\"status\": \"ok\"}"}],
        response_format={"type": "json_object"}
    )
    print("Groq response successful:")
    print(resp.choices[0].message.content)
except Exception as e:
    print("Groq Error:", type(e).__name__, e)
