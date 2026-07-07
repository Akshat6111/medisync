from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.medication import (
    MedicationCreate,
    MedicationResponse,
)
from app.services.medication_service import (
    create_medication,
    delete_medication,
    get_medication_by_id,
    get_my_medications,
)

router = APIRouter(
    prefix="/medications",
    tags=["Medications"],
)


@router.post(
    "/",
    response_model=MedicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_medication(
    medication: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_medication = create_medication(
        db,
        medication,
        current_user,
    )

    if not new_medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found",
        )

    return new_medication


@router.get(
    "/",
    response_model=list[MedicationResponse],
)
def read_my_medications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_my_medications(
        db,
        current_user,
    )


@router.get(
    "/{medication_id}",
    response_model=MedicationResponse,
)
def read_medication(
    medication_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    medication = get_medication_by_id(
        db,
        medication_id,
        current_user,
    )

    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )

    return medication


@router.delete(
    "/{medication_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_medication(
    medication_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    medication = delete_medication(
        db,
        medication_id,
        current_user,
    )

    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )

    return