from pydantic import BaseModel


class AdherenceAnalyticsResponse(BaseModel):
    total_doses: int
    eligible_doses: int

    taken: int
    missed: int
    late: int
    skipped: int
    pending: int

    adherence_rate: float