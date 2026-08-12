"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import { ApplicationsTable } from "@/components/lender/applications-table"
import { useApplications } from "@/lib/hooks"
import { Loader2 } from "lucide-react"

export default function ApplicationsPage() {
  const { applications, isLoading, error } = useApplications()

  return (
    <div className="space-y-8">
      <PageHeader
        title="Applications"
        description="All credit applications across the portfolio."
        actions={
          <Button render={<Link href="/lender/assessments/new" />}>
            New assessment
          </Button>
        }
      />
      {isLoading && applications.length === 0 ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
          <span className="ml-2 text-sm text-muted-foreground">Loading applications...</span>
        </div>
      ) : error ? (
        <div className="rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}
      {!isLoading && !error ? <ApplicationsTable applications={applications} /> : null}
    </div>
  )
}
