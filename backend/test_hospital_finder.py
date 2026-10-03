import asyncio
import sys
from app.services.hospital_service import haversine_distance, get_nearby_hospitals, geocode_query

async def main():
    print("--- 1. Testing Haversine Distance ---")
    dist = haversine_distance(19.0760, 72.8777, 19.0800, 72.8800)
    print(f"Haversine sample distance: {dist} km")
    assert dist > 0, "Distance should be positive"

    print("\n--- 2. Testing Geocode Query (Nominatim) ---")
    try:
        geo = await geocode_query("New Delhi")
        print(f"Geocoded {len(geo)} locations for 'New Delhi':")
        for g in geo[:2]:
            print(f"  - {g.display_name} ({g.lat}, {g.lng})")
        assert len(geo) > 0, "Geocode should return results"
    except Exception as e:
        print(f"Geocode failed: {e}")

    print("\n--- 3. Testing Nearby Hospitals (Overpass API) ---")
    try:
        # Testing coordinates around Connaught Place, New Delhi (28.6315, 77.2167) with 3km radius
        hospitals = await get_nearby_hospitals(28.6315, 77.2167, radius=3000)
        print(f"Found {len(hospitals)} hospitals near Connaught Place (3km radius):")
        for h in hospitals[:5]:
            print(f"  - [{h.distance_km} km] {h.name} | Phone: {h.phone or 'Not available'} | Emergency: {h.emergency} | Addr: {h.address}")
        assert len(hospitals) > 0, "Should find hospitals in central Delhi"
        print("\nAll Backend Hospital Finder tests passed!")
    except Exception as e:
        print(f"Hospital lookup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
