from datetime import date
import requests

BASE = "http://127.0.0.1:8000"
res = requests.post(f"{BASE}/auth/login", data={"username": "testuser_reportbrief@example.com", "password": "TestPassword123!"})
token = res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Clean existing
existing = requests.get(f"{BASE}/cycles/", headers=headers).json()
for c in existing:
    requests.delete(f"{BASE}/cycles/{c['id']}", headers=headers)

# Current date in simulation context is Sep 8, 2026.
# Cycle 1: July 12 - July 17
# Cycle 2: Aug 10 - Aug 15 (29-day cycle)
# Cycle 3: Sep 8 - Ongoing (29-day cycle, starts today!)
requests.post(f"{BASE}/cycles/", headers=headers, json={"start_date": "2026-07-12", "end_date": "2026-07-17"})
requests.post(f"{BASE}/cycles/", headers=headers, json={"start_date": "2026-08-10", "end_date": "2026-08-15"})
requests.post(f"{BASE}/cycles/", headers=headers, json={"start_date": "2026-09-08"})

pred = requests.get(f"{BASE}/cycles/prediction", headers=headers).json()
print("Initial cycles loaded successfully!")
print("Current Cycle Day:", pred["current_cycle_day"])
print("Average Cycle Length:", pred["average_cycle_length"], "days")
print("Predicted Next Start:", pred["predicted_next_start"])
print("Predicted Window:", pred["predicted_window_start"], "to", pred["predicted_window_end"])
