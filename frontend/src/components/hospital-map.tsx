import React, { useEffect, useRef } from "react";
import L from "leaflet";
import type { Hospital } from "@/lib/api";

interface HospitalMapProps {
  userLocation: { lat: number; lng: number } | null;
  hospitals: Hospital[];
  selectedHospitalId: string | null;
  onSelectHospital: (hospital: Hospital) => void;
  className?: string;
}

// Inline SVG Leaflet DivIcons to avoid external asset dependencies or broken PNG paths
function createUserIcon(): L.DivIcon {
  return L.divIcon({
    className: "user-loc-icon",
    html: `
      <div style="position: relative; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;">
        <div class="radar-pulse-ring" style="position: absolute; inset: 0; border-radius: 9999px; background: rgba(37, 99, 235, 0.45);"></div>
        <div style="position: absolute; width: 22px; height: 22px; border-radius: 9999px; background: rgba(59, 130, 246, 0.25); border: 2px solid rgba(147, 197, 253, 0.9);"></div>
        <div style="position: relative; width: 14px; height: 14px; border-radius: 9999px; background: #2563eb; border: 2.5px solid #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></div>
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    popupAnchor: [0, -18],
  });
}

function createHospitalIcon(isSelected: boolean, hasEmergency: boolean | null): L.DivIcon {
  const pinColor = isSelected ? "#dc2626" : hasEmergency ? "#e11d48" : "#ef4444";
  const size = isSelected ? 42 : 34;
  const height = isSelected ? 50 : 42;

  const haloHtml = isSelected
    ? `<div style="position: absolute; inset: -8px; border-radius: 9999px; background: rgba(239, 68, 68, 0.35); filter: blur(4px); animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;"></div>`
    : "";

  const badgeHtml = hasEmergency
    ? `<div style="position: absolute; top: -4px; right: -4px; background: #991b1b; color: #fff; font-size: 8px; font-weight: 800; padding: 1px 4px; border-radius: 4px; border: 1px solid #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">24/7</div>`
    : "";

  return L.divIcon({
    className: `hospital-marker-${isSelected ? "selected" : "normal"}`,
    html: `
      <div style="position: relative; width: ${size}px; height: ${height}px; display: flex; align-items: center; justify-content: center; transition: all 0.2s ease;">
        ${haloHtml}
        ${badgeHtml}
        <svg width="${size}" height="${height}" viewBox="0 0 34 42" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 3px 6px rgba(0,0,0,0.25));">
          <path d="M17 0C7.61 0 0 7.61 0 17C0 27.5 15.2 40.8 15.8 41.3C16.2 41.7 16.8 41.7 17.2 41.3C17.8 40.8 33 27.5 33 17C33 7.61 25.39 0 17 0Z" fill="${pinColor}"/>
          <circle cx="16.5" cy="16.5" r="10.5" fill="#ffffff"/>
          <rect x="14.5" y="10" width="4" height="13" rx="1.5" fill="${pinColor}"/>
          <rect x="10" y="14.5" width="13" height="4" rx="1.5" fill="${pinColor}"/>
        </svg>
      </div>
    `,
    iconSize: [size, height],
    iconAnchor: [size / 2, height],
    popupAnchor: [0, -height + 4],
  });
}

export function HospitalMap({
  userLocation,
  hospitals,
  selectedHospitalId,
  onSelectHospital,
  className = "",
}: HospitalMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const userMarkerRef = useRef<L.Marker | null>(null);
  const hospitalMarkersRef = useRef<Map<string, L.Marker>>(new Map());

  // 1. Initialize Leaflet Map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    // Default center (Connaught Place, New Delhi or user fallback)
    const initialLat = userLocation ? userLocation.lat : 28.6139;
    const initialLng = userLocation ? userLocation.lng : 77.2090;

    const map = L.map(containerRef.current, {
      center: [initialLat, initialLng],
      zoom: 13,
      zoomControl: false,
    });

    L.control.zoom({ position: "bottomright" }).addTo(map);

    // OpenStreetMap standard tiles
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    mapRef.current = map;

    // Invalidate size on initial mount and on window resize
    const handleResize = () => {
      map.invalidateSize();
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // 2. Update User Location Marker
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (userLocation) {
      if (!userMarkerRef.current) {
        const marker = L.marker([userLocation.lat, userLocation.lng], {
          icon: createUserIcon(),
          zIndexOffset: 1000,
        }).addTo(map);
        marker.bindPopup(`
          <div style="padding: 10px 14px; font-size: 13px; font-weight: 600;">
            <div style="color: #2563eb; display: flex; align-items: center; gap: 6px;">
              <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#2563eb;"></span>
              Your Location
            </div>
          </div>
        `);
        userMarkerRef.current = marker;
      } else {
        userMarkerRef.current.setLatLng([userLocation.lat, userLocation.lng]);
      }
    } else if (userMarkerRef.current) {
      userMarkerRef.current.remove();
      userMarkerRef.current = null;
    }
  }, [userLocation]);

  // 3. Update Hospital Markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Clear existing markers
    hospitalMarkersRef.current.forEach((marker) => marker.remove());
    hospitalMarkersRef.current.clear();

    if (hospitals.length === 0) return;

    const bounds = L.latLngBounds([]);
    if (userLocation) {
      bounds.extend([userLocation.lat, userLocation.lng]);
    }

    hospitals.forEach((h) => {
      const isSelected = h.id === selectedHospitalId;
      const marker = L.marker([h.lat, h.lng], {
        icon: createHospitalIcon(isSelected, h.emergency),
        zIndexOffset: isSelected ? 500 : 100,
      }).addTo(map);

      // Popup content with tap-to-call link and directions
      const phoneHtml = h.phone
        ? `<div style="margin-top: 6px; font-size: 13px;">
             <a href="tel:${h.phone}" style="display: inline-flex; align-items: center; gap: 6px; color: #16a34a; font-weight: 600; text-decoration: none; background: rgba(22,163,74,0.1); padding: 4px 10px; border-radius: 6px;">
               📞 Call: ${h.phone}
             </a>
           </div>`
        : `<div style="margin-top: 6px; font-size: 12px; color: #6b7280; font-style: italic;">
             Contact number not available
           </div>`;

      const directionsUrl = `https://www.google.com/maps/dir/?api=1&destination=${h.lat},${h.lng}`;

      const popupContent = `
        <div style="padding: 12px 14px; max-width: 250px; font-family: inherit;">
          <div style="font-weight: 700; font-size: 14px; line-height: 1.3; color: #111827;">${h.name}</div>
          <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px; font-size: 12px;">
            <span style="background: #f3f4f6; color: #374151; font-weight: 600; padding: 2px 7px; border-radius: 4px;">
              ${h.distance_km} km away
            </span>
            ${h.emergency ? `<span style="background: #fee2e2; color: #991b1b; font-weight: 700; padding: 2px 7px; border-radius: 4px;">24/7 Emergency</span>` : ""}
          </div>
          <div style="margin-top: 6px; font-size: 12px; color: #4b5563; line-height: 1.3;">
            ${h.address}
          </div>
          ${phoneHtml}
          <div style="margin-top: 8px; border-top: 1px solid #e5e7eb; padding-top: 6px;">
            <a href="${directionsUrl}" target="_blank" rel="noopener noreferrer" style="font-size: 12px; color: #2563eb; text-decoration: none; font-weight: 600;">
              ↗ Get Directions on Map
            </a>
          </div>
        </div>
      `;

      marker.bindPopup(popupContent);

      marker.on("click", () => {
        onSelectHospital(h);
      });

      hospitalMarkersRef.current.set(h.id, marker);
      bounds.extend([h.lat, h.lng]);
    });

    // Auto-fit bounds if markers exist and no hospital is specifically selected
    if (bounds.isValid() && !selectedHospitalId) {
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
    }
  }, [hospitals, userLocation]);

  // 4. Sync Selection State: Pan to selected hospital marker and open popup
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !selectedHospitalId) return;

    const selectedHospital = hospitals.find((h) => h.id === selectedHospitalId);
    const marker = hospitalMarkersRef.current.get(selectedHospitalId);

    // Update icons for all markers to reflect selected state
    hospitalMarkersRef.current.forEach((m, id) => {
      const h = hospitals.find((item) => item.id === id);
      const isSel = id === selectedHospitalId;
      m.setIcon(createHospitalIcon(isSel, h?.emergency ?? null));
      m.setZIndexOffset(isSel ? 500 : 100);
    });

    if (marker && selectedHospital) {
      map.panTo([selectedHospital.lat, selectedHospital.lng], {
        animate: true,
        duration: 0.5,
      });
      if (!marker.isPopupOpen()) {
        marker.openPopup();
      }
    }
  }, [selectedHospitalId, hospitals]);

  return (
    <div className={`relative w-full h-full min-h-[350px] rounded-2xl overflow-hidden border border-border shadow-inner ${className}`}>
      <div ref={containerRef} className="w-full h-full" style={{ minHeight: "350px" }} />
    </div>
  );
}
