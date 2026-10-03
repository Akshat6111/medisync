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
    update_medication,
    sync_manual_medication_logs,
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


@router.post(
    "/sync-manual-logs",
    status_code=status.HTTP_200_OK,
)
def trigger_manual_schedule_sync(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.patient import Patient
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found",
        )

    synced_count = sync_manual_medication_logs(db, patient.id)
    return {"success": True, "synced_count": synced_count}


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


@router.put(
    "/{medication_id}",
    response_model=MedicationResponse,
)
def edit_medication(
    medication_id: UUID,
    medication: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = update_medication(
        db,
        medication_id,
        medication,
        current_user,
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )

    return updated