import json

data = json.load(open('data/tag_data_old_unique.json', 'r', encoding='utf-8'))

# Pick 8 diverse records (including relevant=True and relevant=False)
samples = []
rel_true = [r for r in data if r['taxonomy'].get('relevant') == True]
rel_false = [r for r in data if r['taxonomy'].get('relevant') == False]

samples.extend(rel_true[:4])
samples.extend(rel_false[:4])

with open('scratch/step1_8_samples.json', 'w', encoding='utf-8') as f:
    json.dump(samples, f, indent=2, ensure_ascii=False)

print(f"Extracted {len(samples)} sample records to scratch/step1_8_samples.json")
