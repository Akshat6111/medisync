// Centralized API client for MediSync backend
const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "https://YOUR_BACKEND_URL";

const TOKEN_KEY = "medisync_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

function parseErrorMessage(data: unknown, fallback: string): string {
  if (!data || typeof data !== "object") return fallback;
  const d = data as { detail?: unknown; message?: unknown };
  if (typeof d.detail === "string") return d.detail;
  if (Array.isArray(d.detail)) {
    return d.detail
      .map((e: { loc?: unknown[]; msg?: string }) => {
        const field = Array.isArray(e.loc) ? e.loc.slice(1).join(".") : "";
        return field ? `${field}: ${e.msg}` : e.msg;
      })
      .filter(Boolean)
      .join(", ") || fallback;
  }
  if (typeof d.message === "string") return d.message;
  return fallback;
}

type RequestOpts = {
  method?: string;
  body?: unknown;
  form?: URLSearchParams;
  formData?: FormData;
  headers?: Record<string, string>;
  auth?: boolean;
};

let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn;
}

export async function apiRequest<T = unknown>(path: string, opts: RequestOpts = {}): Promise<T> {
  const { method = "GET", body, form, formData, headers = {}, auth = true } = opts;
  const h: Record<string, string> = { ...headers };
  let payload: BodyInit | undefined;

  if (formData) {
    payload = formData;
  } else if (form) {
    h["Content-Type"] = "application/x-www-form-urlencoded";
    payload = form.toString();
  } else if (body !== undefined) {
    h["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }


  if (auth) {
    const t = getToken();
    if (t) h["Authorization"] = `Bearer ${t}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, { method, headers: h, body: payload });

  if (res.status === 401 && auth) {
    onUnauthorized?.();
    throw new ApiError(401, "Session expired. Please sign in again.");
  }

  const text = await res.text();
  let data: unknown = null;
  if (text) {
    try { data = JSON.parse(text); } catch { data = text; }
  }

  if (!res.ok) {
    throw new ApiError(res.status, parseErrorMessage(data, `Request failed (${res.status})`), data);
  }

  return data as T;
}

export const api = {
  get: <T>(path: string) => apiRequest<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown) => apiRequest<T>(path, { method: "POST", body }),
  put: <T>(path: string, body?: unknown) => apiRequest<T>(path, { method: "PUT", body }),
  patch: <T>(path: string, body?: unknown) => apiRequest<T>(path, { method: "PATCH", body }),
  del: <T>(path: string) => apiRequest<T>(path, { method: "DELETE" }),
  postForm: <T>(path: string, form: URLSearchParams, auth = false) =>
    apiRequest<T>(path, { method: "POST", form, auth }),
  upload: <T>(path: string, formData: FormData) =>
    apiRequest<T>(path, { method: "POST", formData }),
};

// ---------- Types ----------
export type Role = "PATIENT" | "CAREGIVER" | "ADMIN";

export interface AuthUser {
  id: string;
  full_name: string;
  email: string;
  role: Role;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface Patient {
  id: string;
  full_name: string;
  date_of_birth: string;
  gender: string;
  height_cm: number | null;
  weight_kg: number | null;
  blood_group: string | null;
  allergies: string | null;
  medical_conditions: string | null;
  wake_up_time: string;
  breakfast_time: string;
  lunch_time: string;
  dinner_time: string;
  sleep_time: string;
  created_at: string;
  updated_at: string;
}

export type PatientCreate = Omit<Patient, "id" | "created_at" | "updated_at">;

export interface Medication {
  id: string;
  name: string;
  dosage_amount: number;
  dosage_unit: string;
  frequency_per_day: number;
  duration_days: number;
  route: string;
  with_food: boolean;
  empty_stomach: boolean;
  bedtime_only: boolean;
  start_date: string;
  end_date: string;
  notes: string | null;
  scheduled_time?: string[] | null;
  created_at: string;
}

export type MedicationCreate = Omit<Medication, "id" | "end_date" | "created_at">;

export interface ScheduleItem {
  medication_id: string;
  medication_name: string;
  dose_index: number;
  scheduled_time: string;
}

export interface Conflict {
  conflict: boolean;
  reason: string;
  medication_a_id: string | null;
  medication_b_id: string | null;
  required_gap_hours: number;
  detail: string | null;
}

export interface ScheduleResponse {
  success: boolean;
  schedule: ScheduleItem[];
  conflict: Conflict | null;
}

export type LogStatus = "pending" | "taken" | "missed" | "skipped" | "late";

export interface MedicationLog {
  id: string;
  medication_id: string;
  medication_name?: string;
  dose_index: number;
  scheduled_time: string;
  taken_time: string | null;
  status: LogStatus;
  notes: string | null;
  created_at: string;
}

export interface AdherenceStats {
  total_doses: number;
  eligible_doses: number;
  taken: number;
  missed: number;
  late: number;
  skipped: number;
  pending: number;
  adherence_rate: number;
}

export interface Notification {
  id: string;
  medication_log_id: string;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

// ---------- Lab Reports (ReportBrief) ----------
export type LabReportFlag = "normal" | "high" | "low" | "unknown";
export type LabReportStatus = "processing" | "completed" | "failed";

export interface LabReportValue {
  id: string;
  report_id: string;
  test_name: string;
  value: number;
  unit: string;
  reference_low: number | null;
  reference_high: number | null;
  flag: LabReportFlag;
}

export interface LabReportListItem {
  id: string;
  patient_id: string;
  original_filename: string;
  uploaded_at: string;
  status: LabReportStatus;
  summary: string | null;
  values_count: number;
}

export interface LabReport {
  id: string;
  patient_id: string;
  original_filename: string;
  uploaded_at: string;
  status: LabReportStatus;
  raw_text: string | null;
  summary: string | null;
  values: LabReportValue[];
}

export const labReportApi = {
  list: () => api.get<LabReportListItem[]>("/lab-reports/"),
  get: (id: string) => api.get<LabReport>(`/lab-reports/${id}`),
  upload: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.upload<LabReport>("/lab-reports/", formData);
  },
  delete: (id: string) => api.del<{ message: string }>(`/lab-reports/${id}`),
};

// ---------- CycleSync ----------
export interface CycleLog {
  id: string;
  patient_id: string;
  start_date: string;
  end_date: string | null;
  created_at: string;
}

export interface CycleLogCreate {
  start_date: string;
  end_date?: string | null;
}

export interface CycleLogUpdate {
  start_date?: string;
  end_date?: string | null;
}

export interface CyclePrediction {
  average_cycle_length: number | null;
  std_deviation: number | null;
  current_cycle_day: number | null;
  predicted_next_start: string | null;
  predicted_window_start: string | null;
  predicted_window_end: string | null;
  anomaly_flag: boolean;
  anomaly_reason: string | null;
  total_cycles_logged: number;
}

export const cycleApi = {
  list: () => api.get<CycleLog[]>("/cycles/"),
  prediction: () => api.get<CyclePrediction>("/cycles/prediction"),
  create: (body: CycleLogCreate) => api.post<CycleLog>("/cycles/", body),
  update: (id: string, body: CycleLogUpdate) => api.patch<CycleLog>(`/cycles/${id}`, body),
  delete: (id: string) => api.del<{ message: string }>(`/cycles/${id}`),
};

// ---------- HospitalFinder ----------
export interface Hospital {
  id: string;
  name: string;
  lat: number;
  lng: number;
  address: string;
  phone: string | null;
  distance_km: number;
  emergency: boolean | null;
  source?: string;
}

export interface GeocodeResult {
  lat: number;
  lng: number;
  display_name: string;
}

export const hospitalApi = {
  getNearby: (lat: number, lng: number, radius = 5000) =>
    api.get<Hospital[]>(`/hospitals/nearby?lat=${lat}&lng=${lng}&radius=${radius}`),
  geocode: (query: string) =>
    api.get<GeocodeResult[]>(`/hospitals/geocode?query=${encodeURIComponent(query)}`),
};

// ---------- RxParse (Prescription Digitizer) ----------
export interface ParsedMedicationCandidate {
  raw_text_snippet: string;
  matched_drug_name: string;
  match_confidence: number;
  dosage_amount: number;
  dosage_unit: string;
  frequency_per_day: number;
  suggested_times: string[];
  duration_days: number;
  route: string;
  with_food: boolean;
  empty_stomach: boolean;
  bedtime_only: boolean;
  notes: string | null;
  needs_review: {
    drug_name: boolean;
    dosage: boolean;
    frequency: boolean;
    times: boolean;
  };
}

export interface PrescriptionParseResponse {
  success: boolean;
  raw_text: string;
  candidates: ParsedMedicationCandidate[];
  total_found: number;
}

export const prescriptionApi = {
  parse: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.upload<PrescriptionParseResponse>("/prescriptions/parse", formData);
  },
  syncManualLogs: () => api.post<{ success: boolean; synced_count: number }>("/medications/sync-manual-logs"),
};

// ---------- GenericFinder ----------
export interface PharmacyPriceItem {
  brand_name: string;
  price: number;
  pharmacy_source: string;
  url: string;
  is_generic?: boolean;
  is_cached?: boolean;
  is_fallback?: boolean;
  dosage_form?: string;
  is_searched_medicine?: boolean;
}

export interface PMBJPReference {
  available: boolean;
  generic_name: string;
  typical_price: number;
  market_avg_price: number;
  savings_percent: number;
  product_url?: string;
  kendra_url?: string;
}

export interface GenericFinderResponse {
  query_matched_to: string;
  generic_name: string;
  category: string;
  description?: string;
  how_to_use?: string;
  common_strengths?: string[];
  side_effects?: string[];
  dosage_form: string;
  active_ingredients?: string[];
  pmbjp_reference?: PMBJPReference | null;
  all_generic_substitutes: string[];
  other_form_substitutes?: Record<string, string[]>;
  results: PharmacyPriceItem[];
  other_form_results?: PharmacyPriceItem[];
  cheapest_option?: PharmacyPriceItem | null;
  most_expensive_price?: number | null;
  estimated_savings_percent: number;
  sources_checked: string[];
  sources_failed: string[];
  is_salt_dictionary_match: boolean;
}

export interface PopularCategoriesResponse {
  categories: {
    category: string;
    medicines: string[];
  }[];
}

export interface SavingsCalculationRequest {
  medicine_name: string;
  doses_per_day: number;
  duration_days: number;
}

export interface SavingsCalculationResponse {
  medicine_name: string;
  generic_name: string;
  doses_per_day: number;
  duration_days: number;
  total_tablets_needed: number;
  current_brand_price_per_unit: number;
  cheapest_generic_price_per_unit: number;
  pmbjp_price_per_unit?: number | null;
  brand_total_cost: number;
  generic_total_cost: number;
  pmbjp_total_cost?: number | null;
  total_savings_inr: number;
  savings_percent: number;
  annual_projected_savings_inr: number;
}

export interface CabinetSavingsItem {
  medication_name: string;
  generic_name?: string | null;
  current_estimated_price: number;
  cheapest_substitute_price: number;
  savings_percent: number;
  monthly_savings_inr: number;
  annual_savings_inr: number;
  recommended_generic_name: string;
}

export interface CabinetSavingsResponse {
  total_medications_analyzed: number;
  medications_with_substitutes: number;
  total_monthly_savings_inr: number;
  total_annual_savings_inr: number;
  items: CabinetSavingsItem[];
}

export const genericFinderApi = {
  search: (query: string) =>
    api.get<GenericFinderResponse>(`/generic-finder/search?query=${encodeURIComponent(query)}`),
  popular: () => api.get<PopularCategoriesResponse>("/generic-finder/popular"),
  calculateSavings: (payload: SavingsCalculationRequest) =>
    api.post<SavingsCalculationResponse>("/generic-finder/calculate-savings", payload),
  cabinetSavings: () => api.get<CabinetSavingsResponse>("/generic-finder/cabinet-savings"),
};




