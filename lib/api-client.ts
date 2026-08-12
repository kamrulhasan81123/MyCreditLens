/**
 * MyCreditLens API Client
 * 
 * Centralized HTTP client for all backend API communication.
 * Handles authentication, token refresh, and error normalization.
 */

import type { Application, Borrower, BorrowerSegment, RiskBand } from "@/lib/types"
import { getSupabaseClient } from "@/lib/supabase-client"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ApiError {
  status: number
  detail: string
  errors?: Record<string, string[]>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserProfile {
  id: string
  email: string
  full_name: string
  role: "borrower" | "credit_analyst" | "compliance_reviewer" | "admin"
  is_active: boolean
  created_at: string
}

// ---------------------------------------------------------------------------
// Token management
// ---------------------------------------------------------------------------

const TOKEN_KEY = "mcl_access_token"
const REFRESH_KEY = "mcl_refresh_token"

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem(TOKEN_KEY)
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(TOKEN_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

// ---------------------------------------------------------------------------
// Core request function
// ---------------------------------------------------------------------------

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAccessToken()
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  const url = `${API_BASE_URL}${endpoint}`
  const response = await fetch(url, {
    ...options,
    headers,
  })

  // Handle 401 - try token refresh
  if (response.status === 401 && token) {
    const refreshed = await refreshAccessToken()
    if (refreshed) {
      headers["Authorization"] = `Bearer ${getAccessToken()}`
      const retryResponse = await fetch(url, {
        ...options,
        headers,
      })
      return handleResponse<T>(retryResponse)
    }
    clearTokens()
    if (typeof window !== "undefined") {
      window.location.href = "/sign-in"
    }
    throw { status: 401, detail: "Session expired" } as ApiError
  }

  return handleResponse<T>(response)
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = "An unexpected error occurred"
    let errors: Record<string, string[]> | undefined

    try {
      const body = await response.json()
      detail = body.detail || detail
      errors = body.errors
    } catch {
      // Non-JSON response
    }

    throw { status: response.status, detail, errors } as ApiError
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = localStorage.getItem(REFRESH_KEY)
  if (!refresh) return false

  try {
    const supabase = getSupabaseClient()
    if (supabase) {
      const { data, error } = await supabase.auth.refreshSession({ refresh_token: refresh })
      if (!error && data.session) {
        setTokens(data.session.access_token, data.session.refresh_token)
        return true
      }
      return false
    }
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    })

    if (response.ok) {
      const data: TokenResponse = await response.json()
      setTokens(data.access_token, data.refresh_token)
      return true
    }
  } catch {
    // Refresh failed
  }

  return false
}

// ---------------------------------------------------------------------------
// Convenience methods
// ---------------------------------------------------------------------------

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),

  post: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(endpoint: string) =>
    request<T>(endpoint, { method: "DELETE" }),

  upload: <T>(endpoint: string, formData: FormData) => {
    const token = getAccessToken()
    const headers: Record<string, string> = {}
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
    return fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers,
      body: formData,
    }).then(handleResponse<T>)
  },
}

// ---------------------------------------------------------------------------
// Auth API
// ---------------------------------------------------------------------------

export const authApi = {
  register: (data: { email: string; password: string; full_name: string; role: string }) =>
    api.post<TokenResponse>("/auth/register", data),

  login: (data: { email: string; password: string }) =>
    api.post<TokenResponse>("/auth/login", data),

  me: () => api.get<UserProfile>("/auth/me"),

  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post("/auth/change-password", data),
}

// ---------------------------------------------------------------------------
// Borrowers API
// ---------------------------------------------------------------------------

export const borrowersApi = {
  list: (params?: { page?: number; page_size?: number; search?: string }) => {
    const searchParams = new URLSearchParams()
    if (params?.page) searchParams.set("page", String(params.page))
    if (params?.page_size) searchParams.set("page_size", String(params.page_size))
    if (params?.search) searchParams.set("search", params.search)
    const qs = searchParams.toString()
    return api.get<PaginatedResponse<BorrowerDto>>(`/borrowers${qs ? `?${qs}` : ""}`).then((response) => ({
      ...response,
      items: response.items.map(mapBorrower),
    }))
  },

  get: (id: string) => api.get<BorrowerDto>(`/borrowers/${id}`).then(mapBorrower),

  me: () => api.get<BorrowerDto>("/borrowers/me"),

  updateMe: (data: Record<string, unknown>) => api.put<BorrowerDto>("/borrowers/me", data),

  create: (data: any) => api.post<any>("/borrowers", data),

  update: (id: string, data: any) => api.put<any>(`/borrowers/${id}`, data),
}

