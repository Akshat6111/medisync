import logging
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.prescription import PrescriptionParseResponse
from app.services.prescription_parser import parse_prescription_file

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/prescriptions",
    tags=["Prescriptions"],
)


@router.post(
    "/parse",
    response_model=PrescriptionParseResponse,
    summary="Digitize prescription via OCR & clinical shorthand parsing",
    description="Extracts raw text via OCR, resolves clinical abbreviations (1-0-1, tid, pc), and fuzzy-matches candidate drugs using RapidFuzz.",
)
async def parse_prescription_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    filename = file.filename or "prescription.png"
    lower_name = filename.lower()
    allowed_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".webp"]

    if not any(lower_name.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a PDF, PNG, JPG, JPEG, or WEBP image.",
        )

    file_bytes = await file.read()
    if not file_bytes or len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    try:
        response = parse_prescription_file(file_bytes, filename)
        return response
    except Exception as e:
        logger.error(f"Error parsing prescription document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse prescription: {str(e)}",
        )
