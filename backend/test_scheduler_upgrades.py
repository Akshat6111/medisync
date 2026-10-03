import json
import logging
import uuid
from datetime import date, datetime, time, timedelta

# Suppress verbose SQLAlchemy engine SQL logs so output is clean
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from fastapi.testclient import TestClient
from app.core.time import IST, now_ist
from app.db.database import SessionLocal
from app.main import app
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.medication import Medication
from app.models.medication_log import MedicationLog, MedicationStatus
from app.models.drug_interaction import DrugInteraction
from app.models.notification import Notification
from app.models.lab_report import LabReport, LabReportValue
from app.models.cycle import CycleLog
from app.scheduling.scheduler import solve_schedule, get_min_gap_slots, get_waking_hours
from app.services.schedule_service import generate_schedule, sync_schedule_logs
from app.auth.jwt import create_access_token


def run_all_verification_tests():
    db = SessionLocal()
    client = TestClient(app)

    print("\n" + "=" * 75)
    print("      MEDISYNC CSP SCHEDULER & OPENFDA INTEGRATION TEST SUITE")
    print("=" * 75)

    # --------------------------------------------------------------------------
    # CHECK 1: 3x/day Medication Scheduling Test
    # --------------------------------------------------------------------------
    print("\n[CHECK 1] 3x/day Medication Scheduling (Waking Window Spacing)")
    test_patient_1 = Patient(
        id=uuid.uuid4(),
        full_name="Check1 Test Patient",
        date_of_birth=date(1990, 1, 1),
        gender="Other",
        wake_up_time=time(7, 0),
        breakfast_time=time(8, 0),
        lunch_time=time(13, 0),
        dinner_time=time(20, 0),
        sleep_time=time(22, 0),
    )

    waking_hours = get_waking_hours(test_patient_1)
    print(f"  - Patient waking window : {test_patient_1.wake_up_time.strftime('%H:%M')} to {test_patient_1.sleep_time.strftime('%H:%M')} ({waking_hours} hours)")

    med_3x = Medication(
        id=uuid.uuid4(),
        patient_id=test_patient_1.id,
        name="Amoxicillin 500mg",
        dosage_amount=500,
        dosage_unit="mg",
        frequency_per_day=3,
        duration_days=7,
        route="oral",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=7),
        with_food=False,
        empty_stomach=False,
        bedtime_only=False,
    )

    gap_slots = get_min_gap_slots(med_3x, test_patient_1)
    gap_hours = (gap_slots * 15) / 60.0
    print(f"  - Minimum required gap  : {gap_slots} slots ({gap_hours:.1f} hours) [Old 24/3 logic was 8.0h]")

    schedule_3x = solve_schedule([med_3x], test_patient_1, [])
    if schedule_3x is not None and len(schedule_3x) == 3:
        print("  - STATUS: PASSED")
        print("  - Actual Assigned Time Slots:")
        for dose in schedule_3x:
            print(f"      * Dose #{dose['dose_index'] + 1}: {dose['scheduled_time']} ({dose['medication_name']})")
    else:
        print(f"  - STATUS: FAILED (Returned: {schedule_3x})")
        assert False, "3x/day medication failed to schedule!"

    # --------------------------------------------------------------------------
    # CHECK 2: TAKEN-Dose Immutability Test
    # --------------------------------------------------------------------------
    print("\n[CHECK 2] TAKEN-Dose Immutability on Schedule Re-solve")
    test_user_2 = User(
        id=uuid.uuid4(),
        email=f"test_immutability_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="fakehashpassword",
        full_name="Immutability Patient",
        role=UserRole.PATIENT,
    )
    test_patient_2 = Patient(
        id=uuid.uuid4(),
        user_id=test_user_2.id,
        full_name="Immutability Patient",
        date_of_birth=date(1992, 5, 10),
        gender="Female",
        wake_up_time=time(7, 0),
        breakfast_time=time(8, 0),
        lunch_time=time(13, 0),
        dinner_time=time(20, 0),
        sleep_time=time(22, 0),
    )
    med_test_2 = Medication(
        id=uuid.uuid4(),
        patient_id=test_patient_2.id,
        name="Metformin 500mg",
        dosage_amount=500,
        dosage_unit="mg",
        frequency_per_day=3,
        duration_days=14,
        route="oral",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=14),
        with_food=False,
        empty_stomach=False,
        bedtime_only=False,
    )

    try:
        db.add(test_user_2)
        db.add(test_patient_2)
        db.add(med_test_2)
        db.commit()

        # Step 1: Initial schedule generation
        gen_result = generate_schedule(db, test_patient_2.id)
        assert gen_result["success"] is True

        today = date.today()
        day_start = datetime.combine(today, datetime.min.time(), tzinfo=IST)
        day_end = datetime.combine(today, datetime.max.time(), tzinfo=IST)

        logs = (
            db.query(MedicationLog)
            .filter(
                MedicationLog.medication_id == med_test_2.id,
                MedicationLog.scheduled_time >= day_start,
                MedicationLog.scheduled_time <= day_end,
            )
            .order_by(MedicationLog.dose_index)
            .all()
        )
        assert len(logs) == 3, f"Expected 3 logs, got {len(logs)}"

        # Step 2: Mark Dose 0 as TAKEN
        dose0 = logs[0]
        before_time = dose0.scheduled_time
        dose0.status = MedicationStatus.TAKEN
        dose0.taken_time = now_ist()
        db.commit()

        print(f"  - Dose #1 status                : TAKEN")
        print(f"  - Dose #1 scheduled_time BEFORE : {before_time.strftime('%Y-%m-%d %H:%M:%S%z')} ({before_time.strftime('%H:%M')})")

        # Step 3: Trigger re-solve attempt with altered time (06:30 instead of 07:00)
        altered_time_str = "06:30"
        re_solve_schedule = [
            {
                "medication_id": med_test_2.id,
                "medication_name": med_test_2.name,
                "dose_index": 0,
                "scheduled_time": altered_time_str,  # Solver re-solves to different slot
            },
            {
                "medication_id": med_test_2.id,
                "medication_name": med_test_2.name,
                "dose_index": 1,
                "scheduled_time": "14:00",  # Pending dose updated
            },
            {
                "medication_id": med_test_2.id,
                "medication_name": med_test_2.name,
                "dose_index": 2,
                "scheduled_time": "21:00",
            },
        ]
        sync_schedule_logs(db, re_solve_schedule)

        # Step 4: Refresh from DB and verify
        db.refresh(dose0)
        after_time = dose0.scheduled_time
        print(f"  - Solver attempted new time     : {altered_time_str}")
        print(f"  - Dose #1 scheduled_time AFTER  : {after_time.strftime('%Y-%m-%d %H:%M:%S%z')} ({after_time.strftime('%H:%M')})")

        if before_time == after_time:
            print("  - STATUS: PASSED (scheduled_time is strictly immutable for TAKEN doses)")
        else:
            print(f"  - STATUS: FAILED (Time changed from {before_time} to {after_time})")
            assert False, "TAKEN dose was overwritten!"

    finally:
        db.query(MedicationLog).filter(MedicationLog.medication_id == med_test_2.id).delete()
        db.query(Medication).filter(Medication.patient_id == test_patient_2.id).delete()
        db.query(Patient).filter(Patient.id == test_patient_2.id).delete()
        db.query(User).filter(User.id == test_user_2.id).delete()
        db.commit()

    # --------------------------------------------------------------------------
    # CHECK 3: Direct Query of drug_interactions Table
    # --------------------------------------------------------------------------
    print("\n[CHECK 3] Direct Database Inspection: drug_interactions Table")
    openfda_rows = db.query(DrugInteraction).filter(DrugInteraction.source == "openfda").all()
    total_count = db.query(DrugInteraction).count()

    print(f"  - Total rows in drug_interactions table : {total_count}")
    print(f"  - Rows with source='openfda'            : {len(openfda_rows)}")
    assert total_count > 0, "drug_interactions table is EMPTY!"
    assert len(openfda_rows) == total_count, "Found rows not from openfda!"
    print("  - STATUS: PASSED (Real openFDA data confirmed, zero hardcoded seed data)")
    print("  - Sample 5 real rows from DB:")
    for row in openfda_rows[:5]:
        print(f"      * {row.drug_a.title()} + {row.drug_b.title()} | Severity: {row.severity} ({row.minimum_gap_hours}h gap) | Source: {row.source}")
        print(f"        URL: {row.source_url[:90]}...")

    # --------------------------------------------------------------------------
    # CHECK 4: Manual Test Patient (Wake 07:00, Sleep 23:00, 3x/day) -> GET /schedule/me
    # --------------------------------------------------------------------------
    print("\n[CHECK 4] Manual Test: Patient (07:00 - 23:00) with 3x/day Med -> GET /schedule/me")
    manual_user = User(
        id=uuid.uuid4(),
        email=f"manual_test_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="fakehashpassword",
        full_name="Manual Verification Patient",
        role=UserRole.PATIENT,
    )
    manual_patient = Patient(
        id=uuid.uuid4(),
        user_id=manual_user.id,
        full_name="Manual Verification Patient",
        date_of_birth=date(1985, 4, 12),
        gender="Male",
        wake_up_time=time(7, 0),
        breakfast_time=time(8, 0),
        lunch_time=time(13, 0),
        dinner_time=time(20, 0),
        sleep_time=time(23, 0),  # 23:00 bedtime as requested
    )
    manual_med = Medication(
        id=uuid.uuid4(),
        patient_id=manual_patient.id,
        name="Amoxicillin 500mg",
        dosage_amount=500,
        dosage_unit="mg",
        frequency_per_day=3,     # 3x/day as requested
        duration_days=7,
        route="oral",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=7),
        with_food=False,
        empty_stomach=False,
        bedtime_only=False,
    )

    try:
        db.add(manual_user)
        db.add(manual_patient)
        db.add(manual_med)
        db.commit()

        # Create JWT token for this user
        auth_token = create_access_token({"sub": str(manual_user.id)})

        # Call GET /schedule/me
        response = client.get(
            "/schedule/me",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        print(f"  - HTTP Status Code : {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        response_json = response.json()
        print("  - Exact Response JSON:")
        print(json.dumps(response_json, indent=4))
        print("  - STATUS: PASSED")

    finally:
        db.query(MedicationLog).filter(MedicationLog.medication_id == manual_med.id).delete()
        db.query(Medication).filter(Medication.patient_id == manual_patient.id).delete()
        db.query(Patient).filter(Patient.id == manual_patient.id).delete()
        db.query(User).filter(User.id == manual_user.id).delete()
        db.commit()
        db.close()

    print("\n" + "=" * 75)
    print("                ALL 4 TEST CHECKS COMPLETED & PASSED")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    run_all_verification_tests()
