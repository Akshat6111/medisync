from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import PatientCreate


def create_patient(
    db: Session,
    patient: PatientCreate,
    current_user: User,
):
    existing_patient = (
        db.query(Patient)
        .filter(Patient.user_id == current_user.id)
        .first()
    )

    if existing_patient:
        return None

    db_patient = Patient(
        user_id=current_user.id,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth,
        gender=patient.gender,
        height_cm=patient.height_cm,
        weight_kg=patient.weight_kg,
        blood_group=patient.blood_group,
        allergies=patient.allergies,
        medical_conditions=patient.medical_conditions,
        wake_up_time=patient.wake_up_time,
        breakfast_time=patient.breakfast_time,
        lunch_time=patient.lunch_time,
        dinner_time=patient.dinner_time,
        sleep_time=patient.sleep_time,
    )

    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)

    return db_patient


def get_my_patient(
    db: Session,
    current_user: User,
):
    return (
        db.query(Patient)
        .filter(Patient.user_id == current_user.id)
        .first()
    )


def get_patient_by_id(
    db: Session,
    patient_id,
    current_user: User,
):
    return (
        db.query(Patient)
        .filter(
            Patient.id == patient_id,
            Patient.user_id == current_user.id,
        )
        .first()
    )


def delete_patient(
    db: Session,
    patient_id,
    current_user: User,
):
    patient = (
        db.query(Patient)
        .filter(
            Patient.id == patient_id,
            Patient.user_id == current_user.id,
        )
        .first()
    )

    if patient:
        db.delete(patient)
        db.commit()

    return patient


def update_patient(
    db: Session,
    patient: PatientCreate,
    current_user: User,
):
    db_patient = (
        db.query(Patient)
        .filter(Patient.user_id == current_user.id)
        .first()
    )

    if not db_patient:
        return None

    db_patient.full_name = patient.full_name
    db_patient.date_of_birth = patient.date_of_birth
    db_patient.gender = patient.gender
    db_patient.height_cm = patient.height_cm
    db_patient.weight_kg = patient.weight_kg
    db_patient.blood_group = patient.blood_group
    db_patient.allergies = patient.allergies
    db_patient.medical_conditions = patient.medical_conditions
    db_patient.wake_up_time = patient.wake_up_time
    db_patient.breakfast_time = patient.breakfast_time
    db_patient.lunch_time = patient.lunch_time
    db_patient.dinner_time = patient.dinner_time
    db_patient.sleep_time = patient.sleep_time

    db.commit()
    db.refresh(db_patient)

    return db_patient