// ---------------------------------------------------------------------------
// Applications API
// ---------------------------------------------------------------------------

export const applicationsApi = {
  list: (params?: { page?: number; page_size?: number; status?: string; risk_band?: string }) => {
    const searchParams = new URLSearchParams()
    if (params?.page) searchParams.set("page", String(params.page))
    if (params?.page_size) searchParams.set("page_size", String(params.page_size))
    if (params?.status) searchParams.set("status", params.status)
    if (params?.risk_band) searchParams.set("risk_band", params.risk_band)
    const qs = searchParams.toString()
    return api.get<PaginatedResponse<ApplicationDto>>(`/applications${qs ? `?${qs}` : ""}`).then((response) => ({
      ...response,
      items: response.items.map(mapApplication),
    }))
  },

  get: (id: string) => api.get<ApplicationDto>(`/applications/${id}`).then(mapApplication),

  create: (data: { purpose: string; requested_amount: number; requested_term_months?: number }) =>
    api.post<ApplicationDto>("/applications", data),

  update: (id: string, data: any) => api.put<any>(`/applications/${id}`, data),

  submit: (id: string) => api.post<any>(`/applications/${id}/submit`),
}

// ---------------------------------------------------------------------------
// Scoring API
// ---------------------------------------------------------------------------

export const scoringApi = {
  score: (applicationId: string, modelVersion?: string) =>
    api.post<any>(
      `/applications/${applicationId}/score${modelVersion ? `?model_version=${encodeURIComponent(modelVersion)}` : ""}`
    ),

  getPrediction: (applicationId: string) =>
    api.get<any>(`/applications/${applicationId}/predictions`),

  getExplanation: (applicationId: string) =>
    api.get<any>(`/applications/${applicationId}/explanations`),

}

export const aiApi = {
  counterfactuals: (applicationId: string, targetProbability?: number) =>
    api.post<any>(`/applications/${applicationId}/counterfactuals`, {
      target_probability: targetProbability,
      limit: 5,
    }),
  stressTests: (applicationId: string) =>
    api.post<any>(`/applications/${applicationId}/stress-tests`),
}

// ---------------------------------------------------------------------------
// Data Sources API
// ---------------------------------------------------------------------------

export const dataSourcesApi = {
  list: (applicationId: string) =>
    api.get<any[]>(`/applications/${applicationId}/data-sources`),

  upload: (applicationId: string, file: File, sourceType: string) => {
    const formData = new FormData()
    formData.append("file", file)
    return api.upload<any>(
      `/applications/${applicationId}/data-sources?source_type=${encodeURIComponent(sourceType)}`,
      formData,
    )
  },
}

export const consentsApi = {
  list: (applicationId: string) => api.get<any[]>(`/applications/${applicationId}/consents`),
  grant: (applicationId: string, dataSourceType: string) =>
    api.post<any>(`/applications/${applicationId}/consents`, { data_source_type: dataSourceType }),
  revoke: (applicationId: string, consentId: string) =>
    api.post<any>(`/applications/${applicationId}/consents/${consentId}/revoke`),
}

// ---------------------------------------------------------------------------
// Decisions API
// ---------------------------------------------------------------------------

export const decisionsApi = {
  create: (data: { application_id: string; decision: string; reason: string; override?: boolean; override_reason?: string }) =>
    api.post<any>(`/applications/${data.application_id}/decisions`, data),

  list: (applicationId: string) =>
    api.get<any[]>(`/applications/${applicationId}/decisions`),
}

// ---------------------------------------------------------------------------
// Appeals API
// ---------------------------------------------------------------------------

export const appealsApi = {
  create: (data: { application_id: string; reason: string; evidence?: string }) =>
    api.post<any>(`/applications/${data.application_id}/appeals`, data),

  list: (applicationId: string) =>
    api.get<any[]>(`/applications/${applicationId}/appeals`),
}

// ---------------------------------------------------------------------------
// Reports API
// ---------------------------------------------------------------------------

