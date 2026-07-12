from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session


from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.medication_log import (
    MedicationLogResponse,
    MedicationLogUpdate,
)
from app.services.medication_log_service import (
    delete_medication_log,
    get_my_medication_logs,
    update_medication_log,
)


router = APIRouter(
    prefix="/medication-logs",
    tags=["Medication Logs"],
)


@router.get(
    "/me",
    response_model=list[MedicationLogResponse],
)
def read_my_medication_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_my_medication_logs(
        db,
        current_user,
    )


@router.patch(
    "/{log_id}",
    response_model=MedicationLogResponse,
)
def update_log(
    log_id: UUID,
    update: MedicationLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log, error = update_medication_log(
        db,
        log_id,
        update.status,
        update.notes,
        current_user,
    )

    if not log:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return log


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