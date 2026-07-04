from datetime import date, datetime, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PatientCreate(BaseModel):
    full_name: str
    date_of_birth: date
    gender: str

    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_group: Optional[str] = None

    allergies: Optional[str] = None
    medical_conditions: Optional[str] = None

    wake_up_time: time
    breakfast_time: time
    lunch_time: time
    dinner_time: time
    sleep_time: time


class PatientResponse(PatientCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }