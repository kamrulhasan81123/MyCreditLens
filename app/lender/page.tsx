"use client"

import Link from "next/link"
import { FileText, Loader2, TrendingUp, Users } from "lucide-react"

import { KpiCard } from "@/components/data-display/kpi-card"
import { PageHeader } from "@/components/layout/page-header"
import { ApplicationsTable } from "@/components/lender/applications-table"
import { Button } from "@/components/ui/button"
import { useApplications, useBorrowers } from "@/lib/hooks"

export default function LenderOverviewPage() {
  const applications = useApplications({ page_size: 100 })
  const borrowers = useBorrowers({ page_size: 100 })
  const approved = applications.applications.filter((item) => item.status === "APPROVED").length
  const reviewQueue = applications.applications.filter((item) =>
    ["SUBMITTED", "SCORED", "MANUAL_REVIEW", "INFORMATION_REQUESTED"].includes(item.status),
  )
  const approvalRate = applications.total
    ? `${Math.round((approved / applications.total) * 100)}%`
    : "0%"
  const loading = applications.isLoading || borrowers.isLoading
  const error = applications.error || borrowers.error

  return (
    <div className="space-y-8">
      <PageHeader
        title="Portfolio overview"
        description="Current application and borrower activity from the live API."
        actions={
          <Button render={<Link href="/lender/applications" />}>
            View applications
          </Button>
        }
      />
      {loading ? <div className="flex justify-center py-10"><Loader2 className="size-6 animate-spin" /></div> : null}
      {error ? <div className="rounded-lg border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive">{error}</div> : null}
      {!loading && !error ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard label="Applications" value={String(applications.total)} icon={FileText} />
            <KpiCard label="Approval rate" value={approvalRate} icon={TrendingUp} />
            <KpiCard label="Borrowers" value={String(borrowers.total)} icon={Users} />
            <KpiCard label="Review queue" value={String(reviewQueue.length)} icon={FileText} />
          </div>
          <div>
            <h2 className="mb-4 text-lg font-semibold">Review queue</h2>
            <ApplicationsTable applications={reviewQueue.slice(0, 10)} />
          </div>
        </>
      ) : null}
    </div>
  )
}
