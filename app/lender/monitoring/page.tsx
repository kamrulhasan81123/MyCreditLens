"use client"

import { useEffect, useState } from "react"
import { Activity, ShieldQuestion, Target, TriangleAlert } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { PageHeader } from "@/components/layout/page-header"
import { KpiCard } from "@/components/data-display/kpi-card"
import { CategoricalBarChart, SimpleLineChart } from "@/components/charts/charts"
import { monitoringApi, modelApi } from "@/lib/api-client"

export default function MonitoringPage() {
  const [summary, setSummary] = useState<any | null>(null)
  const [metadata, setMetadata] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    Promise.all([monitoringApi.summary(), modelApi.metadata().catch(() => null)])
      .then(([s, m]) => {
        if (!active) return
        setSummary(s)
        setMetadata(m)
      })
      .catch((e) => active && setError(e instanceof Error ? e.message : "Failed to load monitoring data"))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [])

  if (loading) {
    return (
      <div className="space-y-8">
        <PageHeader title="Model monitoring" description="Loading real backend monitoring data…" />
        <div className="h-40 animate-pulse rounded-xl border border-border bg-secondary/40" />
      </div>
    )
  }

  if (error || !summary) {
    return (
      <div className="space-y-8">
        <PageHeader title="Model monitoring" description="Production health for the active model." />
        <div className="rounded-lg border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive">
          {error ?? "Monitoring data is unavailable."}
        </div>
      </div>
    )
  }

  const pct = (v: number | null) => (v == null ? "N/A" : `${(v * 100).toFixed(1)}%`)
  const volume = Object.entries(summary.scoring_volume_over_time ?? {}).map(([day, count]) => ({ month: day, count }))
  const pdDist = Object.entries(summary.pd_distribution ?? {}).map(([bucket, count]) => ({ feature: bucket, count }))
  const bandDist = Object.entries(summary.risk_band_distribution ?? {}).map(([band, count]) => ({ feature: band, count }))

  return (
    <div className="space-y-8">
      <PageHeader
        title="Model monitoring"
        description={`Production health for ${summary.active_model_name ?? "the active model"} v${summary.active_model_version ?? "?"}. Backed by the live database.`}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Total predictions" value={String(summary.total_predictions)} delta={{ value: "all time", trend: "neutral" }} icon={Activity} />
        <KpiCard label="OOD rate" value={pct(summary.ood_rate)} delta={{ value: "review trigger", trend: "neutral" }} icon={ShieldQuestion} />
        <KpiCard label="Manual-review rate" value={pct(summary.manual_review_rate)} delta={{ value: "medium band + OOD", trend: "neutral" }} icon={Target} />
        <KpiCard label="Mean uncertainty" value={summary.mean_uncertainty == null ? "N/A" : summary.mean_uncertainty.toFixed(3)} delta={{ value: "1 − confidence", trend: "neutral" }} icon={Activity} />
      </div>

      {/* Honest performance state — no fabricated production ROC-AUC/calibration. */}
      <div className="flex items-start gap-3 rounded-xl border border-amber-300 bg-amber-50 p-4 text-amber-950">
        <TriangleAlert className="mt-0.5 size-5 shrink-0" />
        <div className="text-sm">
          <p className="font-medium">Production performance: {summary.performance_status}</p>
          <p>{summary.performance_note}</p>
          {metadata?.evaluation_summary ? (
            <p className="mt-1">
              Development-grade held-out metrics (training dataset, not production): ROC-AUC{" "}
              {metadata.evaluation_summary.roc_auc?.toFixed?.(3) ?? "N/A"}, Brier{" "}
              {metadata.evaluation_summary.brier_score?.toFixed?.(3) ?? "N/A"}, ECE{" "}
              {metadata.evaluation_summary.expected_calibration_error?.toFixed?.(3) ?? "N/A"}.
            </p>
          ) : null}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Scoring volume over time</CardTitle>
            <CardDescription>Predictions per day (live database)</CardDescription>
          </CardHeader>
          <CardContent>
            {volume.length ? (
              <SimpleLineChart data={volume} dataKey="count" categoryKey="month" />
            ) : (
              <p className="py-10 text-center text-sm text-muted-foreground">No predictions recorded yet.</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Risk-band distribution</CardTitle>
            <CardDescription>Persisted predictions by risk band</CardDescription>
          </CardHeader>
          <CardContent>
            {bandDist.length ? (
              <CategoricalBarChart data={bandDist} dataKey="count" categoryKey="feature" color="var(--color-chart-2)" height={280} />
            ) : (
              <p className="py-10 text-center text-sm text-muted-foreground">No predictions recorded yet.</p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Predicted PD distribution</CardTitle>
          <CardDescription>Calibrated probability-of-default buckets across all persisted predictions</CardDescription>
        </CardHeader>
        <CardContent>
          {pdDist.length ? (
            <CategoricalBarChart data={pdDist} dataKey="count" categoryKey="feature" color="var(--color-chart-4)" height={280} />
          ) : (
            <p className="py-10 text-center text-sm text-muted-foreground">No predictions recorded yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
