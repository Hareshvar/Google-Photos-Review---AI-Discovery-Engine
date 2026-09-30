import json
from dotenv import load_dotenv
load_dotenv()

from backend.rag.rag_engine import RAGEngine

rag = RAGEngine()

print("--- Test 1: Out-of-Scope Query ---")
res1 = rag.ask("Who is the PM of India?")
print(json.dumps(res1, indent=2))

print("\n--- Test 2: In-Scope Research Query ---")
res2 = rag.ask("What visual cues do users forget about a photo?")
print(json.dumps(res2, indent=2))
