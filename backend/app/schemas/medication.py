from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class MedicationCreate(BaseModel):
    patient_id: UUID

    name: str

    dosage_amount: int
    dosage_unit: str

    frequency_per_day: int

    duration_days: int

    route: str

    with_food: bool = False
    empty_stomach: bool = False
    bedtime_only: bool = False

    start_date: date

    notes: Optional[str] = None


class MedicationResponse(MedicationCreate):
    id: UUID
    created_at: datetime
    end_date: date

    model_config = {
        "from_attributes": True
    }