import sys
import urllib.request
import json
import time

sys.stdout.reconfigure(encoding='utf-8')

url = "http://127.0.0.1:8000/api/chat"

# Turn 1
payload1 = {
    "prompt": "Which photo types fail search most frequently?",
    "session_id": "test_session_101",
    "chat_history": []
}

req1 = urllib.request.Request(url, data=json.dumps(payload1).encode('utf-8'), headers={'Content-Type': 'application/json'})
res1 = json.loads(urllib.request.urlopen(req1).read().decode('utf-8'))

print("=== TURN 1 RESPONSE ===")
print("Answer:", res1.get('answer'))

# Turn 2 (Follow-up relying on memory)
history = [
    {"role": "user", "content": payload1["prompt"]},
    {"role": "assistant", "content": res1.get('answer')}
]

payload2 = {
    "prompt": "What about receipts specifically?",
    "session_id": "test_session_101",
    "chat_history": history
}

req2 = urllib.request.Request(url, data=json.dumps(payload2).encode('utf-8'), headers={'Content-Type': 'application/json'})
res2 = json.loads(urllib.request.urlopen(req2).read().decode('utf-8'))

print("\n=== TURN 2 RESPONSE (FOLLOW-UP WITH MEMORY) ===")
print("Answer:", res2.get('answer'))

# Check for raw cluster_01 or (cluster 01) formatting errors
has_cluster_tag = "cluster" in res2.get('answer', '').lower()
print(f"\nContains raw cluster tags: {has_cluster_tag}")
