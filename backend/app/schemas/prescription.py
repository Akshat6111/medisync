from typing import Dict, List, Optional
from pydantic import BaseModel


class ParsedMedicationCandidate(BaseModel):
    raw_text_snippet: str
    matched_drug_name: str
    match_confidence: float  # 0 to 100
    dosage_amount: int
    dosage_unit: str
    frequency_per_day: int
    suggested_times: List[str]
    duration_days: int = 7
    route: str = "oral"
    with_food: bool = False
    empty_stomach: bool = False
    bedtime_only: bool = False
    notes: Optional[str] = None
    needs_review: Dict[str, bool]  # e.g., {"drug_name": False, "dosage": False, "frequency": False, "times": True}


class PrescriptionParseResponse(BaseModel):
    success: bool
    raw_text: str
    candidates: List[ParsedMedicationCandidate]
    total_found: int
