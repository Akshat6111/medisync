from datetime import date, datetime
from typing import Any, Dict

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.time import IST

from app.models.drug_interaction import DrugInteraction
from app.models.medication import Medication
from app.models.medication_log import (
    MedicationLog,
    MedicationStatus,
)
from app.models.patient import Patient
from app.scheduling.scheduler import (
    diagnose_conflict,
    solve_schedule,
)


def get_active_medications(
    db: Session,
    patient_id,
):
    today = date.today()

    return (
        db.query(Medication)
        .filter(
            Medication.patient_id == patient_id,
            Medication.start_date <= today,
            Medication.end_date >= today,
        )
        .all()
    )


def get_real_interactions(
    db: Session,
    medications,
):
    medication_names = {
        medication.name.strip().lower()
        for medication in medications
    }

    interactions = (
        db.query(DrugInteraction)
        .filter(
            or_(
                and_(
                    DrugInteraction.drug_a.in_(
                        medication_names
                    ),
                    DrugInteraction.drug_b.in_(
                        medication_names
                    ),
                ),
                and_(
                    DrugInteraction.drug_b.in_(
                        medication_names
                    ),
                    DrugInteraction.drug_a.in_(
                        medication_names
                    ),
                ),
            )
        )
        .all()
    )

    return [
        {
            "drug_a": interaction.drug_a,
            "drug_b": interaction.drug_b,
            "minimum_gap_hours": (
                interaction.minimum_gap_hours
            ),
            "severity": interaction.severity,
        }
        for interaction in interactions
    ]


def sync_schedule_logs(
    db: Session,
    schedule,
):
    today = date.today()

    day_start = datetime.combine(
        today,
        datetime.min.time(),
    )

    day_end = datetime.combine(
        today,
        datetime.max.time(),
    )

    for dose in schedule:
        scheduled_time = datetime.strptime(
            dose["scheduled_time"],
            "%H:%M",
        ).time()

        scheduled_datetime = datetime.combine(
        today,
        scheduled_time,
        tzinfo=IST,
        )

        existing_log = (
            db.query(MedicationLog)
            .filter(
                MedicationLog.medication_id
                == dose["medication_id"],
                MedicationLog.dose_index
                == dose["dose_index"],
                MedicationLog.scheduled_time
                >= day_start,
                MedicationLog.scheduled_time
                <= day_end,
            )
            .first()
        )

        if existing_log:
            if (
                existing_log.status
                == MedicationStatus.PENDING
            ):
                existing_log.scheduled_time = (
                    scheduled_datetime
                )

            continue

        medication_log = MedicationLog(
            medication_id=dose["medication_id"],
            dose_index=dose["dose_index"],
            scheduled_time=scheduled_datetime,
            status=MedicationStatus.PENDING,
        )

        db.add(medication_log)

    db.commit()


def generate_schedule(
    db: Session,
    patient_id,
) -> Dict[str, Any]:

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id)
        .first()
    )

    if patient is None:
        return {
            "success": False,
            "conflict": {
                "conflict": True,
                "reason": "insufficient_time_windows",
                "drug_a": None,
                "drug_b": None,
                "required_gap_hours": None,
                "detail": "Patient not found.",
            },
        }

    medications = get_active_medications(
        db,
        patient_id,
    )

    if not medications:
        return {
            "success": True,
            "schedule": [],
        }

    interactions = get_real_interactions(
        db,
        medications,
    )

    schedule = solve_schedule(
        medications,
        patient,
        interactions,
    )

    if schedule is None:
        conflict = diagnose_conflict(
            medications,
            patient,
            interactions,
        )

        return {
            "success": False,
            "conflict": conflict,
        }

    sync_schedule_logs(
        db,
        schedule,
    )

    return {
        "success": True,
        "schedule": schedule,
    }