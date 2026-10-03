import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Phone,
  Navigation,
  MapPin,
  Search,
  Cross,
  AlertTriangle,
  LocateFixed,
  Loader2,
  ExternalLink,
  ShieldAlert,
  Hospital as HospitalIcon,
  RefreshCw,
  Info,
} from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { HospitalMap } from "@/components/hospital-map";
import { hospitalApi, type Hospital, type GeocodeResult } from "@/lib/api";

export const Route = createFileRoute("/_app/hospitals")({
  component: HospitalFinderPage,
});

// National Emergency Numbers
const EMERGENCY_AMBULANCE = "108";
const EMERGENCY_UNIFIED = "112";

const RADIUS_OPTIONS = [
  { label: "2 km", value: 2000 },
  { label: "5 km", value: 5000 },
  { label: "10 km", value: 10000 },
  { label: "15 km", value: 15000 },
  { label: "25 km", value: 25000 },
];

function HospitalFinderPage() {
  // Location states
  const [userCoords, setUserCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [locationName, setLocationName] = useState<string>("Detecting location...");
  const [geoStatus, setGeoStatus] = useState<"idle" | "detecting" | "granted" | "denied">("idle");
  const [geoError, setGeoError] = useState<string | null>(null);

  // Search & Filter states
  const [searchQuery, setSearchQuery] = useState("");
  const [isGeocoding, setIsGeocoding] = useState(false);
  const [radiusMeters, setRadiusMeters] = useState<number>(5000);
  const [selectedHospitalId, setSelectedHospitalId] = useState<string | null>(null);

  const cardRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  // 1. Browser Geolocation Request
  const requestBrowserLocation = () => {
    if (!navigator.geolocation) {
      setGeoStatus("denied");
      setGeoError("Geolocation is not supported by your browser. Please enter your location manually.");
      setDefaultFallbackCoords();
      return;
    }

    setGeoStatus("detecting");
    setGeoError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setUserCoords({ lat: latitude, lng: longitude });
        setLocationName("Your Current Location");
        setGeoStatus("granted");
      },
      (err) => {
        console.warn("Geolocation permission error:", err);
        setGeoStatus("denied");
        setGeoError("Location permission was denied or unavailable. You can enter your city or area below.");
        setDefaultFallbackCoords();
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000,
      }
    );
  };

  const setDefaultFallbackCoords = () => {
    // Default to central New Delhi if no location granted
    setUserCoords({ lat: 28.6139, lng: 77.2090 });
    setLocationName("New Delhi (Default City)");
  };

  useEffect(() => {
    requestBrowserLocation();
  }, []);

  // 2. Fetch Nearby Hospitals using React Query
  const {
    data: hospitals = [],
    isLoading: isHospitalsLoading,
    isError: isHospitalsError,
    error: hospitalsError,
    refetch,
  } = useQuery({
    queryKey: ["nearby-hospitals", userCoords?.lat, userCoords?.lng, radiusMeters],
    queryFn: () => {
      if (!userCoords) return Promise.resolve([] as Hospital[]);
      return hospitalApi.getNearby(userCoords.lat, userCoords.lng, radiusMeters);
    },
    enabled: !!userCoords,
    staleTime: 1000 * 60 * 5, // 5 minutes cache
    retry: 1,
  });

  // 3. Manual Geocoding via Nominatim backend proxy
  const handleManualSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() || searchQuery.trim().length < 2) return;

    setIsGeocoding(true);
    setGeoError(null);
    try {
      const results: GeocodeResult[] = await hospitalApi.geocode(searchQuery.trim());
      if (results && results.length > 0) {
        const topResult = results[0];
        setUserCoords({ lat: topResult.lat, lng: topResult.lng });
        setLocationName(topResult.display_name.split(",").slice(0, 2).join(","));
        setSearchQuery("");
      } else {
        setGeoError(`No location found for "${searchQuery}". Please try another city or landmark.`);
      }
    } catch (err: any) {
      setGeoError("Failed to search location. Please check your internet connection.");
    } finally {
      setIsGeocoding(false);
    }
  };

  // 4. Scroll Card into View when Marker Clicked
  const handleSelectHospital = (hospital: Hospital) => {
    setSelectedHospitalId(hospital.id);
    const cardEl = cardRefs.current.get(hospital.id);
    if (cardEl) {
      cardEl.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* 1. Header */}
      <PageHeader
        title="Hospital Finder"
        description="Find nearby hospitals, emergency centers, and instant tap-to-call numbers."
      />

      {/* 2. Distinct Emergency Banner (Always Visible) */}
      <div className="relative overflow-hidden rounded-2xl border-2 border-red-500/40 bg-gradient-to-r from-red-600 via-rose-600 to-red-700 text-white p-4 md:p-5 shadow-lg shadow-red-500/10">
        <div className="absolute -right-8 -bottom-8 opacity-10 pointer-events-none">
          <ShieldAlert className="w-48 h-48 text-white" />
        </div>
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="relative flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/20 backdrop-blur border border-white/30 shadow-inner">
              <span className="absolute flex h-full w-full rounded-xl bg-white/30 animate-ping opacity-40"></span>
              <ShieldAlert className="h-6 w-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg tracking-tight">Immediate Medical Emergency?</span>
                <span className="bg-white/20 text-[11px] font-extrabold uppercase px-2 py-0.5 rounded-full border border-white/25">
                  24/7 Priority
                </span>
              </div>
              <p className="text-sm text-red-100 mt-0.5 max-w-xl">
                For life-threatening accidents, severe trauma, or heart emergencies, call national ambulance dispatch immediately.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
            {/* National Ambulance Call (108) */}
            <a
              href={`tel:${EMERGENCY_AMBULANCE}`}
              className="flex-1 md:flex-initial inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-white text-red-700 font-bold text-sm shadow hover:bg-red-50 active:scale-95 transition-all"
            >
              <Phone className="h-4 w-4 fill-red-600 text-red-600" />
              <span>Call Ambulance ({EMERGENCY_AMBULANCE})</span>
            </a>

            {/* Unified Emergency Call (112) */}
            <a
              href={`tel:${EMERGENCY_UNIFIED}`}
              className="flex-1 md:flex-initial inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-red-900/60 hover:bg-red-900/80 text-white font-semibold text-sm border border-white/20 active:scale-95 transition-all"
            >
              <Phone className="h-4 w-4" />
              <span>Emergency ({EMERGENCY_UNIFIED})</span>
            </a>
          </div>
        </div>
      </div>

      {/* 3. Location Bar & Search Controls */}
      <Card className="rounded-2xl border bg-card p-4 shadow-sm">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
          {/* Active location indicator + Re-detect button */}
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-muted text-foreground font-medium">
              <MapPin className="h-4 w-4 text-primary shrink-0" />
              <span className="truncate max-w-[240px] md:max-w-xs">{locationName}</span>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={requestBrowserLocation}
              disabled={geoStatus === "detecting"}
              className="rounded-lg gap-1.5 text-xs h-9"
            >
              {geoStatus === "detecting" ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <LocateFixed className="h-3.5 w-3.5 text-primary" />
              )}
              <span>{geoStatus === "detecting" ? "Detecting..." : "Detect My Location"}</span>
            </Button>
          </div>

          {/* Manual Location Search Input */}
          <form onSubmit={handleManualSearch} className="flex items-center gap-2 flex-1 max-w-md">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search city, area, or landmark..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 h-9 rounded-lg text-sm bg-muted/40"
              />
            </div>
            <Button
              type="submit"
              size="sm"
              disabled={isGeocoding || !searchQuery.trim()}
              className="h-9 rounded-lg text-xs gap-1"
            >
              {isGeocoding ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Search"}
            </Button>
          </form>

          {/* Radius Toggle Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0">
            <span className="text-xs text-muted-foreground font-medium mr-1">Radius:</span>
            {RADIUS_OPTIONS.map((opt) => {
              const active = radiusMeters === opt.value;
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setRadiusMeters(opt.value)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors shrink-0 ${
                    active
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground"
                  }`}
                >
                  {opt.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Geolocation Notice / Error Banner */}
        {geoError && (
          <div className="mt-3 flex items-center gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-700 dark:text-amber-400 text-xs">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{geoError}</span>
          </div>
        )}
      </Card>

      {/* 4. Main Split Content: Map & Hospital Cards List */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left / Top: Interactive Leaflet Map (Sticky on Desktop) */}
        <div className="lg:col-span-7 lg:sticky lg:top-24 space-y-2">
          <div className="h-[380px] lg:h-[580px] w-full rounded-2xl overflow-hidden border border-border shadow-md bg-muted/20">
            <HospitalMap
              userLocation={userCoords}
              hospitals={hospitals}
              selectedHospitalId={selectedHospitalId}
              onSelectHospital={handleSelectHospital}
            />
          </div>
          <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
            <span>Click any marker to view hospital details & call options</span>
            <span className="font-semibold text-foreground">
              {hospitals.length} {hospitals.length === 1 ? "hospital" : "hospitals"} found
            </span>
          </div>
        </div>

        {/* Right / Bottom: Hospital Cards List */}
        <div className="lg:col-span-5 space-y-3.5">
          {/* Loading Skeletons */}
          {isHospitalsLoading && (
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <Card key={i} className="rounded-2xl border p-4 space-y-3">
                  <div className="flex justify-between items-start">
                    <Skeleton className="h-5 w-48 rounded" />
                    <Skeleton className="h-4 w-16 rounded-full" />
                  </div>
                  <Skeleton className="h-4 w-full rounded" />
                  <div className="flex gap-2 pt-2">
                    <Skeleton className="h-8 w-28 rounded-lg" />
                    <Skeleton className="h-8 w-24 rounded-lg" />
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* Overpass Timeout / Service Error State */}
          {!isHospitalsLoading && isHospitalsError && (
            <Card className="rounded-2xl border border-destructive/30 bg-destructive/5 p-6 text-center space-y-4">
              <div className="mx-auto w-12 h-12 rounded-full bg-destructive/10 text-destructive flex items-center justify-center">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div>
                <h3 className="font-semibold text-base">Hospital search is temporarily slow</h3>
                <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
                  The public OpenStreetMap lookup service is experiencing heavy load. Please try again or search a different area.
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
                className="rounded-xl gap-2 text-xs"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Retry Hospital Lookup
              </Button>
            </Card>
          )}

          {/* Empty Results State */}
          {!isHospitalsLoading && !isHospitalsError && hospitals.length === 0 && (
            <Card className="rounded-2xl border p-8 text-center space-y-4 bg-card/60">
              <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center text-muted-foreground">
                <HospitalIcon className="h-6 w-6" />
              </div>
              <div>
                <h3 className="font-semibold text-base">No hospitals found within {radiusMeters / 1000} km</h3>
                <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
                  Try expanding your search radius or search for a nearby major city.
                </p>
              </div>
              <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
                {radiusMeters < 10000 && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setRadiusMeters(10000)}
                    className="rounded-xl text-xs"
                  >
                    Expand to 10 km
                  </Button>
                )}
                {radiusMeters < 25000 && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setRadiusMeters(25000)}
                    className="rounded-xl text-xs"
                  >
                    Expand to 25 km
                  </Button>
                )}
              </div>
            </Card>
          )}

          {/* Hospital Cards List */}
          {!isHospitalsLoading && !isHospitalsError && hospitals.length > 0 && (
            <div className="space-y-3 max-h-[620px] overflow-y-auto pr-1">
              {hospitals.map((h) => {
                const isSelected = h.id === selectedHospitalId;
                const directionsUrl = `https://www.google.com/maps/dir/?api=1&destination=${h.lat},${h.lng}`;

                return (
                  <div
                    key={h.id}
                    ref={(el) => {
                      if (el) cardRefs.current.set(h.id, el);
                      else cardRefs.current.delete(h.id);
                    }}
                  >
                    <Card
                      onClick={() => setSelectedHospitalId(h.id)}
                      className={`rounded-2xl border p-4 transition-all cursor-pointer ${
                        isSelected
                          ? "border-primary ring-2 ring-primary/20 bg-accent/20 shadow-md scale-[1.01]"
                          : "hover:border-border/80 hover:bg-muted/40 shadow-sm"
                      }`}
                    >
                      <CardContent className="p-0 space-y-2.5">
                        {/* Title & Distance */}
                        <div className="flex items-start justify-between gap-2">
                          <div className="space-y-1 flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <h3 className="font-bold text-sm text-foreground leading-snug truncate">
                                {h.name}
                              </h3>
                              {h.emergency && (
                                <span className="bg-red-500/10 text-red-600 dark:text-red-400 font-extrabold text-[10px] px-2 py-0.5 rounded-full border border-red-500/20 shrink-0">
                                  24/7 Emergency
                                </span>
                              )}
                            </div>
                          </div>
                          <Badge variant="secondary" className="shrink-0 text-xs font-semibold rounded-lg">
                            {h.distance_km} km away
                          </Badge>
                        </div>

                        {/* Address */}
                        <div className="flex items-start gap-2 text-xs text-muted-foreground leading-relaxed">
                          <MapPin className="h-3.5 w-3.5 shrink-0 text-muted-foreground/70 mt-0.5" />
                          <span className="line-clamp-2">{h.address}</span>
                        </div>

                        {/* Phone Number / Fallback */}
                        <div className="flex items-center gap-2 text-xs pt-0.5">
                          <Phone className="h-3.5 w-3.5 shrink-0 text-muted-foreground/70" />
                          {h.phone ? (
                            <a
                              href={`tel:${h.phone}`}
                              onClick={(e) => e.stopPropagation()}
                              className="font-semibold text-emerald-600 dark:text-emerald-400 hover:underline inline-flex items-center gap-1"
                            >
                              <span>{h.phone}</span>
                              <span className="text-[10px] font-normal text-muted-foreground">(Tap to call)</span>
                            </a>
                          ) : (
                            <span className="text-muted-foreground/80 italic">
                              Contact number not available
                            </span>
                          )}
                        </div>

                        {/* Action Buttons */}
                        <div className="flex items-center gap-2 pt-2 border-t border-border/60">
                          {/* Call Button */}
                          {h.phone ? (
                            <Button
                              asChild
                              size="sm"
                              variant="default"
                              className="h-8 rounded-lg text-xs gap-1.5 flex-1 bg-emerald-600 hover:bg-emerald-700 text-white"
                            >
                              <a href={`tel:${h.phone}`} onClick={(e) => e.stopPropagation()}>
                                <Phone className="h-3 w-3" />
                                <span>Call Hospital</span>
                              </a>
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              variant="outline"
                              disabled
                              className="h-8 rounded-lg text-xs gap-1.5 flex-1 opacity-50 cursor-not-allowed"
                            >
                              <Phone className="h-3 w-3" />
                              <span>No Phone Listed</span>
                            </Button>
                          )}

                          {/* Directions Button */}
                          <Button
                            asChild
                            size="sm"
                            variant="outline"
                            className="h-8 rounded-lg text-xs gap-1.5 flex-1"
                          >
                            <a
                              href={directionsUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <Navigation className="h-3 w-3 text-primary" />
                              <span>Directions</span>
                              <ExternalLink className="h-2.5 w-2.5 opacity-60" />
                            </a>
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* 5. Public OpenStreetMap Data Disclaimer */}
      <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-muted/50 border border-border text-muted-foreground text-xs leading-relaxed">
        <Info className="h-4 w-4 shrink-0 text-muted-foreground mt-0.5" />
        <p>
          <span className="font-semibold text-foreground">Data Notice:</span> Hospital locations, facilities, and phone numbers are queried in real-time from public OpenStreetMap community data. Contact numbers may not be verified ambulance lines or staffed 24/7. In acute medical crises, always call the national emergency dispatch line (<span className="font-semibold text-foreground">108</span> or <span className="font-semibold text-foreground">112</span>) directly.
        </p>
      </div>
    </div>
  );
}
