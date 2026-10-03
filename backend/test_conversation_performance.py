import sys
import io
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.ai.service import _SESSION_CONTEXT_CACHE, clear_session_cache

db = SessionLocal()
user = db.query(User).first()
if not user:
    user = User(id="00000000-0000-0000-0000-000000000001", email="test@medisync.ai", full_name="Test Patient")
db.close()

app.dependency_overrides[get_current_user] = lambda: user
client = TestClient(app)

session_id = f"test-session-{int(time.time())}"
clear_session_cache(session_id=session_id, user_id=user.id)

conversation_script = [
    "What medications am I currently taking?",
    "When should I take my first dose of the day?",
    "What is Ozotel 40 used for?",
    "Does Ozotel 40 interact with any of my current medications?",
    "What are common side effects of Ozotel 40?",
    "Can it cause dizziness or low blood pressure?",
    "What should I do if I experience mild dizziness?",
    "Should I take it in the morning or at night?",
    "Can you summarize the advice you gave me earlier about Ozotel 40?",
    "Thank you, is there any final precaution I should keep in mind?",
]

messages_state = []
timings = []
payload_stats = []

print("=" * 80)
print("STARTING 10-MESSAGE MULTI-TURN HEALTH ASSISTANT PERFORMANCE TEST")
print(f"Session ID: {session_id}")
print("=" * 80)

for i, query in enumerate(conversation_script, start=1):
    # Cap to last 6 messages (matching frontend logic)
    history_payload = messages_state[-6:]
    
    # Calculate uncapped history for comparison
    uncapped_history = list(messages_state)
    
    req_body = {
        "message": query,
        "history": history_payload,
        "session_id": session_id,
    }
    
    uncapped_body = {
        "message": query,
        "history": uncapped_history,
        "session_id": session_id,
    }
    
    body_json = json.dumps(req_body)
    uncapped_json = json.dumps(uncapped_body)
    
    payload_stats.append({
        "turn": i,
        "history_count_capped": len(history_payload),
        "payload_bytes_capped": len(body_json),
        "history_count_uncapped": len(uncapped_history),
        "payload_bytes_uncapped": len(uncapped_json),
    })

    t_start = time.perf_counter()
    resp = client.post("/ai/chat", json=req_body)
    duration = time.perf_counter() - t_start
    timings.append((i, query, duration, resp.status_code))

    assert resp.status_code == 200, f"Error at turn {i}: {resp.status_code} {resp.text}"
    answer = resp.json()["response"]

    # Append to state
    messages_state.append({"role": "user", "content": query})
    messages_state.append({"role": "assistant", "content": answer})

    cache_key = f"{user.id}:{session_id}"
    cache_status = "HIT (Pinecone skipped)" if cache_key in _SESSION_CONTEXT_CACHE and i > 1 else "MISS (Retrieved & Cached)"
    print(f"Message #{i:2d} | Time: {duration:5.2f}s | Cache: {cache_status:24s} | History Sent: {len(history_payload):2d} msgs ({len(body_json):5d} B) | Query: '{query[:35]}...'", flush=True)
    time.sleep(2.5)


print("\n" + "=" * 80, flush=True)
print("PAYLOAD ANALYSIS & COMPARISON (MESSAGE #1 vs MESSAGE #6 vs MESSAGE #10)", flush=True)
print("=" * 80, flush=True)

for p in payload_stats:
    if p["turn"] in (1, 6, 10):
        print(f"Message #{p['turn']}:", flush=True)
        print(f"  - Capped (Actual sent):   {p['history_count_capped']} history msgs | {p['payload_bytes_capped']} bytes", flush=True)
        print(f"  - Uncapped (Before fix): {p['history_count_uncapped']} history msgs | {p['payload_bytes_uncapped']} bytes", flush=True)
        if p["turn"] > 1:
            saved_bytes = p['payload_bytes_uncapped'] - p['payload_bytes_capped']
            print(f"  - Reduction: {saved_bytes} bytes saved ({(saved_bytes / p['payload_bytes_uncapped']) * 100:.1f}% reduction)", flush=True)

print("\n" + "=" * 80, flush=True)
print("RESPONSE TIMES REPORT (MESSAGES 1, 5, AND 10)", flush=True)
print("=" * 80, flush=True)
t1 = timings[0][2]
t5 = timings[4][2]
t10 = timings[9][2]
avg_time = sum(t[2] for t in timings) / len(timings)

print(f"Message #1:  {t1:.2f} seconds", flush=True)
print(f"Message #5:  {t5:.2f} seconds", flush=True)
print(f"Message #10: {t10:.2f} seconds", flush=True)
print(f"10-turn Average Response Time: {avg_time:.2f} seconds", flush=True)
print(f"Flatness Check: Message #10 ({t10:.2f}s) vs Message #5 ({t5:.2f}s) vs Message #1 ({t1:.2f}s)", flush=True)
print("=" * 80, flush=True)

