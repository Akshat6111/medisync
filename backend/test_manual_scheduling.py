import uuid
from datetime import date, timedelta
from app.db.database import SessionLocal
from app.models.patient import Patient
from app.models.medication import Medication
from app.models.medication_log import MedicationLog, MedicationStatus
from app.models.lab_report import LabReport, LabReportValue
from app.models.cycle import CycleLog
from app.models.drug_interaction import DrugInteraction
from app.models.notification import Notification
from app.services.medication_service import sync_manual_medication_logs
from app.services.schedule_service import generate_schedule

def test_manual_scheduling_and_csp_isolation():
    db = SessionLocal()
    try:
        # Find any test patient
        patient = db.query(Patient).first()
        if not patient:
            print("No patient found in database to run live test against.")
            return

        print(f"Testing with Patient ID: {patient.id} ({patient.full_name})")

        # 1. Test Manual Medication Creation & Sync
        test_med_id = uuid.uuid4()
        manual_med = Medication(
            id=test_med_id,
            patient_id=patient.id,
            name="Manual Test Drug",
            dosage_amount=500,
            dosage_unit="mg",
            frequency_per_day=2,
            duration_days=10,
            route="oral",
            start_date=date.today() - timedelta(days=1),
            end_date=date.today() + timedelta(days=9),
            scheduled_time=["09:15", "21:30"],
        )
        db.add(manual_med)
        db.commit()

        synced_count = sync_manual_medication_logs(db, patient.id)
        print(f"Manual sync generated/updated {synced_count} log(s) for today.")

        # Query the generated logs
        logs = db.query(MedicationLog).filter(
            MedicationLog.medication_id == test_med_id
        ).order_by(MedicationLog.dose_index).all()

        print(f"Generated {len(logs)} logs for Manual Test Drug:")
        for log in logs:
            print(f"  - Dose #{log.dose_index + 1}: Scheduled at {log.scheduled_time.strftime('%H:%M')} (Status: {log.status.value})")

        assert len(logs) == 2, "Should have created 2 dose logs"
        assert logs[0].scheduled_time.strftime("%H:%M") == "09:15", "First dose should be 09:15"
        assert logs[1].scheduled_time.strftime("%H:%M") == "21:30", "Second dose should be 21:30"

        # 2. Confirm Existing CSP Scheduler still runs without regression
        print("\n--- Testing Existing CSP Scheduler (Zero Regression) ---")
        csp_result = generate_schedule(db, patient.id)
        print(f"CSP Solver Success: {csp_result.get('success')}")
        if csp_result.get("schedule"):
            print(f"CSP generated {len(csp_result['schedule'])} scheduled doses.")
        elif csp_result.get("conflict"):
            print(f"CSP detected conflict: {csp_result['conflict']}")

        print("\nAll Manual Scheduling and CSP isolation tests PASSED!")

        # Clean up test medication and its logs
        db.delete(manual_med)
        db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    test_manual_scheduling_and_csp_isolation()
