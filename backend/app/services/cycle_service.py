from datetime import date, timedelta
import logging
import statistics
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.cycle import CycleLog
from app.schemas.cycle import (
    CycleLogCreate,
    CycleLogUpdate,
    CyclePredictionResponse,
)

logger = logging.getLogger(__name__)


def create_cycle_log(
    db: Session,
    patient_id: UUID,
    data: CycleLogCreate,
) -> CycleLog:
    log = CycleLog(
        patient_id=patient_id,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_cycle_logs(
    db: Session,
    patient_id: UUID,
) -> List[CycleLog]:
    return (
        db.query(CycleLog)
        .filter(CycleLog.patient_id == patient_id)
        .order_by(CycleLog.start_date.desc())
        .all()
    )


def get_cycle_log_by_id(
    db: Session,
    log_id: UUID,
    patient_id: UUID,
) -> Optional[CycleLog]:
    return (
        db.query(CycleLog)
        .filter(CycleLog.id == log_id, CycleLog.patient_id == patient_id)
        .first()
    )


def update_cycle_log(
    db: Session,
    log_id: UUID,
    patient_id: UUID,
    data: CycleLogUpdate,
) -> Optional[CycleLog]:
    log = get_cycle_log_by_id(db, log_id, patient_id)
    if not log:
        return None

    if data.start_date is not None:
        log.start_date = data.start_date
    if data.end_date is not None:
        log.end_date = data.end_date

    db.commit()
    db.refresh(log)
    return log


def delete_cycle_log(
    db: Session,
    log_id: UUID,
    patient_id: UUID,
) -> bool:
    log = get_cycle_log_by_id(db, log_id, patient_id)
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True


def compute_cycle_prediction(cycle_logs: List[CycleLog]) -> CyclePredictionResponse:
    """
    Computes rolling average cycle length, standard deviation, predicted next period window,
    and anomaly detection with an explicit 3-cycle guardrail.
    """
    total_cycles = len(cycle_logs)
    if total_cycles == 0:
        return CyclePredictionResponse(total_cycles_logged=0)

    # Sort chronological order (oldest to newest)
    sorted_logs = sorted(cycle_logs, key=lambda c: c.start_date)
    latest_log = sorted_logs[-1]

    # Menstrual cycle day counting: Cycle Day 1 is the first day of the period
    today = date.today()
    days_since_start = (today - latest_log.start_date).days
    current_cycle_day = max(1, days_since_start + 1)

    # Need at least 2 logs to determine at least one cycle interval
    if total_cycles < 2:
        return CyclePredictionResponse(
            total_cycles_logged=1,
            current_cycle_day=current_cycle_day,
            average_cycle_length=None,
            std_deviation=None,
            predicted_next_start=None,
            predicted_window_start=None,
            predicted_window_end=None,
            anomaly_flag=False,
            anomaly_reason=None,
        )

    # Calculate intervals between consecutive start dates
    intervals = [
        (sorted_logs[i + 1].start_date - sorted_logs[i].start_date).days
        for i in range(len(sorted_logs) - 1)
    ]
    # Filter valid positive interval lengths
    valid_intervals = [d for d in intervals if d > 0]
    if not valid_intervals:
        return CyclePredictionResponse(
            total_cycles_logged=total_cycles,
            current_cycle_day=current_cycle_day,
        )

    # Calculate average cycle length
    avg_length = round(float(statistics.mean(valid_intervals)), 1)

    # Calculate standard deviation (sample standard deviation requires >= 2 intervals)
    if len(valid_intervals) >= 2:
        std_dev = round(float(statistics.stdev(valid_intervals)), 1)
    else:
        std_dev = 0.0

    # Predicted next cycle start
    predicted_next = latest_log.start_date + timedelta(days=int(round(avg_length)))

    # Predicted window: predicted_next ± std_deviation (rounded to whole days, min 1 day)
    window_spread = max(1, int(round(std_dev))) if std_dev > 0 else 1
    window_start = predicted_next - timedelta(days=window_spread)
    window_end = predicted_next + timedelta(days=window_spread)

    # Anomaly detection guardrail:
    # ONLY evaluate if there are at least 3 historical cycles (i.e. >= 2 completed intervals)
    anomaly_flag = False
    anomaly_reason = None

    if total_cycles >= 3 and len(valid_intervals) >= 2:
        last_interval = valid_intervals[-1]
        prior_intervals = valid_intervals[:-1]
        prior_avg = float(statistics.mean(prior_intervals))
        prior_std = float(statistics.stdev(prior_intervals)) if len(prior_intervals) >= 2 else 0.0

        # Method 1: Compare to prior baseline variance if >= 2 prior intervals exist
        if len(prior_intervals) >= 2 and prior_std > 0:
            diff_from_prior = abs(last_interval - prior_avg)
            if diff_from_prior > 1.5 * prior_std:
                anomaly_flag = True
                direction = "longer" if last_interval > prior_avg else "shorter"
                anomaly_reason = (
                    f"Your last cycle was {last_interval} days ({direction} than your typical "
                    f"{prior_avg:.1f} ± {prior_std:.1f} day pattern)."
                )

        # Method 2: Standard deviation test across overall sample or significant deviation from baseline
        if not anomaly_flag:
            diff_from_avg = abs(last_interval - avg_length)
            if std_dev > 0 and diff_from_avg > 1.5 * std_dev:
                anomaly_flag = True
                direction = "longer" if last_interval > avg_length else "shorter"
                anomaly_reason = (
                    f"Your last cycle was {last_interval} days ({direction} than your typical "
                    f"{avg_length:.1f} ± {std_dev:.1f} day pattern)."
                )
            elif (len(prior_intervals) == 1 and abs(last_interval - prior_avg) >= 6) or (prior_std == 0 and abs(last_interval - prior_avg) >= 5):
                anomaly_flag = True
                direction = "longer" if last_interval > prior_avg else "shorter"
                anomaly_reason = (
                    f"Your last cycle was {last_interval} days ({direction} than your previous "
                    f"{prior_avg:.0f} day pattern)."
                )

    return CyclePredictionResponse(
        total_cycles_logged=total_cycles,
        current_cycle_day=current_cycle_day,
        average_cycle_length=avg_length,
        std_deviation=std_dev,
        predicted_next_start=predicted_next,
        predicted_window_start=window_start,
        predicted_window_end=window_end,
        anomaly_flag=anomaly_flag,
        anomaly_reason=anomaly_reason,
    )
