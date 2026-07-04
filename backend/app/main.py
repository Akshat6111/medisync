from fastapi import FastAPI

from app.api.patient import router as patient_router

from app.db.database import Base, engine
from app.models.patient import Patient

app = FastAPI(
    title="MediSync AI",
    version="1.0.0"
)

# Create all tables
Base.metadata.create_all(bind=engine)

app.include_router(patient_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to MediSync AI 🚀"
    }