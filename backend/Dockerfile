# Multi-stage or single-stage Dockerfile for MediSync Backend with Tesseract and Poppler
FROM python:3.11-slim

# Install system-level dependencies for PDF processing and OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser and dependencies for price scraping
RUN python -m playwright install --with-deps chromium

# Copy application source code
COPY . .

# Expose backend port
ENV PORT=8000
EXPOSE 8000

# Start uvicorn supporting dynamic $PORT from cloud platforms (Render, Railway, Fly.io, Cloud Run)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
