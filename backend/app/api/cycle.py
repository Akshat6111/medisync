from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.models.patient import Patient
from app.models.user import User
from app.schemas.cycle import (
    CycleLogCreate,
    CycleLogResponse,
    CycleLogUpdate,
    CyclePredictionResponse,
)
from app.services.cycle_service import (
    compute_cycle_prediction,
    create_cycle_log,
    delete_cycle_log,
    get_cycle_logs,
    update_cycle_log,
)

router = APIRouter(
    prefix="/cycles",
    tags=["CycleSync"],
)


@router.post(
    "/",
    response_model=CycleLogResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_log(
    data: CycleLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found. Please complete your profile first.",
        )

    log = create_cycle_log(db, patient.id, data)
    return log


@router.get(
    "/",
    response_model=List[CycleLogResponse],
)
def list_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        return []

    return get_cycle_logs(db, patient.id)


@router.get(
    "/prediction",
    response_model=CyclePredictionResponse,
)
def get_prediction(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        return CyclePredictionResponse()

    logs = get_cycle_logs(db, patient.id)
    return compute_cycle_prediction(logs)


@router.put(
    "/{log_id}",
    response_model=CycleLogResponse,
)
def update_log(
    log_id: UUID,
    data: CycleLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )

    updated = update_cycle_log(db, log_id, patient.id, data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cycle log not found.",
        )

    return updated


@router.delete(
    "/{log_id}",
    status_code=status.HTTP_200_OK,
)
def remove_log(
    log_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )

    success = delete_cycle_log(db, log_id, patient.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cycle log not found.",
        )

    return {"message": "Cycle log deleted successfully"}
