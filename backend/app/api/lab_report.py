from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.models.patient import Patient
from app.models.user import User
from app.schemas.lab_report import LabReportListItemResponse, LabReportResponse
from app.services.lab_report_service import (
    create_and_process_lab_report,
    delete_lab_report,
    get_report_by_id,
    get_reports_by_patient,
)

router = APIRouter(
    prefix="/lab-reports",
    tags=["Lab Reports"],
)


@router.post(
    "/",
    response_model=LabReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_lab_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found. Please complete your profile first.",
        )

    filename = file.filename or "uploaded_report.pdf"
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    report = create_and_process_lab_report(
        db=db,
        patient_id=patient.id,
        filename=filename,
        file_bytes=file_bytes,
    )

    return report


@router.get(
    "/",
    response_model=List[LabReportListItemResponse],
)
def list_lab_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        return []

    reports = get_reports_by_patient(db, patient.id)
    results = []
    for r in reports:
        # Create preview summary (first 140 chars)
        summary_preview = r.summary
        if summary_preview and len(summary_preview) > 140:
            summary_preview = summary_preview[:140] + "..."

        results.append(
            LabReportListItemResponse(
                id=r.id,
                patient_id=r.patient_id,
                original_filename=r.original_filename,
                uploaded_at=r.uploaded_at,
                status=r.status.value if hasattr(r.status, "value") else str(r.status),
                summary=summary_preview,
                values_count=len(r.values),
            )
        )
    return results


@router.get(
    "/{report_id}",
    response_model=LabReportResponse,
)
def get_lab_report_detail(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )

    report = get_report_by_id(db, report_id, patient.id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab report not found.",
        )

    return report


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_200_OK,
)
def remove_lab_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )

    success = delete_lab_report(db, report_id, patient.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab report not found.",
        )

    return {"message": "Report deleted successfully"}
