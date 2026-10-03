import sys
import io
import time
import datetime
import requests

# Fix encoding for Windows console
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"
timestamp = int(time.time())
test_email = f"journey_patient_{timestamp}@medisync.ai"
test_password = "SecurePassword123!"
test_name = "Journey Tester"

print("=" * 80)
print("STARTING FULL END-TO-END LOCAL USER-JOURNEY TEST (IN ONE CONTINUOUS SESSION)")
print(f"Target Server: {BASE_URL}")
print(f"Test User: {test_email}")
print("=" * 80)

# STEP 1: Register
print("\n[STEP 1/10] Registering new user...")
reg_res = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "email": test_email,
        "password": test_password,
        "full_name": test_name,
    },
)
print(f"Register status: {reg_res.status_code}")
assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
user_id = reg_res.json()["id"]
print(f"Registered User ID: {user_id}")

# STEP 2: Login
print("\n[STEP 2/10] Logging in...")
login_res = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": test_email, "password": test_password},
)
print(f"Login status: {login_res.status_code}")
assert login_res.status_code == 200, f"Login failed: {login_res.text}"
token = login_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Obtained JWT Bearer token.")

# STEP 2b: Create Patient Profile
print("\n[STEP 2b] Setting up Patient Routine & Demographics...")
patient_res = requests.post(
    f"{BASE_URL}/patients/",
    headers=headers,
    json={
        "full_name": test_name,
        "date_of_birth": "1995-06-15",
        "gender": "female",
        "wake_up_time": "07:00",
        "breakfast_time": "08:30",
        "lunch_time": "13:30",
        "dinner_time": "20:30",
        "sleep_time": "23:00",
        "medical_conditions": "Mild Hypertension",
        "allergies": "Penicillin",
    },
)
print(f"Patient creation status: {patient_res.status_code}")
assert patient_res.status_code == 201, f"Patient profile creation failed: {patient_res.text}"
patient_id = patient_res.json()["id"]
print(f"Patient ID: {patient_id}")

# STEP 3: Add Medication (automatic CSP mode)
print("\n[STEP 3/10] Adding medication via automatic CSP mode...")
today_str = datetime.date.today().isoformat()
med_res = requests.post(
    f"{BASE_URL}/medications/",
    headers=headers,
    json={
        "name": "Metformin",
        "dosage_amount": 500,
        "dosage_unit": "mg",
        "frequency_per_day": 2,
        "duration_days": 14,
        "route": "oral",
        "with_food": True,
        "empty_stomach": False,
        "bedtime_only": False,
        "start_date": today_str,
        "notes": "Take with meals",
    },
)
print(f"Medication creation status: {med_res.status_code}")
assert med_res.status_code == 201, f"Medication add failed: {med_res.text}"
med_id = med_res.json()["id"]
print(f"Medication ID: {med_id} ({med_res.json()['name']})")

# STEP 4: Check Schedule
print("\n[STEP 4/10] Checking Schedule (CSP Solver)...")
sched_res = requests.get(f"{BASE_URL}/schedule/me", headers=headers)
print(f"Schedule status: {sched_res.status_code}")
assert sched_res.status_code == 200, f"Schedule check failed: {sched_res.text}"
sched_data = sched_res.json()
print(f"Schedule generated: Success={sched_data.get('success')}, Total Scheduled Doses={len(sched_data.get('schedule', []))}")
for dose in sched_data.get("schedule", []):
    print(f"  • {dose['scheduled_time']} - {dose['medication_name']} (Dose #{dose['dose_index'] + 1})")

# STEP 5: Scan Prescription with RxParse
print("\n[STEP 5/10] Scanning Prescription with RxParse...")
with open("user_prescription.jpg", "rb") as f:
    rx_res = requests.post(
        f"{BASE_URL}/prescriptions/parse",
        headers=headers,
        files={"file": ("user_prescription.jpg", f, "image/jpeg")},
        timeout=30.0,
    )
print(f"RxParse status: {rx_res.status_code}")
assert rx_res.status_code == 200, f"RxParse failed: {rx_res.text}"
rx_data = rx_res.json()
print(f"RxParse Result: Success={rx_data.get('success')}, Extracted Candidates={len(rx_data.get('candidates', []))}")
for c in rx_data.get("candidates", [])[:3]:
    print(f"  • Extracted: {c['matched_drug_name']} ({c['dosage_amount']} {c['dosage_unit']}) - Confidence: {c['match_confidence']}%")

