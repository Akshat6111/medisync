import sys
import io

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.medication import Medication
from app.auth.dependencies import get_current_user

db = SessionLocal()
user = db.query(User).first()
if not user:
    # Create or use fallback mock user
    print("No user in DB, using fallback mock user")
    user = User(id="00000000-0000-0000-0000-000000000001", email="test@medisync.ai", full_name="Test Patient")

app.dependency_overrides[get_current_user] = lambda: user
client = TestClient(app)

print("=" * 70)
print("TEST CASE (a): Question about user's own logged medications")
print("=" * 70)
query_a = "What medications am I currently taking?"
resp_a = client.post("/ai/chat", json={"message": query_a, "history": []})
assert resp_a.status_code == 200, f"Error {resp_a.status_code}: {resp_a.text}"
answer_a = resp_a.json()["response"]
print(f"User: {query_a}\n")
print(f"MediSync AI:\n{answer_a}\n")

print("=" * 70)
print("TEST CASE (b): General medical knowledge ('what is Ozotel 40')")
print("=" * 70)
query_b = "what is Ozotel 40 used for"
resp_b = client.post("/ai/chat", json={"message": query_b, "history": []})
assert resp_b.status_code == 200, f"Error {resp_b.status_code}: {resp_b.text}"
answer_b = resp_b.json()["response"]
print(f"User: {query_b}\n")
print(f"MediSync AI:\n{answer_b}\n")

print("=" * 70)
print("TEST CASE (c): Multi-turn conversation with memory")
print("=" * 70)
turn1_q = "what is Ozotel 40 used for"
turn1_a = answer_b

turn2_q = "What are its common side effects, and should I take it with or without food?"
history_payload = [
    {"role": "user", "content": turn1_q},
    {"role": "assistant", "content": turn1_a},
]
resp_c = client.post("/ai/chat", json={"message": turn2_q, "history": history_payload})
assert resp_c.status_code == 200, f"Error {resp_c.status_code}: {resp_c.text}"
answer_c = resp_c.json()["response"]
print(f"Turn 1 User: {turn1_q}")
print(f"Turn 1 Assistant: (Answered about Ozotel 40)\n")
print(f"Turn 2 User (Follow-up): {turn2_q}\n")
print(f"Turn 2 Assistant (Multi-turn response):\n{answer_c}\n")

print("=" * 70)
print("ALL 3 TEST CASES COMPLETED SUCCESSFULLY!")
print("=" * 70)

db.close()
