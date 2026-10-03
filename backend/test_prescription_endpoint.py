import httpx
from app.auth.jwt import create_access_token
from app.db.database import SessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.lab_report import LabReport
from app.models.cycle import CycleLog
from app.models.medication import Medication
from app.models.medication_log import MedicationLog
from app.models.drug_interaction import DrugInteraction

def test_live_prescription_endpoint():
    db = SessionLocal()
    user = db.query(User).first()
    db.close()

    if not user:
        print("No user found in DB to test API.")
        return

    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    with open("sample_prescription.pdf", "rb") as f:
        files = {"file": ("sample_prescription.pdf", f, "application/pdf")}
        resp = httpx.post(
            "http://127.0.0.1:8000/prescriptions/parse",
            files=files,
            headers=headers,
            timeout=15.0,
        )

    print(f"API Response Status: {resp.status_code}")
    print(f"Response text: {resp.text}")
    if resp.status_code != 200:
        return
    data = resp.json()
    print(f"Success: {data.get('success')}, Candidates: {len(data.get('candidates', []))}")
    for c in data.get("candidates", []):
        print(f"  - {c['matched_drug_name']} ({c['dosage_amount']} {c['dosage_unit']}, Freq: {c['frequency_per_day']}, Times: {c['suggested_times']})")
        print(f"    Confidence: {c['match_confidence']}%, Needs Review: {c['needs_review']}")

if __name__ == "__main__":
    test_live_prescription_endpoint()
