import os
import json
import math
import re
from collections import Counter
from typing import List, Dict, Any

class LightVectorSearch:
    """Ultra-lightweight TF-IDF Vector Search (<5MB RAM) for low-memory cloud hosts (e.g. Render 512MB free tier)."""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        mapped_path = os.path.join(data_dir, "final_tagged_dataset_mapped.json")
        final_path = os.path.join(data_dir, "final_tagged_dataset.json")
        if os.path.exists(mapped_path):
            self.tagged_file = mapped_path
        elif os.path.exists(final_path):
            self.tagged_file = final_path
        else:
            self.tagged_file = os.path.join(data_dir, "tagged_posts.json")
            
        self.documents: List[Dict[str, Any]] = []
        self._load_and_index()

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b[a-z0-9]+\b', text.lower())

    def _load_and_index(self):
        if not os.path.exists(self.tagged_file):
            return

        with open(self.tagged_file, "r", encoding="utf-8") as f:
            tagged_data = json.load(f)

        relevant_posts = [p for p in tagged_data if p.get("taxonomy", {}).get("relevant") is True]
        if not relevant_posts:
            relevant_posts = tagged_data[:916]

        doc_count = len(relevant_posts)
        df = Counter()

        for p in relevant_posts:
            title = p.get("title", "")
            raw_text = p.get("raw_text", "")
            tax = p.get("taxonomy", {})
            quote = tax.get("quote", title[:100] if title else raw_text[:100])
            
            full_text = f"{title} {raw_text} {quote} {' '.join(tax.get('cues_remembered', []))} {tax.get('primary_cue', '')} {tax.get('target_type', '')}"
            tokens = set(self._tokenize(full_text))
            
            for t in tokens:
                df[t] += 1

            self.documents.append({
                "post_id": p.get("post_id"),
                "source": p.get("source", "unknown"),
                "url": p.get("url") or "",
                "created_at": p.get("created_at", "2024-01-01"),
                "quote": quote,
                "quote_verified": tax.get("quote_verified", False),
                "target_type": tax.get("target_type", "other"),
                "failure_step": tax.get("failure_step", "no_or_wrong_results"),
                "matched_text": f"{title}\n{raw_text}".strip(),
                "tokens": self._tokenize(full_text),
                "token_counts": Counter(self._tokenize(full_text))
            })

        self.idf = {t: math.log((doc_count + 1) / (df[t] + 1)) + 1.0 for t in df}

    def query_similar(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        query_tokens = self._tokenize(query_text)
        if not query_tokens or not self.documents:
            return []

        q_tf = Counter(query_tokens)
        q_vec = {t: q_tf[t] * self.idf.get(t, 1.0) for t in q_tf}
        q_norm = math.sqrt(sum(v ** 2 for v in q_vec.values()))

        if q_norm == 0:
            return self.documents[:n_results]

        scored_docs = []
        for doc in self.documents:
            dot_product = 0.0
            d_counts = doc["token_counts"]
            for t, q_val in q_vec.items():
                if t in d_counts:
                    d_val = d_counts[t] * self.idf.get(t, 1.0)
                    dot_product += q_val * d_val

            d_norm = math.sqrt(sum((count * self.idf.get(t, 1.0)) ** 2 for t, count in d_counts.items()))
            sim = dot_product / (q_norm * d_norm) if (q_norm * d_norm) > 0 else 0.0

            scored_docs.append((sim, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for sim, doc in scored_docs[:n_results]:
            item = dict(doc)
            item["distance"] = round(1.0 - sim, 4)
            del item["tokens"]
            del item["token_counts"]
            results.append(item)

        return results

if __name__ == "__main__":
    search = LightVectorSearch(data_dir="./data")
    res = search.query_similar("What visual cues do users remember?")
    print(f"Retrieved {len(res)} matching posts.")
    for idx, r in enumerate(res, 1):
        print(f"[{idx}] {r['source']} | Quote: {r['quote']}")
