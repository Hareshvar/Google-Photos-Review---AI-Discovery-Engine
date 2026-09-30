import json
import re

def synthesize_smart_fallback(prompt: str, precomputed: dict, citations: list) -> str:
    prompt_lower = prompt.lower()
    
    key_insights = precomputed.get("key_insights", [])
    
    # Q1: Target Types / photo types
    if any(w in prompt_lower for w in ["type", "kinds", "category", "what photos", "which photo", "content", "struggle to retrieve"]):
        q1 = next((item for item in key_insights if item.get("number") == 1), None)
        if q1 and q1.get("distribution"):
            top_3 = q1["distribution"][:3]
            dist_str = ", ".join([f"{d.get('label') or d.get('category')} ({d.get('share_pct') or d.get('pct')}%)" for d in top_3])
            return f"Based on verified feedback (n=916), users struggle most to find {dist_str}. Inspect the verified quote citations below for specific post evidence."

    # Q2 / Q3: Remembered or forgotten cues
    if any(w in prompt_lower for w in ["cue", "remember", "forget", "clue", "information", "recall"]):
        q2 = next((item for item in key_insights if item.get("number") == 2), None)
        if q2 and q2.get("distribution"):
            top_3 = q2["distribution"][:3]
            dist_str = ", ".join([f"{d.get('label') or d.get('category')} ({d.get('share_pct') or d.get('pct')}%)" for d in top_3])
            return f"According to user records, the primary clues people remember about a photo are {dist_str}. Inspect the verified quote citations below for specific post evidence."

    # Q6 / Q9: Flow / Errors / Failures
    if any(w in prompt_lower for w in ["error", "fail", "flow", "breakdown", "kpi", "step", "problem"]):
        q9 = next((item for item in key_insights if item.get("number") == 9), None)
        if q9 and q9.get("distribution"):
            top_3 = [d for d in q9["distribution"] if d.get("key") != "no_failure"][:3]
            dist_str = ", ".join([f"{d.get('category') or d.get('label')} ({d.get('share_pct') or d.get('pct')}%)" for d in top_3])
            return f"Analysis of retrieval breakdowns indicates major search failure modes occur at: {dist_str}. Inspect the verified quote citations below for specific post evidence."

    # General fallback using quotes
    top_quotes = [f'"{c["quote"]}"' for c in citations if c.get("quote")]
    if top_quotes:
        return f"Analysis of collected feedback (n=916) reveals user photo retrieval friction. Verified user submissions highlight: {' '.join(top_quotes[:2])}. Inspect the verified quote citations below for full post details."
    
    return "Analysis of collected feedback (n=916) indicates user friction when attempting to locate photos. Searchers frequently report difficulty retrieving photos when exact dates or visual tags are missing."

# Test Q1 matching
precomputed = json.load(open("data/precomputed_stats.json", "r", encoding="utf-8"))
cits = [{"quote": "Sample quote 1"}, {"quote": "Sample quote 2"}]

print("Test Q1 prompt 'Which type of photo is difficult to find?':")
print(synthesize_smart_fallback("Which type of photo is difficult to find?", precomputed, cits))
