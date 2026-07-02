from fastapi import FastAPI

app = FastAPI(
    title="MediSync AI",
    version="1.0.0",
    description="AI-Powered Medication Management & Caregiver Platform"
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to MediSync AI 🚀"
    }