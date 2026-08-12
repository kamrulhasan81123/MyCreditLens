"use client"

import { Loader2 } from "lucide-react"
import { useParams } from "next/navigation"

import { ApplicationDetail } from "@/components/lender/application-detail"
import { useApplication } from "@/lib/hooks"

export default function ApplicationDetailPage() {
  const params = useParams<{ id: string }>()
  const { application, isLoading, error } = useApplication(params.id)

  if (isLoading) {
    return (
      <div className="flex min-h-64 items-center justify-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
        Loading application...
      </div>
    )
  }

  if (error || !application) {
    return (
      <div className="rounded-lg border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive">
        {error || "Application not found"}
      </div>
    )
  }

  return <ApplicationDetail application={application} />
}
