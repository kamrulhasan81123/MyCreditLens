"use client"

import { useEffect, useState } from "react"
import { ScaleIcon, ShieldCheck } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { PageHeader } from "@/components/layout/page-header"
import { CategoricalBarChart } from "@/components/charts/charts"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { fairnessApi } from "@/lib/api-client"

const pct = (v: number | null | undefined, d = 0) => (v == null ? "N/A" : `${(v * 100).toFixed(d)}%`)

export default function FairnessPage() {
  const [audit, setAudit] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    fairnessApi
      .ageBandAudit()
      .then((a) => active && setAudit(a))
      .catch((e) => active && setError(e instanceof Error ? e.message : "Failed to load fairness audit"))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [])

  if (loading) {
    return (
      <div className="space-y-8">
        <PageHeader title="Fairness & bias" description="Loading real age-band fairness audit…" />
        <div className="h-40 animate-pulse rounded-xl border border-border bg-secondary/40" />
      </div>
    )
  }

  if (error || !audit || audit.status !== "evaluated") {
    return (
      <div className="space-y-8">
        <PageHeader title="Fairness & bias" description="Age-band fairness audit on the model evaluation split." />
        <div className="rounded-lg border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive">
          {error ?? (audit?.detail || "Fairness audit is unavailable (evaluation dataset not present).")}
        </div>
      </div>
    )
  }

  const bands = Object.entries(audit.groups as Record<string, any>)
    .filter(([, g]) => g.sample_count > 0)
    .map(([label, g]) => ({ label, ...g }))
  const pdData = bands.map((b) => ({ segment: b.label, rate: Math.round((b.mean_predicted_pd ?? 0) * 100) }))
  const di = audit.disparate_impact_ratio

  return (
    <div className="space-y-8">
      <PageHeader
        title="Fairness & bias"
        description="Age-band audit of the active model on its held-out evaluation split (development-grade)."
      />

      <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950">
        {audit.note}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center gap-3">
            <span className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <ScaleIcon className="size-5" />
            </span>
            <div>
              <CardTitle className="text-base">Disparate impact ratio</CardTitle>
              <CardDescription>Min / max high-risk flag rate across age bands</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold tabular-nums text-foreground">{di == null ? "N/A" : di.toFixed(2)}</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {di == null
                ? "Insufficient groups to compute."
                : di >= 0.8
                  ? "Within the 0.80 four-fifths guideline."
                  : "Below the 0.80 four-fifths guideline — review required."}
              {audit.equal_opportunity_difference != null
                ? ` Equal-opportunity difference: ${(audit.equal_opportunity_difference * 100).toFixed(1)}%.`
                : ""}
            </p>
          </CardContent>
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Mean predicted PD by age band</CardTitle>
            <CardDescription>Average calibrated probability of default per band</CardDescription>
          </CardHeader>
          <CardContent>
            <CategoricalBarChart data={pdData} dataKey="rate" categoryKey="segment" color="var(--color-chart-2)" height={220} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Age-band error metrics</CardTitle>
          <CardDescription>Observed default, high-risk flag rate, and error rates per band (decision threshold {audit.decision_threshold})</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-secondary/60">
                  <TableHead>Age band</TableHead>
                  <TableHead className="text-right">Observed default</TableHead>
                  <TableHead className="text-right">Mean PD</TableHead>
                  <TableHead className="text-right">High-risk flag rate</TableHead>
                  <TableHead className="text-right">False positive</TableHead>
                  <TableHead className="text-right">False negative</TableHead>
                  <TableHead className="text-right">Sample</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bands.map((b) => (
                  <TableRow key={b.label}>
                    <TableCell className="font-medium text-foreground">
                      {b.label}
                      {b.small_group_warning ? <span className="ml-2 text-xs text-amber-600">(small sample)</span> : null}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">{pct(b.observed_default_rate, 1)}</TableCell>
                    <TableCell className="text-right tabular-nums">{pct(b.mean_predicted_pd, 1)}</TableCell>
                    <TableCell className="text-right tabular-nums">{pct(b.selection_rate_flagged_high, 0)}</TableCell>
                    <TableCell className="text-right tabular-nums">{pct(b.false_positive_rate, 0)}</TableCell>
                    <TableCell className="text-right tabular-nums">{pct(b.false_negative_rate, 0)}</TableCell>
                    <TableCell className="text-right tabular-nums text-muted-foreground">{b.sample_count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <div className="flex items-start gap-3 rounded-xl border border-border bg-secondary/40 p-4">
        <ShieldCheck className="mt-0.5 size-5 shrink-0 text-primary" />
        <p className="text-sm leading-relaxed text-muted-foreground">
          {audit.sensitive_attribute} is used here for a governance audit only. This is a
          development-grade measurement on the evaluation split and is <strong>not</strong> a legal
          or regulatory fairness certification.
        </p>
      </div>
    </div>
  )
}
