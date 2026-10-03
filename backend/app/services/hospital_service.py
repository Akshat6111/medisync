import logging
import math
import httpx
from typing import List, Optional

from app.config.settings import settings
from app.schemas.hospital import HospitalResponse, GeocodeResponse

logger = logging.getLogger(__name__)

import time

OVERPASS_ENDPOINTS = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {
    "User-Agent": "MediSync-Healthcare-Platform/1.0 (medisync-emergency@healthapp.org)"
}

# Coordinate-level cache: (lat_2dec, lng_2dec, radius) -> {"time": timestamp, "data": List[HospitalResponse]}
_HOSPITAL_CACHE = {}
_CACHE_TTL = 3600  # 1 hour



def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def _extract_phone(tags: dict) -> Optional[str]:
    """Extract and normalize a contact or emergency phone number from OSM tags."""
    candidates = [
        tags.get("contact:phone"),
        tags.get("phone"),
        tags.get("contact:mobile"),
        tags.get("emergency:phone"),
        tags.get("tel"),
    ]
    for cand in candidates:
        if cand and isinstance(cand, str) and cand.strip():
            # If multiple numbers separated by semicolon or comma, take the first one
            first = cand.split(";")[0].split(",")[0].strip()
            if first:
                return first
    return None


def _extract_address(tags: dict, fallback_lat: float, fallback_lng: float) -> str:
    """Construct a human-readable address from OSM address tags."""
    if tags.get("addr:full"):
        return tags["addr:full"].strip()

    parts = []
    street_parts = []
    if tags.get("addr:housenumber"):
        street_parts.append(tags["addr:housenumber"])
    if tags.get("addr:street"):
        street_parts.append(tags["addr:street"])
    if street_parts:
        parts.append(" ".join(street_parts))

    if tags.get("addr:suburb"):
        parts.append(tags["addr:suburb"])
    if tags.get("addr:district"):
        parts.append(tags["addr:district"])
    if tags.get("addr:city"):
        parts.append(tags["addr:city"])
    elif tags.get("addr:town"):
        parts.append(tags["addr:town"])
    elif tags.get("addr:village"):
        parts.append(tags["addr:village"])

    if tags.get("addr:postcode"):
        parts.append(tags["addr:postcode"])

    if parts:
        return ", ".join(parts)

    return f"Coordinates: {fallback_lat:.4f}, {fallback_lng:.4f}"


async def _fetch_from_google_places(
    lat: float, lng: float, radius: float
) -> List[HospitalResponse]:
    """Fallback or alternative lookup via Google Places Nearby Search."""
    api_key = settings.GOOGLE_MAPS_API_KEY
    if not api_key:
        return []

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": int(radius),
        "type": "hospital",
        "key": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        results: List[HospitalResponse] = []
        for place in data.get("results", []):
            loc = place.get("geometry", {}).get("location", {})
            h_lat = loc.get("lat")
            h_lng = loc.get("lng")
            if h_lat is None or h_lng is None:
                continue

            dist = haversine_distance(lat, lng, h_lat, h_lng)
            results.append(
                HospitalResponse(
                    id=f"google_{place.get('place_id', '')}",
                    name=place.get("name", "Hospital"),
                    lat=h_lat,
                    lng=h_lng,
                    address=place.get("vicinity", "Nearby area"),
                    phone=None,
                    distance_km=dist,
                    emergency=True if "emergency" in place.get("types", []) else None,
                    source="google",
                )
            )
        results.sort(key=lambda h: h.distance_km)
        return results
    except Exception as e:
        logger.warning(f"Google Places lookup failed: {e}")
        return []


