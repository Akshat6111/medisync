from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.medication_log import MedicationStatus


class MedicationLogCreate(BaseModel):
    medication_id: UUID

    scheduled_time: datetime

    taken_time: Optional[datetime] = None

    status: MedicationStatus

    notes: Optional[str] = None


class MedicationLogResponse(MedicationLogCreate):
    id: UUID

    created_at: datetime

    model_config = {
        "from_attributes": True
    }