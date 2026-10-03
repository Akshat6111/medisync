from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.embeddings import warmup_embeddings_async


from app.api.patient import router as patient_router
from app.api.medication import router as medication_router
from app.api.auth import router as auth_router
from app.api.schedule import router as schedule_router
from app.api.medication_log import router as log_router
from app.api.analytics import router as analytics_router
from app.api.notification import router as notification_router
from app.api.lab_report import router as lab_report_router
from app.api.cycle import router as cycle_router
from app.ai.router import router as ai_router
from app.api.hospital import router as hospital_router
from app.api.prescription import router as prescription_router
from app.api.generic_finder import router as generic_finder_router

from app.db.database import Base, engine

from app.models.patient import Patient
from app.models.medication import Medication
from app.models.user import User
from app.models.medication_log import MedicationLog
from app.models.drug_interaction import DrugInteraction
from app.models.notification import Notification
from app.models.lab_report import LabReport, LabReportValue
from app.models.cycle import CycleLog
from app.models.price_cache import PriceCache


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure AI embedding model is pre-warmed in background thread
    warmup_embeddings_async()
    yield


app = FastAPI(
    title="MediSync AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Start background warmup immediately on process boot
warmup_embeddings_async()


Base.metadata.create_all(bind=engine)

app.include_router(patient_router)
app.include_router(medication_router)
app.include_router(auth_router)
app.include_router(schedule_router)
app.include_router(log_router)
app.include_router(analytics_router)
app.include_router(notification_router)
app.include_router(lab_report_router)
app.include_router(cycle_router)
app.include_router(ai_router)
app.include_router(hospital_router)
app.include_router(prescription_router)
app.include_router(generic_finder_router)


import os

default_cors = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
env_cors = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
cors_origins = env_cors if env_cors else default_cors

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Welcome to MediSync AI 🚀"
    }