async def _fetch_from_overpass(
    lat: float, lng: float, radius: float
) -> List[HospitalResponse]:
    """Query Overpass API for nearby hospitals with timeout resilience and mirror failover."""
    # Build Overpass QL query: nodes, ways, and relations tagged amenity=hospital
    query = f"""
    [out:json][timeout:10];
    (
      node["amenity"="hospital"](around:{int(radius)},{lat},{lng});
      way["amenity"="hospital"](around:{int(radius)},{lat},{lng});
      relation["amenity"="hospital"](around:{int(radius)},{lat},{lng});
    );
    out center;
    """

    data = None
    last_err = None

    async with httpx.AsyncClient(headers=HEADERS, timeout=10.0) as client:
        for endpoint in OVERPASS_ENDPOINTS:
            try:
                resp = await client.post(endpoint, data={"data": query})
                if resp.status_code == 200:
                    data = resp.json()
                    break
                else:
                    logger.warning(
                        f"Overpass mirror {endpoint} responded with status {resp.status_code}"
                    )
            except Exception as e:
                logger.warning(f"Failed calling Overpass mirror {endpoint}: {e}")
                last_err = e

    if not data or "elements" not in data:
        if last_err:
            raise RuntimeError(f"Overpass API lookup failed or timed out: {last_err}")
        return []

    elements = data.get("elements", [])
    hospitals: List[HospitalResponse] = []
    seen_ids = set()

    for elem in elements:
        elem_id = f"{elem.get('type', 'node')}_{elem.get('id')}"
        if elem_id in seen_ids:
            continue
        seen_ids.add(elem_id)

        # Coordinate resolution
        if elem.get("type") == "node":
            h_lat = elem.get("lat")
            h_lng = elem.get("lon")
        else:
            center = elem.get("center", {})
            h_lat = center.get("lat")
            h_lng = center.get("lon")

        if h_lat is None or h_lng is None:
            continue

        tags = elem.get("tags", {})
        name = tags.get("name") or tags.get("name:en") or tags.get("operator") or "Hospital / Healthcare Center"
        phone = _extract_phone(tags)
        address = _extract_address(tags, h_lat, h_lng)

        emergency_tag = tags.get("emergency")
        emergency = True if emergency_tag in ("yes", "24/7", "designated") else (False if emergency_tag == "no" else None)

        dist = haversine_distance(lat, lng, h_lat, h_lng)

        hospitals.append(
            HospitalResponse(
                id=elem_id,
                name=name,
                lat=round(h_lat, 6),
                lng=round(h_lng, 6),
                address=address,
                phone=phone,
                distance_km=dist,
                emergency=emergency,
                source="osm",
            )
        )

    # Sort closest first
    hospitals.sort(key=lambda h: h.distance_km)
    return hospitals


async def get_nearby_hospitals(
    lat: float, lng: float, radius: float = 5000.0
) -> List[HospitalResponse]:
    """Retrieve nearby hospitals, preferring Overpass API and falling back to Google Places or cache if available."""
    cache_key = (round(lat, 2), round(lng, 2), int(radius))
    now = time.time()
    if cache_key in _HOSPITAL_CACHE:
        entry = _HOSPITAL_CACHE[cache_key]
        if now - entry["time"] < _CACHE_TTL:
            return entry["data"]

    try:
        results = await _fetch_from_overpass(lat, lng, radius)
        if results:
            _HOSPITAL_CACHE[cache_key] = {"time": now, "data": results}
            return results
    except Exception as e:
        logger.warning(f"Overpass API error: {e}")
        # If Google Places API is available, try it as fallback
        if settings.GOOGLE_MAPS_API_KEY:
            google_results = await _fetch_from_google_places(lat, lng, radius)
            if google_results:
                _HOSPITAL_CACHE[cache_key] = {"time": now, "data": google_results}
                return google_results

        # Return cached results if any exist even if expired
        if cache_key in _HOSPITAL_CACHE:
            logger.info("Returning previously cached hospital results following upstream timeout")
            return _HOSPITAL_CACHE[cache_key]["data"]

        raise

    # If Overpass returned 0 results and Google Places key is present, try Google Places
    if settings.GOOGLE_MAPS_API_KEY:
        google_results = await _fetch_from_google_places(lat, lng, radius)
        if google_results:
            _HOSPITAL_CACHE[cache_key] = {"time": now, "data": google_results}
            return google_results

    return []


async def geocode_query(query: str) -> List[GeocodeResponse]:
    """Geocode a text location string using Nominatim with resilient timeout."""
    params = {
        "q": query,
        "format": "json",
        "limit": 5,
        "addressdetails": 1,
    }

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=8.0) as client:
            resp = await client.get(NOMINATIM_URL, params=params)
            resp.raise_for_status()
            items = resp.json()

        results: List[GeocodeResponse] = []
        for item in items:
            try:
                results.append(
                    GeocodeResponse(
                        lat=float(item["lat"]),
                        lng=float(item["lon"]),
                        display_name=item.get("display_name", query),
                    )
                )
            except (KeyError, ValueError):
                continue
        return results
    except Exception as e:
        logger.error(f"Geocoding error for query '{query}': {e}")
        return []
