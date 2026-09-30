import sys
import json
import logging
from backend.rag.rag_engine import RAGEngine

logging.basicConfig(level=logging.INFO)

rag = RAGEngine(data_dir="./data")
query = "What information do people actually remember about a photo?"

print("--- TESTING RAG QUERY ---")
res = rag.ask(query)
print("\n--- RESULT ---")
print("Status:", res.get("status"))
print("Answer:", res.get("answer"))
print("Citations:")
for idx, c in enumerate(res.get("citations", []), 1):
    print(f" Quote {idx} [{c['source']}]: {c['quote']}")