export const reportsApi = {
  create: (data: { application_id: string; report_type: string; content?: any; summary?: string }) =>
    api.post<any>(`/applications/${data.application_id}/reports`, data),

  list: (applicationId: string) =>
    api.get<any[]>(`/applications/${applicationId}/reports`),
}


export const auditApi = {
  list: () => api.get<any[]>("/audit-logs"),
}

// ---------------------------------------------------------------------------
// Model / Monitoring / Fairness insight APIs (read-only, backend-backed)
// ---------------------------------------------------------------------------

export const modelApi = {
  active: () => api.get<any>("/models/active"),
  metadata: () => api.get<any>("/models/metadata"),
}

export const monitoringApi = {
  summary: () => api.get<any>("/monitoring/summary"),
}

export const fairnessApi = {
  ageBandAudit: () => api.get<any>("/fairness/age-band-audit"),
  calibrationSegments: () => api.get<any>("/calibration/segments"),
}

export const decisionRoomApi = {
  // Real, backend-computed Decision Room payload (application, scoring, SHAP,
  // data reliability, cash-flow, integrity alerts, model agreement, timeline).
  get: (applicationId: string) => api.get<any>(`/applications/${applicationId}/decision-room`),
}

export interface ApplicationDto {
  id: string
  reference: string
  borrower_id: string
  purpose: string
  requested_amount: number
  requested_term_months: number | null
  status: string
  risk_band: string | null
  probability_of_default: number | null
  confidence: number | null
  model_version: string | null
  recommended_action: string | null
  data_quality_score: number | null
  assigned_analyst_id: string | null
  submitted_at: string | null
  scored_at: string | null
  decided_at: string | null
  created_at: string
  updated_at: string
}

export interface BorrowerDto {
  id: string
  user_id: string
  borrower_type: string
  employment_type: string | null
  employer_name: string | null
  business_name: string | null
  phone: string | null
  address: string | null
  updated_at: string
}

function toRiskBand(dto: ApplicationDto): RiskBand {
  const explicit = dto.risk_band?.toUpperCase()
  if (explicit === "LOW" || explicit === "MEDIUM" || explicit === "HIGH") return explicit
  const probability = dto.probability_of_default ?? 0
  if (probability < 0.15) return "LOW"
  if (probability < 0.3) return "MEDIUM"
  return "HIGH"
}

export function mapApplication(dto: ApplicationDto): Application {
  return {
    id: dto.id,
    reference: dto.reference,
    borrowerName: `Borrower ${dto.borrower_id.slice(0, 8)}`,
    borrowerType: "THIN_FILE",
    requestedAmount: dto.requested_amount,
    purpose: dto.purpose,
    status: dto.status.toUpperCase() as Application["status"],
    probabilityOfDefault: dto.probability_of_default ?? 0,
    riskBand: toRiskBand(dto),
    confidence: dto.confidence ?? 0,
    dataQuality: dto.data_quality_score ?? 0,
    assignedAnalyst: dto.assigned_analyst_id ?? "Unassigned",
    submittedAt: dto.submitted_at ?? dto.created_at,
    lastUpdated: dto.updated_at,
    modelVersion: dto.model_version ?? "Demo scoring not run",
    recommendedAction: (dto.recommended_action?.toUpperCase() ?? "MANUAL_REVIEW") as Application["recommendedAction"],
    factors: [],
    policyResults: [],
    dataSources: [],
    consents: [],
    decisions: [],
    audit: [],
    incomeMonthly: 0,
    expenseMonthly: 0,
    netCashFlow: 0,
  }
}

export function mapBorrower(dto: BorrowerDto): Borrower {
  const segmentMap: Record<string, BorrowerSegment> = {
    gig_worker: "GIG_WORKER",
    micro_business: "MICRO_ENTREPRENEUR",
    sole_proprietor: "SMALL_MERCHANT",
    individual: "THIN_FILE",
  }
  return {
    id: dto.id,
    name: dto.business_name || `Borrower ${dto.id.slice(0, 8)}`,
    segment: segmentMap[dto.borrower_type] ?? "THIN_FILE",
    applications: 0,
    latestRiskBand: "LOW",
    activeApplication: null,
    lastUpdated: dto.updated_at,
    email: "Not exposed",
    occupation: dto.employer_name || dto.employment_type || "Not provided",
  }
}
