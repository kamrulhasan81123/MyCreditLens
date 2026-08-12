"use client"

import { useState, useEffect, useCallback } from "react"
import { borrowersApi, type ApiError } from "@/lib/api-client"
import type { Borrower } from "@/lib/types"

// ---------------------------------------------------------------------------
// Hook: List borrowers
// ---------------------------------------------------------------------------

export function useBorrowers(params?: {
  page?: number
  page_size?: number
  search?: string
}) {
  const [borrowers, setBorrowers] = useState<Borrower[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(params?.page || 1)
  const [totalPages, setTotalPages] = useState(1)

  const fetchBorrowers = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await borrowersApi.list({
        page,
        page_size: params?.page_size || 20,
        search: params?.search,
      })
      setBorrowers(response.items)
      setTotal(response.total)
      setTotalPages(response.total_pages)
    } catch (err) {
      const apiErr = err as ApiError
      setError(apiErr?.detail || "Failed to load borrowers")
    } finally {
      setIsLoading(false)
    }
  }, [page, params?.page_size, params?.search])

  useEffect(() => {
    fetchBorrowers()
  }, [fetchBorrowers])

  return {
    borrowers,
    isLoading,
    error,
    total,
    page,
    totalPages,
    setPage,
    refetch: fetchBorrowers,
  }
}

// ---------------------------------------------------------------------------
// Hook: Single borrower
// ---------------------------------------------------------------------------

export function useBorrower(id: string | undefined) {
  const [borrower, setBorrower] = useState<Borrower | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchBorrower = useCallback(async () => {
    if (!id) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await borrowersApi.get(id)
      setBorrower(data)
    } catch (err) {
      const apiErr = err as ApiError
      setError(apiErr?.detail || "Failed to load borrower")
    } finally {
      setIsLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchBorrower()
  }, [fetchBorrower])

  return { borrower, isLoading, error, refetch: fetchBorrower }
}