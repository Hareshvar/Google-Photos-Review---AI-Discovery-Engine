import os
import json
from dotenv import load_dotenv
load_dotenv()

from backend.analysis.summary_writer import SummaryWriter

writer = SummaryWriter()
print("Groq client initialized:", bool(writer._groq_client))
print("Gemini client initialized:", bool(writer._gemini_client))

with open('data/precomputed_stats.json', encoding='utf-8') as f:
    stats = json.load(f)

insights = stats.get('key_insights', [])
updated_cards = writer.write_summaries(insights)

for card in updated_cards[:3]:
    print(f"\n==========================================")
    print(f"Question {card.get('number')}: {card.get('question')}")
    print(f"Summary:\n{card.get('summary')}")