# STEP 6: Upload Lab Report to ReportBrief
print("\n[STEP 6/10] Uploading Lab Report to ReportBrief...")
with open("sample_lab_report.pdf", "rb") as f:
    report_res = requests.post(
        f"{BASE_URL}/lab-reports/",
        headers=headers,
        files={"file": ("sample_lab_report.pdf", f, "application/pdf")},
        timeout=30.0,
    )
print(f"ReportBrief status: {report_res.status_code}")
assert report_res.status_code == 201, f"ReportBrief failed: {report_res.text}"
report_data = report_res.json()
print(f"Report ID: {report_data.get('id')}")
print(f"Extracted Test Values Count: {len(report_data.get('values', []))}")
print(f"AI Plain-Language Summary Length: {len(report_data.get('summary', ''))} chars")
print("Summary Preview:")
print("\n".join(report_data.get("summary", "").splitlines()[:6]))

# STEP 7: Log a Cycle Entry in CycleSync
print("\n[STEP 7/10] Logging Cycle in CycleSync...")
cycle_res = requests.post(
    f"{BASE_URL}/cycles/",
    headers=headers,
    json={
        "start_date": "2026-09-01",
        "end_date": "2026-09-06",
    },
)
print(f"CycleSync log status: {cycle_res.status_code}")
assert cycle_res.status_code == 201, f"CycleSync log failed: {cycle_res.text}"
pred_res = requests.get(f"{BASE_URL}/cycles/prediction", headers=headers)
print(f"Cycle Prediction status: {pred_res.status_code}, Current Day: {pred_res.json().get('current_cycle_day')}")

# STEP 8: Check Nearby Hospitals
print("\n[STEP 8/10] Finding Nearby Hospitals...")
hosp_res = requests.get(
    f"{BASE_URL}/hospitals/nearby",
    params={"lat": 28.6139, "lng": 77.2090, "radius": 3000},
)
print(f"HospitalFinder status: {hosp_res.status_code}")
assert hosp_res.status_code == 200, f"HospitalFinder failed: {hosp_res.text}"
hospitals = hosp_res.json()
print(f"Nearby Hospitals Found: {len(hospitals)}")
if hospitals:
    print(f"  • Nearest: {hospitals[0]['name']} ({hospitals[0]['distance_km']} km away)")

# STEP 9: Search GenericFinder
print("\n[STEP 9/10] Searching GenericFinder...")
gf_res = requests.get(
    f"{BASE_URL}/generic-finder/search",
    params={"query": "Dolo 650"},
)
print(f"GenericFinder status: {gf_res.status_code}")
assert gf_res.status_code == 200, f"GenericFinder search failed: {gf_res.text}"
gf_data = gf_res.json()
print(f"GenericFinder Matched: '{gf_data.get('query_matched_to')}' -> Active Salt: '{gf_data.get('generic_name')}'")
results = gf_data.get("results", [])
assert len(results) > 0, "No results returned"
assert results[0].get("is_searched_medicine") is True, "Position #1 must be the searched medicine!"
print(f"  • Position #1 Pinned Searched Medicine: '{results[0]['brand_name']}' (Rs. {results[0]['price']})")
if len(results) > 1:
    print(f"  • Position #2 Cheapest Generic Substitute: '{results[1]['brand_name']}' (Rs. {results[1]['price']})")
print(f"Estimated Savings: {gf_data.get('estimated_savings_percent')}%")

# STEP 10: Ask RAG Assistant a Question
print("\n[STEP 10/10] Asking MediSync RAG Health Assistant...")
t_chat0 = time.time()
chat_res = requests.post(
    f"{BASE_URL}/ai/chat",
    headers=headers,
    json={"message": "What medications am I currently taking, and should I take them with food?"},
    timeout=20.0,
)
t_chat1 = time.time()
print(f"Chat status: {chat_res.status_code} | Latency: {t_chat1 - t_chat0:.2f}s")
assert chat_res.status_code == 200, f"Chat failed: {chat_res.text}"
chat_answer = chat_res.json()["response"]
print("\nAssistant Response:")
print(chat_answer)

# Assert grounding
assert "metformin" in chat_answer.lower(), "Assistant response should reference the user's Metformin prescription!"

print("\n" + "=" * 80)
print("SUCCESS: COMPLETE USER JOURNEY COMPLETED WITH ZERO ERRORS OR REGRESSIONS!")
print("=" * 80)
