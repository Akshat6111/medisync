from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.medication_log import MedicationStatus


class MedicationLogUpdate(BaseModel):
    status: MedicationStatus
    notes: Optional[str] = None


class MedicationLogResponse(BaseModel):
    id: UUID
    medication_id: UUID
    dose_index: int
    scheduled_time: datetime
    taken_time: Optional[datetime]
    status: MedicationStatus
    notes: Optional[str]
    created_at: datetime

    model_config = {
        "from_attributes": True
    }