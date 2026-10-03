from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CycleLogCreate(BaseModel):
    start_date: date
    end_date: Optional[date] = None


class CycleLogUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CycleLogResponse(BaseModel):
    id: UUID
    patient_id: UUID
    start_date: date
    end_date: Optional[date] = None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class CyclePredictionResponse(BaseModel):
    average_cycle_length: Optional[float] = None
    std_deviation: Optional[float] = None
    current_cycle_day: Optional[int] = None
    predicted_next_start: Optional[date] = None
    predicted_window_start: Optional[date] = None
    predicted_window_end: Optional[date] = None
    anomaly_flag: bool = False
    anomaly_reason: Optional[str] = None
    total_cycles_logged: int = 0
