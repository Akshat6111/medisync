from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.patient import PatientCreate, PatientResponse
from app.services.patient_service import (
    create_patient,
    get_all_patients,
    get_patient_by_id,
    delete_patient,
)

router = APIRouter(
    prefix="/patients",
    tags=["Patients"]
)


@router.post("/", response_model=PatientResponse)
def add_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    return create_patient(db, patient)


@router.get("/", response_model=list[PatientResponse])
def read_patients(db: Session = Depends(get_db)):
    return get_all_patients(db)


@router.get("/{patient_id}", response_model=PatientResponse)
def read_patient(patient_id: UUID, db: Session = Depends(get_db)):
    patient = get_patient_by_id(db, patient_id)

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return patient


@router.delete("/{patient_id}")
def remove_patient(patient_id: UUID, db: Session = Depends(get_db)):
    patient = delete_patient(db, patient_id)

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return {"message": "Patient deleted successfully"}