"use client"

import { useState, useEffect, useCallback } from "react"
import { applicationsApi, scoringApi, type ApiError } from "@/lib/api-client"
import type { Application } from "@/lib/types"

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface UseApplicationsState {
  applications: Application[]
  isLoading: boolean
  error: string | null
  total: number
  page: number
  totalPages: number
}

interface UseApplicationsReturn extends UseApplicationsState {
  refetch: () => void
  setPage: (page: number) => void
}

// ---------------------------------------------------------------------------
// Hook: List applications
// ---------------------------------------------------------------------------

export function useApplications(params?: {
  page?: number
  page_size?: number
  status?: string
  risk_band?: string
}): UseApplicationsReturn {
  const [state, setState] = useState<UseApplicationsState>({
    applications: [],
    isLoading: true,
    error: null,
    total: 0,
    page: params?.page || 1,
    totalPages: 1,
  })

  const fetchApplications = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }))
    try {
      const response = await applicationsApi.list({
        page: state.page,
        page_size: params?.page_size || 20,
        status: params?.status,
        risk_band: params?.risk_band,
      })
      setState({
        applications: response.items,
        isLoading: false,
        error: null,
        total: response.total,
        page: response.page,
        totalPages: response.total_pages,
      })
    } catch (err) {
      const apiErr = err as ApiError
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: apiErr?.detail || "Failed to load applications",
      }))
    }
  }, [state.page, params?.page_size, params?.status, params?.risk_band])

  useEffect(() => {
    fetchApplications()
  }, [fetchApplications])

  const setPage = useCallback((page: number) => {
    setState((prev) => ({ ...prev, page }))
  }, [])

  return {
    ...state,
    refetch: fetchApplications,
    setPage,
  }
}

// ---------------------------------------------------------------------------
// Hook: Single application
// ---------------------------------------------------------------------------

export function useApplication(id: string | undefined) {
  const [application, setApplication] = useState<Application | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchApplication = useCallback(async () => {
    if (!id) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await applicationsApi.get(id)
      if (data.status === "SCORED" || data.status === "MANUAL_REVIEW") {
        try {
          const explanation = await scoringApi.getExplanation(id)
          data.factors = Object.entries(explanation.shap_values || {}).map(([feature, contribution]) => ({
            feature,
            label: feature.split("__").at(-1)?.replaceAll("_", " ") || feature,
            direction: Number(contribution) >= 0 ? "increases_risk" : "reduces_risk",
            impact: Number(contribution),
            borrowerValue: "See feature evidence",
            expectedRange: "Training distribution",
            explanation: explanation.plain_language_explanation || "This feature affected the trained model output.",
          }))
        } catch {
          // The application remains viewable if an older score has no explanation record.
        }
      }
      setApplication(data)
    } catch (err) {
      const apiErr = err as ApiError
      setError(apiErr?.detail || "Failed to load application")
    } finally {
      setIsLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchApplication()
  }, [fetchApplication])

  return { application, isLoading, error, refetch: fetchApplication }
}
