import sys
from app.ai.service import chat
from app.db.database import SessionLocal
from app.models.user import User

db = SessionLocal()
try:
    user = db.query(User).first()
    if not user:
        print("Skipped: No user found in database to run test_chat.")
    else:
        question = input("Ask: ") if sys.stdin.isatty() else "What are my medications?"
        answer = chat(query=question, db=db, current_user=user)
        print("\n")
        print(answer)
finally:
    db.close()