"use client"

import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

import { PageHeader } from "@/components/layout/page-header"
import { AuditTable } from "@/components/lender/audit-table"
import { auditApi, type ApiError } from "@/lib/api-client"
import type { AuditEvent } from "@/lib/types"

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    auditApi.list().then((items) => setEvents(items.map((item) => ({
      id: item.id,
      timestamp: item.created_at,
      user: item.user_id || "system",
      action: item.action,
      entityType: item.resource_type,
      entityId: item.resource_id || "-",
      ip: "not captured",
      result: "SUCCESS" as const,
    })))).catch((caught: ApiError) => setError(caught.detail || "Unable to load audit logs")).finally(() => setLoading(false))
  }, [])

  return <div className="space-y-8"><PageHeader title="Audit logs" description="Append-only records created by application workflow actions." />{loading ? <div className="flex justify-center py-10"><Loader2 className="size-6 animate-spin" /></div> : null}{error ? <div className="rounded-lg border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive">{error}</div> : null}{!loading && !error ? <AuditTable events={events} /> : null}</div>
}
