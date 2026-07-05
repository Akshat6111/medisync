from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.medication import MedicationCreate, MedicationResponse
from app.services.medication_service import (
    create_medication,
    get_all_medications,
    get_medication_by_id,
    delete_medication,
)

router = APIRouter(
    prefix="/medications",
    tags=["Medications"]
)


@router.post("/", response_model=MedicationResponse)
def add_medication(
    medication: MedicationCreate,
    db: Session = Depends(get_db)
):
    new_medication = create_medication(db, medication)

    if not new_medication:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    return new_medication


@router.get("/", response_model=list[MedicationResponse])
def read_medications(db: Session = Depends(get_db)):
    return get_all_medications(db)


@router.get("/{medication_id}", response_model=MedicationResponse)
def read_medication(
    medication_id: UUID,
    db: Session = Depends(get_db)
):
    medication = get_medication_by_id(db, medication_id)

    if not medication:
        raise HTTPException(
            status_code=404,
            detail="Medication not found"
        )

    return medication


@router.delete("/{medication_id}")
def remove_medication(
    medication_id: UUID,
    db: Session = Depends(get_db)
):
    medication = delete_medication(db, medication_id)

    if not medication:
        raise HTTPException(
            status_code=404,
            detail="Medication not found"
        )

    return {
        "message": "Medication deleted successfully"
    }