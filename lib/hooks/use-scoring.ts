"use client"

import { useState, useCallback } from "react"
import { scoringApi, type ApiError } from "@/lib/api-client"

// ---------------------------------------------------------------------------
// Hook: Score an application
// ---------------------------------------------------------------------------

export function useScoring() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [prediction, setPrediction] = useState<any>(null)
  const [explanation, setExplanation] = useState<any>(null)

  const score = useCallback(async (applicationId: string, modelVersion?: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await scoringApi.score(applicationId, modelVersion)
      setPrediction(result)
      return result
    } catch (err) {
      const apiErr = err as ApiError
      setError(apiErr?.detail || "Scoring failed")
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const fetchExplanation = useCallback(async (applicationId: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await scoringApi.getExplanation(applicationId)
      setExplanation(result)
      return result
    } catch (err) {
      const apiErr = err as ApiError
      setError(apiErr?.detail || "Failed to load explanation")
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  return {
    isLoading,
    error,
    prediction,
    explanation,
    score,
    fetchExplanation,
  }
}
