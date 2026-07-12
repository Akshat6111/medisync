from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session
from app.core.time import IST, now_ist

from app.models.medication import Medication
from app.models.medication_log import (
    MedicationLog,
    MedicationStatus,
)
from app.models.patient import Patient
from app.models.user import User


LATE_WINDOW_MINUTES = 60


def get_current_patient(
    db: Session,
    current_user: User,
):
    return (
        db.query(Patient)
        .filter(
            Patient.user_id == current_user.id
        )
        .first()
    )


def update_expired_logs(
    db: Session,
    patient_id,
):
    now = now_ist()

    missed_before = now - timedelta(
        minutes=LATE_WINDOW_MINUTES
    )

    logs = (
        db.query(MedicationLog)
        .join(Medication)
        .filter(
            Medication.patient_id == patient_id,
            MedicationLog.status
            == MedicationStatus.PENDING,
            MedicationLog.scheduled_time
            < missed_before,
        )
        .all()
    )

    for log in logs:
        log.status = MedicationStatus.MISSED

    db.commit()


def get_my_medication_logs(
    db: Session,
    current_user: User,
):
    patient = get_current_patient(
        db,
        current_user,
    )

    if not patient:
        return []

    update_expired_logs(
        db,
        patient.id,
    )

    return (
        db.query(MedicationLog)
        .join(Medication)
        .filter(
            Medication.patient_id == patient.id
        )
        .order_by(
            MedicationLog.scheduled_time
        )
        .all()
    )


def update_medication_log(
    db: Session,
    log_id: UUID,
    status: MedicationStatus,
    notes: str | None,
    current_user: User,
):
    patient = get_current_patient(
        db,
        current_user,
    )

    if not patient:
        return None, "Patient not found"

    log = (
        db.query(MedicationLog)
        .join(Medication)
        .filter(
            MedicationLog.id == log_id,
            Medication.patient_id == patient.id,
        )
        .first()
    )

    if not log:
        return None, "Medication log not found"

    if log.status in (
    MedicationStatus.TAKEN,
    MedicationStatus.LATE,
    MedicationStatus.SKIPPED,
    ):
        return None, "Dose has already been completed"

    now = now_ist()

    if status == MedicationStatus.TAKEN:
        scheduled_time = log.scheduled_time

        if scheduled_time.tzinfo is None:
            scheduled_time = scheduled_time.replace(tzinfo=IST)
        if now < scheduled_time:
            return (
                None,
                "Dose cannot be taken before scheduled time",
            )

        late_after = (
            scheduled_time
            + timedelta(
                minutes=LATE_WINDOW_MINUTES
            )
        )

        if now > late_after:
            log.status = MedicationStatus.LATE
        else:
            log.status = MedicationStatus.TAKEN

        log.taken_time = now

    elif status == MedicationStatus.SKIPPED:
        if log.status != MedicationStatus.PENDING:
            return (
                None,
                "Only pending doses can be skipped",
            )

        log.status = MedicationStatus.SKIPPED
    else:
        return (
            None,
            "Only taken or skipped can be set manually",
        )

    log.notes = notes

    db.commit()
    db.refresh(log)

    return log, None


def delete_medication_log(
    db: Session,
    log_id: UUID,
    current_user: User,
):
    patient = get_current_patient(
        db,
        current_user,
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