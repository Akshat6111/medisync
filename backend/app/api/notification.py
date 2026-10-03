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
from app.schemas.notification import NotificationResponse
from app.services.notification_service import (
    get_my_notifications,
    mark_notification_read,
)


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get(
    "/me",
    response_model=list[NotificationResponse],
)
def read_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_my_notifications(
        db,
        current_user,
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = mark_notification_read(
        db,
        notification_id,
        current_user,
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return notification


@router.post(
    "/trigger",
    summary="Trigger reminder checks manually",
    description="Manually checks for due and overdue medication logs, creates notifications, and sends email reminders without duplication.",
)
def trigger_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.notification_service import get_current_patient, create_due_notifications
    patient = get_current_patient(db, current_user)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    created_count = create_due_notifications(db, patient.id)
    return {
        "status": "success",
        "new_notifications_created": created_count,
        "message": f"{created_count} new reminder(s) generated and delivered." if created_count > 0 else "All reminders already delivered (no duplicates)."
    }