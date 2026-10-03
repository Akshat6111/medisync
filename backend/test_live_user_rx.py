import httpx
from app.auth.jwt import create_access_token
from app.db.database import SessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.medication import Medication
from app.models.medication_log import MedicationLog
from app.models.lab_report import LabReport
from app.models.cycle import CycleLog
from app.models.drug_interaction import DrugInteraction

def test_live_user_rx():
    db = SessionLocal()
    user = db.query(User).first()
    db.close()
    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    with open("user_prescription.jpg", "rb") as f:
        files = {"file": ("user_prescription.jpg", f, "image/jpeg")}
        resp = httpx.post(
            "http://127.0.0.1:8000/prescriptions/parse",
            files=files,
            headers=headers,
            timeout=30.0,
        )

    print(f"HTTP Status: {resp.status_code}")
    data = resp.json()
    print(f"Success: {data.get('success')}, Total Found: {data.get('total_found')}")
    for c in data.get("candidates", []):
        print(f"  - {c['matched_drug_name']} ({c['dosage_amount']} {c['dosage_unit']}) {c['frequency_per_day']}x daily {c['suggested_times']} -> {c['match_confidence']}%")

if __name__ == "__main__":
    test_live_user_rx()
