"use client"

import Link from "next/link"
import { ArrowRight, FileText, Loader2, Plug } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { StatusBadge } from "@/components/risk/badges"
import { formatCurrency } from "@/lib/format"
import { useApplications } from "@/lib/hooks"

const STATUS_PROGRESS: Record<string, number> = {
  DRAFT: 15,
  SUBMITTED: 35,
  DATA_PENDING: 45,
  READY_FOR_SCORING: 55,
  SCORED: 70,
  MANUAL_REVIEW: 80,
  INFORMATION_REQUESTED: 75,
  APPROVED: 100,
  REJECTED: 100,
  APPEALED: 90,
}

export default function BorrowerDashboard() {
  const { applications, isLoading, error } = useApplications({ page_size: 10 })
  const application = applications[0]

  if (isLoading) {
    return <div className="flex min-h-64 items-center justify-center"><Loader2 className="size-6 animate-spin" /></div>
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-foreground">Your applications</h1>
        <p className="text-sm text-muted-foreground">Track your latest application and manage supporting data.</p>
      </div>

      {error ? <div className="rounded-lg border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive">{error}</div> : null}

      {!error && !application ? (
        <Card>
          <CardContent className="flex flex-col items-start gap-4 py-8">
            <p className="text-sm text-muted-foreground">You do not have an application yet.</p>
            <Button render={<Link href="/borrower/new-application" />}>Create application</Button>
          </CardContent>
        </Card>
      ) : null}

      {application ? (
        <Card>
          <CardHeader className="flex flex-row items-start justify-between">
            <div>
              <CardTitle>{application.reference}</CardTitle>
              <CardDescription>{formatCurrency(application.requestedAmount)} · {application.purpose}</CardDescription>
            </div>
            <StatusBadge status={application.status} />
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between text-sm"><span className="text-muted-foreground">Progress</span><span>{STATUS_PROGRESS[application.status] ?? 25}%</span></div>
            <Progress value={STATUS_PROGRESS[application.status] ?? 25} />
            <p className="text-sm text-muted-foreground">Status updates shown here come directly from the application service.</p>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <ActionCard href="/borrower/connected-data" icon={Plug} title="Connected data" description="Upload and review consented transaction data." />
        <ActionCard href="/borrower/documents" icon={FileText} title="Documents" description="Review files attached to your latest application." />
      </div>
    </div>
  )
}

function ActionCard({ href, icon: Icon, title, description }: { href: string; icon: React.ElementType; title: string; description: string }) {
  return <Link href={href}><Card className="h-full"><CardContent className="flex items-start gap-3 pt-6"><Icon className="size-5 text-primary" /><div className="flex-1"><p className="text-sm font-medium">{title}</p><p className="text-sm text-muted-foreground">{description}</p></div><ArrowRight className="size-4 text-muted-foreground" /></CardContent></Card></Link>
}
