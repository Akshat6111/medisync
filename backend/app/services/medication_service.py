from datetime import timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.medication import Medication
from app.models.patient import Patient
from app.schemas.medication import MedicationCreate


def create_medication(db: Session, medication: MedicationCreate):
    patient = (
        db.query(Patient)
        .filter(Patient.id == medication.patient_id)
        .first()
    )

    if not patient:
        return None

    end_date = medication.start_date + timedelta(days=medication.duration_days)

    db_medication = Medication(
        **medication.model_dump(),
        end_date=end_date
    )

    db.add(db_medication)
    db.commit()
    db.refresh(db_medication)

    return db_medication


def get_all_medications(db: Session):
    return db.query(Medication).all()


def get_medication_by_id(db: Session, medication_id: UUID):
    return (
        db.query(Medication)
        .filter(Medication.id == medication_id)
        .first()
    )


def delete_medication(db: Session, medication_id: UUID):
    medication = (
        db.query(Medication)
        .filter(Medication.id == medication_id)
        .first()
    )

    if medication:
        db.delete(medication)
        db.commit()

    return medication