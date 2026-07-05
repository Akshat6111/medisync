from fastapi import FastAPI

from app.api.patient import router as patient_router
from app.api.medication import router as medication_router

from app.db.database import Base, engine
from app.models.patient import Patient
from app.models.medication import Medication



app = FastAPI(
    title="MediSync AI",
    version="1.0.0"
)

# Create all tables
Base.metadata.create_all(bind=engine)

app.include_router(patient_router)
app.include_router(medication_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to MediSync AI 🚀"
    }