"""
Comprehensive verification script for CycleSync backend endpoints,
specifically validating the 3-cycle anomaly guardrail and prediction engine.
"""
from datetime import date, timedelta
import requests

BASE_URL = "http://127.0.0.1:8000"

# Sign in with test user
username = "testuser_reportbrief@example.com"
password = "TestPassword123!"

login_res = requests.post(f"{BASE_URL}/auth/login", data={"username": username, "password": password})
token = login_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("Cleaning any existing cycle logs for test patient...")
existing = requests.get(f"{BASE_URL}/cycles/", headers=headers).json()
for item in existing:
    requests.delete(f"{BASE_URL}/cycles/{item['id']}", headers=headers)

# -------------------------------------------------------------
# TEST 1: Exactly 1 cycle logged
# -------------------------------------------------------------
print("\n--- TEST 1: Single Cycle Logged ---")
res1 = requests.post(
    f"{BASE_URL}/cycles/",
    headers=headers,
    json={"start_date": "2026-05-01", "end_date": "2026-05-06"},
)
assert res1.status_code == 201, f"Failed log 1: {res1.text}"
pred1 = requests.get(f"{BASE_URL}/cycles/prediction", headers=headers).json()
print("1 Log Prediction Response:", pred1)
assert pred1["total_cycles_logged"] == 1
assert pred1["average_cycle_length"] is None
assert pred1["anomaly_flag"] is False
assert pred1["current_cycle_day"] is not None
print("[OK] Test 1 passed: 1 cycle returns no average and anomaly_flag=False.")

# -------------------------------------------------------------
# TEST 2: Exactly 2 cycles logged (THE 3-CYCLE GUARDRAIL CHECK)
# -------------------------------------------------------------
print("\n--- TEST 2: Exactly 2 Cycles Logged (Guardrail Validation) ---")
# Cycle 2 start is May 29 (28-day cycle)
res2 = requests.post(
    f"{BASE_URL}/cycles/",
    headers=headers,
    json={"start_date": "2026-05-29", "end_date": "2026-06-03"},
)
assert res2.status_code == 201
pred2 = requests.get(f"{BASE_URL}/cycles/prediction", headers=headers).json()
print("2 Logs Prediction Response:", pred2)
assert pred2["total_cycles_logged"] == 2
assert pred2["average_cycle_length"] == 28.0
assert pred2["std_deviation"] == 0.0
# CRITICAL SPEC CHECK: Must NOT trigger anomaly on 2 cycles
assert pred2["anomaly_flag"] is False, f"Anomaly flagged prematurely with only 2 cycles: {pred2}"
assert pred2["anomaly_reason"] is None
assert pred2["predicted_next_start"] == "2026-06-26"
print("[OK] Test 2 passed: 2 cycles computed average=28.0d and STRICTLY preserved anomaly_flag=False (guardrail hold).")

# -------------------------------------------------------------
# TEST 3: Add 3rd cycle that is wildly different (40 days later)
# -------------------------------------------------------------
print("\n--- TEST 3: Add 3rd Wildly Different Cycle (40-day interval) ---")
# Cycle 3 start is July 8 (40 days after May 29)
res3 = requests.post(
    f"{BASE_URL}/cycles/",
    headers=headers,
    json={"start_date": "2026-07-08", "end_date": "2026-07-13"},
)
assert res3.status_code == 201
pred3 = requests.get(f"{BASE_URL}/cycles/prediction", headers=headers).json()
print("3 Logs Prediction Response:", pred3)
assert pred3["total_cycles_logged"] == 3
# With intervals [28, 40]: average = 34.0, stdev = 8.48
# Last interval = 40. diff = |40 - 34| = 6.
print(f"Average: {pred3['average_cycle_length']}, SD: {pred3['std_deviation']}, Anomaly: {pred3['anomaly_flag']}")

# Now let's test a true > 1.5 SD outlier:
# Let's add standard baseline cycles:
# Cycle 4: August 5 (28 days later)
# Cycle 5: September 2 (28 days later)
# Cycle 6: October 18 (46 days later -> huge outlier!)
print("\n--- TEST 3B: Explicit Outlier (> 1.5 SD) with 4+ cycles ---")
requests.post(f"{BASE_URL}/cycles/", headers=headers, json={"start_date": "2026-08-05", "end_date": "2026-08-10"})
requests.post(f"{BASE_URL}/cycles/", headers=headers, json={"start_date": "2026-09-02", "end_date": "2026-09-07"})
pred_steady = requests.get(f"{BASE_URL}/cycles/prediction", headers=headers).json()
print("Steady baseline prediction:", pred_steady)
assert pred_steady["anomaly_flag"] is False, "Unexpected anomaly on steady cycles"

# Now post a 46-day cycle:
res_outlier = requests.post(f"{BASE_URL}/cycles/", headers=headers, json={"start_date": "2026-10-18", "end_date": "2026-10-23"})
pred_outlier = requests.get(f"{BASE_URL}/cycles/prediction", headers=headers).json()
print("Outlier prediction response:", pred_outlier)
assert pred_outlier["anomaly_flag"] is True, "Expected anomaly flag to be TRUE for 46-day cycle"
assert pred_outlier["anomaly_reason"] is not None
print(f"[OK] Test 3B passed: Anomaly triggered accurately! Reason: {pred_outlier['anomaly_reason']}")

# -------------------------------------------------------------
# TEST 4: Update & Delete
# -------------------------------------------------------------
print("\n--- TEST 4: PUT update and DELETE ---")
outlier_id = res_outlier.json()["id"]
# Update end_date
put_res = requests.put(f"{BASE_URL}/cycles/{outlier_id}", headers=headers, json={"end_date": "2026-10-24"})
assert put_res.status_code == 200
assert put_res.json()["end_date"] == "2026-10-24"
print("[OK] PUT /cycles/{id} succeeded.")

del_res = requests.delete(f"{BASE_URL}/cycles/{outlier_id}", headers=headers)
assert del_res.status_code == 200
print("[OK] DELETE /cycles/{id} succeeded.")

print("\nALL CYCLESYNC TESTS PASSED!")
