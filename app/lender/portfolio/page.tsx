"use client"

import { Banknote, Loader2, PieChart, TrendingDown, Wallet } from "lucide-react"

import { KpiCard } from "@/components/data-display/kpi-card"
import { PageHeader } from "@/components/layout/page-header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { formatCurrency, formatPercent } from "@/lib/format"
import { useApplications } from "@/lib/hooks"

export default function PortfolioPage() {
  const { applications, isLoading, error } = useApplications({ page_size: 100 })
  const total = applications.reduce((sum, item) => sum + item.requestedAmount, 0)
  const average = applications.length ? total / applications.length : 0
  const averagePd = applications.length ? applications.reduce((sum, item) => sum + item.probabilityOfDefault, 0) / applications.length : 0
  const highRisk = applications.length ? applications.filter((item) => item.riskBand === "HIGH").length / applications.length : 0
  const counts = ["LOW", "MEDIUM", "HIGH"].map((band) => ({ band, count: applications.filter((item) => item.riskBand === band).length }))

  return <div className="space-y-8"><PageHeader title="Portfolio analytics" description="Aggregate values computed from current application records." />{isLoading ? <div className="flex justify-center py-10"><Loader2 className="size-6 animate-spin" /></div> : null}{error ? <div className="rounded-lg border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive">{error}</div> : null}{!isLoading && !error ? <><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><KpiCard label="Requested exposure" value={formatCurrency(total)} icon={Wallet} /><KpiCard label="Average request" value={formatCurrency(average)} icon={Banknote} /><KpiCard label="Average demo PD" value={formatPercent(averagePd)} icon={TrendingDown} /><KpiCard label="High-risk share" value={formatPercent(highRisk)} icon={PieChart} /></div><Card><CardHeader><CardTitle>Risk-band distribution</CardTitle></CardHeader><CardContent className="grid gap-3 sm:grid-cols-3">{counts.map((item) => <div key={item.band} className="border p-4"><p className="text-xs text-muted-foreground">{item.band}</p><p className="text-2xl font-semibold">{item.count}</p></div>)}</CardContent></Card></> : null}</div>
}
