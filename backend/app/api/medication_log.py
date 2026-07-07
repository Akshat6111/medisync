from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.medication_log import (
    MedicationLogCreate,
    MedicationLogResponse,
)
from app.services.medication_log_service import (
    create_medication_log,
    delete_medication_log,
    get_medication_logs,
)

router = APIRouter(
    prefix="/medication-logs",
    tags=["Medication Logs"],
)


@router.post(
    "/",
    response_model=MedicationLogResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_medication_log(
    log: MedicationLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_log = create_medication_log(
        db,
        log,
        current_user,
    )

    if not new_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )

    return new_log


@router.get(
    "/{medication_id}",
    response_model=list[MedicationLogResponse],
)
def read_medication_logs(
    medication_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_medication_logs(
        db,
        medication_id,
        current_user,
    )


@router.delete(
    "/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_medication_log(
    log_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = delete_medication_log(
        db,
        log_id,
        current_user,
    )

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication log not found",
        )

    return