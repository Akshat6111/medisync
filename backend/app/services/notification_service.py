from datetime import timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.time import IST, now_ist
from app.models.medication import Medication
from app.models.medication_log import (
    MedicationLog,
    MedicationStatus,
)
from app.models.notification import Notification
from app.models.patient import Patient
from app.models.user import User


REMINDER_WINDOW_MINUTES = 15


def get_current_patient(
    db: Session,
    current_user: User,
):
    return (
        db.query(Patient)
        .filter(
            Patient.user_id == current_user.id
        )
        .first()
    )


def create_due_notifications(
    db: Session,
    patient_id,
):
    now = now_ist()

    reminder_until = now + timedelta(
        minutes=REMINDER_WINDOW_MINUTES
    )

    logs = (
        db.query(MedicationLog)
        .join(Medication)
        .filter(
            Medication.patient_id == patient_id,
            MedicationLog.status
            == MedicationStatus.PENDING,
        )
        .all()
    )

    for log in logs:
        scheduled_time = log.scheduled_time

        if scheduled_time.tzinfo is None:
            scheduled_time = scheduled_time.replace(
                tzinfo=IST
            )

        if now <= scheduled_time <= reminder_until:
            notification_type = "due"

            title = "Medication due soon"

            message = (
                f"{log.medication.name} is scheduled "
                f"for {scheduled_time.strftime('%H:%M')}."
            )

        elif scheduled_time < now:
            notification_type = "overdue"

            title = "Medication overdue"

            message = (
                f"{log.medication.name} was scheduled "
                f"for {scheduled_time.strftime('%H:%M')}."
            )

        else:
            continue

        existing_notification = (
            db.query(Notification)
            .filter(
                Notification.medication_log_id
                == log.id,
                Notification.notification_type
                == notification_type,
            )
            .first()
        )

        if existing_notification:
            continue

        notification = Notification(
            medication_log_id=log.id,
            notification_type=notification_type,
            title=title,
            message=message,
        )

        db.add(notification)

    db.commit()


def get_my_notifications(
    db: Session,
    current_user: User,
):
    patient = get_current_patient(
        db,
        current_user,
    )

    if not patient:
        return []

    create_due_notifications(
        db,
        patient.id,
    )

    return (
        db.query(Notification)
        .join(MedicationLog)
        .join(Medication)
        .filter(
            Medication.patient_id == patient.id
        )
        .order_by(
            Notification.created_at.desc()
        )
        .all()
    )


def mark_notification_read(
    db: Session,
    notification_id: UUID,
    current_user: User,
):
    patient = get_current_patient(
        db,
        current_user,
    )

    if not patient:
        return None

    notification = (
        db.query(Notification)
        .join(MedicationLog)
        .join(Medication)
        .filter(
            Notification.id == notification_id,
            Medication.patient_id == patient.id,
        )
        .first()
    )

    if not notification:
        return None

    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification