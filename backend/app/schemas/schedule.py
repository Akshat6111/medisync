from typing import Dict, List, Optional
from pydantic import BaseModel
from uuid import UUID


class DoseTime(BaseModel):
    medication_id: UUID
    medication_name: str
    dose_index: int          # 0 = first dose of the day, 1 = second, etc.
    scheduled_time: str      # "HH:MM" format


class ScheduleConflict(BaseModel):
    conflict: bool = True
    reason: str               # "interaction_gap" | "insufficient_time_windows"
    medication_a_id: Optional[UUID] = None
    medication_b_id: Optional[UUID] = None
    required_gap_hours: Optional[float] = None
    detail: Optional[str] = None


class ScheduleResponse(BaseModel):
    success: bool
    schedule: Optional[List[DoseTime]] = None
    conflict: Optional[ScheduleConflict] = None