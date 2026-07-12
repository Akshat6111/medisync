from fastapi import FastAPI

from app.api.patient import router as patient_router
from app.api.medication import router as medication_router
from app.api.auth import router as auth_router
from app.api.schedule import router as schedule_router
from app.api.medication_log import router as log_router
from app.api.analytics import router as analytics_router
from app.api.notification import router as notification_router

from app.db.database import Base, engine

from app.models.patient import Patient
from app.models.medication import Medication
from app.models.user import User
from app.models.medication_log import MedicationLog
from app.models.drug_interaction import DrugInteraction
from app.models.notification import Notification


app = FastAPI(
    title="MediSync AI",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)

app.include_router(patient_router)
app.include_router(medication_router)
app.include_router(auth_router)
app.include_router(schedule_router)
app.include_router(log_router)
app.include_router(analytics_router)
app.include_router(notification_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to MediSync AI 🚀"
    }