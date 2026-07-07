from datetime import timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.medication import Medication
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
    )

    db.add(db_medication)
    db.commit()
    db.refresh(db_medication)

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

    return medication