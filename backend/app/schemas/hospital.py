from pydantic import BaseModel


class HospitalResponse(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    address: str
    phone: str | None = None
    distance_km: float
    emergency: bool | None = None
    source: str = "osm"


class GeocodeResponse(BaseModel):
    lat: float
    lng: float
    display_name: str
