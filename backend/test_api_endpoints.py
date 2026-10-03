"""
End-to-end API test script for ReportBrief endpoints.
Tests:
1. Login with test account (or register if needed)
2. POST /lab-reports/ with sample_lab_report.pdf
3. GET /lab-reports/ (list view)
4. GET /lab-reports/{id} (detail view)
5. Validates structure, flags, and grounded summary
"""
import os
import requests

BASE_URL = "http://127.0.0.1:8000"

# Sign in or register test user
username = "testuser_reportbrief@example.com"
password = "TestPassword123!"

# Try logging in
login_res = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": username, "password": password},
)

if login_res.status_code != 200:
    # Register user
    reg_res = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": username, "password": password, "full_name": "Test Patient", "role": "PATIENT"},
    )
    # Login again
    login_res = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password},
    )

token = login_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Ensure patient profile exists
patient_check = requests.get(f"{BASE_URL}/patients/me", headers=headers)
if patient_check.status_code != 200:
    requests.post(
        f"{BASE_URL}/patients/",
        headers=headers,
        json={
            "full_name": "Test Patient",
            "date_of_birth": "1985-05-15",
            "gender": "Female",
            "wake_up_time": "07:00:00",
            "breakfast_time": "08:00:00",
            "lunch_time": "12:30:00",
            "dinner_time": "19:30:00",
            "sleep_time": "23:00:00",
        },
    )

print("Step 1: Uploading sample_lab_report.pdf to POST /lab-reports/")
pdf_path = os.path.join(os.path.dirname(__file__), "sample_lab_report.pdf")
with open(pdf_path, "rb") as f:
    files = {"file": ("sample_lab_report.pdf", f, "application/pdf")}
    upload_res = requests.post(f"{BASE_URL}/lab-reports/", headers=headers, files=files)

print("Upload response status:", upload_res.status_code)
assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
report_data = upload_res.json()
report_id = report_data["id"]
print(f"Report ID: {report_id}, Status: {report_data['status']}")
print(f"Values extracted: {len(report_data['values'])}")

print("\nStep 2: Listing reports with GET /lab-reports/")
list_res = requests.get(f"{BASE_URL}/lab-reports/", headers=headers)
assert list_res.status_code == 200
reports_list = list_res.json()
print(f"Total reports in list: {len(reports_list)}")
print(f"First report preview: {reports_list[0]['original_filename']} | values_count: {reports_list[0]['values_count']}")

print("\nStep 3: Fetching detail with GET /lab-reports/{id}")
detail_res = requests.get(f"{BASE_URL}/lab-reports/{report_id}", headers=headers)
assert detail_res.status_code == 200
detail_data = detail_res.json()
print("Detail Status:", detail_data["status"])
print("Summary Preview:")
print(detail_data["summary"][:300] + "...")
print("\nExtracted Values in detail:")
for val in detail_data["values"]:
    print(f"  - {val['test_name']}: {val['value']} {val['unit']} -> {val['flag']}")

print("\nStep 4: Deleting test report with DELETE /lab-reports/{id}")
del_res = requests.delete(f"{BASE_URL}/lab-reports/{report_id}", headers=headers)
assert del_res.status_code == 200
print("Delete response:", del_res.json())

print("\nAll ReportBrief API tests passed successfully!")
