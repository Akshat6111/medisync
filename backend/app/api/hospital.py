import logging
from typing import List
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.hospital import HospitalResponse, GeocodeResponse
from app.services.hospital_service import get_nearby_hospitals, geocode_query

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/hospitals",
    tags=["Hospitals"],
)


@router.get(
    "/nearby",
    response_model=List[HospitalResponse],
    summary="Find nearby hospitals",
    description="Locates nearby hospitals using Overpass API (OpenStreetMap) within the given radius (meters). Distance calculated via Haversine.",
)
async def find_nearby_hospitals(
    lat: float = Query(..., description="Target latitude (-90 to 90)", ge=-90.0, le=90.0),
    lng: float = Query(..., description="Target longitude (-180 to 180)", ge=-180.0, le=180.0),
    radius: float = Query(5000.0, description="Search radius in meters (500m to 50000m)", ge=500.0, le=50000.0),
):
    try:
        results = await get_nearby_hospitals(lat=lat, lng=lng, radius=radius)
        return results
    except Exception as e:
        logger.error(f"Error fetching nearby hospitals: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hospital lookup service is temporarily slow or busy. Please try again in a moment.",
        )


@router.get(
    "/geocode",
    response_model=List[GeocodeResponse],
    summary="Geocode city or address",
    description="Geocodes a search string using OpenStreetMap Nominatim with server-side caching and resilient timeout.",
)
async def geocode_address(
    query: str = Query(..., min_length=2, description="City, locality, or landmark to geocode"),
):
    try:
        results = await geocode_query(query=query)
        return results
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to geocode location search query.",
        )
