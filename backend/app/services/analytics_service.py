from sqlalchemy.orm import Session

from app.models.medication import Medication
from app.models.medication_log import (
    MedicationLog,
    MedicationStatus,
)
from app.models.patient import Patient
from app.models.user import User
from app.services.medication_log_service import (
    update_expired_logs,
)


def get_adherence_analytics(
    db: Session,
    current_user: User,
):
    patient = (
        db.query(Patient)
        .filter(
            Patient.user_id == current_user.id
        )
        .first()
    )

    if not patient:
        return None

    update_expired_logs(
        db,
        patient.id,
    )

    logs = (
        db.query(MedicationLog)
        .join(Medication)
        .filter(
            Medication.patient_id == patient.id
        )
        .all()
    )

    taken = 0
    missed = 0
    late = 0
    skipped = 0
    pending = 0

    for log in logs:
        if log.status == MedicationStatus.TAKEN:
            taken += 1

        elif log.status == MedicationStatus.MISSED:
            missed += 1

        elif log.status == MedicationStatus.LATE:
            late += 1

        elif log.status == MedicationStatus.SKIPPED:
            skipped += 1

        elif log.status == MedicationStatus.PENDING:
            pending += 1

    total_doses = len(logs)

    eligible_doses = (
        taken
        + late
        + missed
        + skipped
    )

    successful_doses = (
        taken
        + late
    )

    if eligible_doses == 0:
        adherence_rate = 0.0
    else:
        adherence_rate = round(
            (
                successful_doses
                / eligible_doses
            )
            * 100,
            2,
        )

    return {
        "total_doses": total_doses,
        "eligible_doses": eligible_doses,
        "taken": taken,
        "missed": missed,
        "late": late,
        "skipped": skipped,
        "pending": pending,
        "adherence_rate": adherence_rate,
    }