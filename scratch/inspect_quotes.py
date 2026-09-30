import json

data = json.load(open('data/precomputed_stats.json', encoding='utf-8'))
insights = {card['id']: card for card in data.get('key_insights', [])}

for qid in ['q1', 'q2', 'q6']:
    card = insights.get(qid, {})
    quotes = card.get('example_quotes', [])
    print(f"\n=== {qid.upper()}: {card.get('question')} (n={card.get('evidence_n')}) ===")
    for idx, q in enumerate(quotes, 1):
        row = 1 if idx <= 2 else 2
        col = 1 if idx in (1, 3) else 2
        print(f"  [Row {row}, Col {col}] ({q.get('source')} | Post ID: {q.get('post_id')}): \"{q.get('quote')}\"")
