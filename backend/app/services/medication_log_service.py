from uuid import UUID

from sqlalchemy.orm import Session

from app.models.medication import Medication
from app.models.medication_log import MedicationLog
from app.models.patient import Patient
from app.models.user import User
from app.schemas.medication_log import MedicationLogCreate


def create_medication_log(
    db: Session,
    log: MedicationLogCreate,
    current_user: User,
):
    patient = (
        db.query(Patient)
        .filter(Patient.user_id == current_user.id)
        .first()
    )

    if not patient:
        return None

    medication = (
        db.query(Medication)
        .filter(
            Medication.id == log.medication_id,
            Medication.patient_id == patient.id,
        )
        .first()
    )

    if not medication:
        return None

    db_log = MedicationLog(
        medication_id=log.medication_id,
        scheduled_time=log.scheduled_time,
        taken_time=log.taken_time,
        status=log.status,
        notes=log.notes,
    )

    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    return db_log


def get_medication_logs(
    db: Session,
    medication_id: UUID,
    current_user: User,
):
    patient = (
        db.query(Patient)
        .filter(Patient.user_id == current_user.id)
        .first()
    )

    if not patient:
        return []

    medication = (
        db.query(Medication)
        .filter(
            Medication.id == medication_id,
            Medication.patient_id == patient.id,
        )
        .first()
    )

    if not medication:
        return []

    return (
        db.query(MedicationLog)
        .filter(
            MedicationLog.medication_id == medication_id
        )
        .all()
    )


def delete_medication_log(
    db: Session,
    log_id: UUID,
    current_user: User,
):
    patient = (
        db.query(Patient)
        .filter(Patient.user_id == current_user.id)
        .first()
    )

    if not patient:
        return None

    log = (
        db.query(MedicationLog)
        .join(Medication)
        .filter(
            MedicationLog.id == log_id,
            Medication.patient_id == patient.id,
        )
        .first()
    )

    if log:
        db.delete(log)
        db.commit()

    return log