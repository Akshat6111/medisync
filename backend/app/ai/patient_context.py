from typing import Optional
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.medication import Medication
from app.models.medication_log import MedicationLog
from app.models.user import User
from app.services.patient_service import get_my_patient


def get_patient_context(db: Session, current_user: User) -> str:
    """
    Builds strict clinical and personal ground truth for the authenticated user,
    including demographics, vitals, routine times, actively prescribed medications,
    and recent adherence logs.
    """
    patient = get_my_patient(db, current_user)

    if patient is None:
        return "=== PATIENT RECORD ===\nNo patient profile found in MediSync for this account."

    lines = [
        "=== PATIENT RECORD (GROUND TRUTH) ===",
        f"Patient Name: {patient.full_name}",
        f"Gender: {patient.gender} | Date of Birth: {patient.date_of_birth}",
        f"Height: {patient.height_cm or 'Not recorded'} cm | Weight: {patient.weight_kg or 'Not recorded'} kg | Blood Group: {patient.blood_group or 'Not recorded'}",
        f"Known Allergies: {patient.allergies or 'None reported'}",
        f"Diagnosed Medical Conditions: {patient.medical_conditions or 'None reported'}",
        f"Daily Routine Times: Wake: {patient.wake_up_time}, Breakfast: {patient.breakfast_time}, Lunch: {patient.lunch_time}, Dinner: {patient.dinner_time}, Sleep: {patient.sleep_time}",
    ]

    # Active Prescribed Medications in MediSync
    try:
        medications = (
            db.query(Medication)
            .filter(Medication.patient_id == patient.id)
            .order_by(Medication.name)
            .all()
        )
        if medications:
            lines.append("\nActive Prescribed Medications in MediSync:")
            for med in medications:
                sched_str = f"Scheduled Times: {med.scheduled_time}" if med.scheduled_time else "Scheduled Times: Standard daily"
                food_notes = []
                if med.with_food:
                    food_notes.append("take with food")
                if med.empty_stomach:
                    food_notes.append("take on empty stomach")
                if med.bedtime_only:
                    food_notes.append("bedtime only")
                food_rule = f" ({', '.join(food_notes)})" if food_notes else ""

                lines.append(
                    f"- {med.name}: {med.dosage_amount} {med.dosage_unit}, Route: {med.route}, "
                    f"Frequency: {med.frequency_per_day}x/day{food_rule}, "
                    f"Duration: {med.duration_days} days (From: {med.start_date} To: {med.end_date}). "
                    f"{sched_str}. Notes: {med.notes or 'None'}"
                )
        else:
            lines.append("\nActive Prescribed Medications in MediSync: None recorded.")
    except Exception as e:
        lines.append(f"\nActive Prescribed Medications: Unable to query database ({e}).")

    # Recent Medication Adherence Logs
    try:
        logs = (
            db.query(MedicationLog)
            .join(Medication, Medication.id == MedicationLog.medication_id)
            .filter(Medication.patient_id == patient.id)
            .order_by(desc(MedicationLog.scheduled_time))
            .limit(10)
            .all()
        )
        if logs:
            lines.append("\nRecent Medication Adherence Logs:")
            for log in logs:
                med_name = log.medication.name if log.medication else "Medication"
                status_val = log.status.value.upper() if hasattr(log.status, "value") else str(log.status).upper()
                lines.append(f"- {log.scheduled_time}: {med_name} — Status: {status_val} (Notes: {log.notes or 'None'})")
        else:
            lines.append("\nRecent Medication Adherence Logs: No logs recorded yet.")
    except Exception as e:
        lines.append(f"\nRecent Medication Adherence Logs: Unable to query logs ({e}).")

    return "\n".join(lines)