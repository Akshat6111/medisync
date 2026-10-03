from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class LabReportValueResponse(BaseModel):
    id: UUID
    report_id: UUID
    test_name: str
    value: float
    unit: str
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    flag: str

    model_config = {
        "from_attributes": True
    }


class LabReportListItemResponse(BaseModel):
    id: UUID
    patient_id: UUID
    original_filename: str
    uploaded_at: datetime
    status: str
    summary: Optional[str] = None
    values_count: int = 0

    model_config = {
        "from_attributes": True
    }


class LabReportResponse(BaseModel):
    id: UUID
    patient_id: UUID
    original_filename: str
    uploaded_at: datetime
    status: str
    raw_text: Optional[str] = None
    summary: Optional[str] = None
    values: List[LabReportValueResponse] = []

    model_config = {
        "from_attributes": True
    }
