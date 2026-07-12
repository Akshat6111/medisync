from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.auth.dependencies import get_current_user   # adjust import to match your actual auth dependency
from app.models.patient import Patient
from app.schemas.schedule import ScheduleResponse
from app.services.schedule_service import generate_schedule

router = APIRouter(prefix="/schedule", tags=["Schedule"])


@router.get("/me", response_model=ScheduleResponse)
def get_my_schedule(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

    if patient is None:
        raise HTTPException(status_code=404, detail="Patient profile not found for this user.")

    result = generate_schedule(db, patient.id)
    return result