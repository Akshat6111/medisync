from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.analytics import (
    AdherenceAnalyticsResponse,
)
from app.services.analytics_service import (
    get_adherence_analytics,
)


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get(
    "/adherence",
    response_model=AdherenceAnalyticsResponse,
)
def read_adherence_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analytics = get_adherence_analytics(
        db,
        current_user,
    )

    if analytics is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    return analytics