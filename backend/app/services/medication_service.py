from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.time import IST
from app.models.medication import Medication
from app.models.medication_log import MedicationLog, MedicationStatus
from app.models.patient import Patient
from app.models.user import User
from app.schemas.medication import MedicationCreate


def create_medication(
    db: Session,
    medication: MedicationCreate,
    current_user: User,
):
    patient = (
        db.query(Patient)
        .filter(Patient.user_id == current_user.id)
        .first()
    )

    if not patient:
        return None

    end_date = (
        medication.start_date
        + timedelta(days=medication.duration_days)
    )

    db_medication = Medication(
        patient_id=patient.id,
        name=medication.name,
        dosage_amount=medication.dosage_amount,
        dosage_unit=medication.dosage_unit,
        frequency_per_day=medication.frequency_per_day,
        duration_days=medication.duration_days,
        route=medication.route,
        with_food=medication.with_food,
        empty_stomach=medication.empty_stomach,
        bedtime_only=medication.bedtime_only,
        start_date=medication.start_date,
        end_date=end_date,
        notes=medication.notes,
        scheduled_time=medication.scheduled_time,
    )

    db.add(db_medication)
    db.commit()
    db.refresh(db_medication)

    if db_medication.scheduled_time:
        sync_manual_medication_logs(db, patient.id)

    return db_medication


def get_my_medications(
    db: Session,
    current_user: User,
):
    patient = (
        db.query(Patient)
        .filter(Patient.user_id == current_user.id)
        .first()
    )

    if not patient:
        return []

    return (
        db.query(Medication)
        .filter(Medication.patient_id == patient.id)
        .all()
    )


def get_medication_by_id(
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
        return None

    return (
        db.query(Medication)
        .filter(
            Medication.id == medication_id,
            Medication.patient_id == patient.id,
        )
        .first()
    )


def delete_medication(
    db: Session,
    medication_id: UUID,
    current_user: User,
):
    medication = get_medication_by_id(
        db,
        medication_id,
        current_user,
    )

    if medication:
        db.delete(medication)
        db.commit()
        try:
            from app.ai.cache import clear_session_cache
            clear_session_cache(user_id=current_user.id)
        except Exception:
            pass

    return medication


def update_medication(
    db: Session,
    medication_id: UUID,
    medication: MedicationCreate,
    current_user: User,
):
    patient = (
        db.query(Patient)
        .filter(Patient.user_id == current_user.id)
        .first()
    )

    if not patient:
        return None

    db_medication = (
        db.query(Medication)
        .filter(
            Medication.id == medication_id,
            Medication.patient_id == patient.id,
        )
        .first()
    )

    if not db_medication:
        return None

    end_date = (
        medication.start_date
        + timedelta(days=medication.duration_days)
    )

    db_medication.name = medication.name
    db_medication.dosage_amount = medication.dosage_amount
    db_medication.dosage_unit = medication.dosage_unit
    db_medication.frequency_per_day = medication.frequency_per_day
    db_medication.duration_days = medication.duration_days
    db_medication.route = medication.route
    db_medication.with_food = medication.with_food
    db_medication.empty_stomach = medication.empty_stomach
    db_medication.bedtime_only = medication.bedtime_only
    db_medication.start_date = medication.start_date
    db_medication.end_date = end_date
    db_medication.notes = medication.notes
    db_medication.scheduled_time = medication.scheduled_time

    db.commit()
    db.refresh(db_medication)

    if db_medication.scheduled_time:
        sync_manual_medication_logs(db, patient.id)

    return db_medication


def sync_manual_medication_logs(
    db: Session,
    patient_id: UUID,
) -> int:
    """
    Directly generates or updates today's medication_logs for medications
    that have manually configured scheduled_time values.
    Runs independently of the CSP scheduler.
    """
    today = date.today()
    day_start = datetime.combine(today, datetime.min.time())
    day_end = datetime.combine(today, datetime.max.time())

    medications = (
        db.query(Medication)
        .filter(
            Medication.patient_id == patient_id,
            Medication.start_date <= today,
            Medication.end_date >= today,
            Medication.scheduled_time.isnot(None),
        )
        .all()
    )

    synced_count = 0
    for med in medications:
        times = med.scheduled_time
        if not isinstance(times, list) or len(times) == 0:
            continue

        for dose_index, time_str in enumerate(times):
            try:
                parts = time_str.strip().split(":")
                t_hour = int(parts[0])
                t_minute = int(parts[1])
                scheduled_datetime = datetime.combine(
                    today,
                    datetime.min.time().replace(hour=t_hour, minute=t_minute),
                    tzinfo=IST,
                )
            except Exception:
                continue

            existing_log = (
                db.query(MedicationLog)
                .filter(
                    MedicationLog.medication_id == med.id,
                    MedicationLog.dose_index == dose_index,
                    MedicationLog.scheduled_time >= day_start,
                    MedicationLog.scheduled_time <= day_end,
                )
                .first()
            )

            if existing_log:
                if existing_log.status == MedicationStatus.PENDING:
                    existing_log.scheduled_time = scheduled_datetime
                    synced_count += 1
            else:
                new_log = MedicationLog(
                    medication_id=med.id,
                    dose_index=dose_index,
                    scheduled_time=scheduled_datetime,
                    status=MedicationStatus.PENDING,
                )
                db.add(new_log)
                synced_count += 1

    db.commit()
    return synced_count
