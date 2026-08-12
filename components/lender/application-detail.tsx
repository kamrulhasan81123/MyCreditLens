"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import { decisionRoomApi } from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  DataQualityBadge,
  RiskBadge,
  StatusBadge,
} from "@/components/risk/badges"
import { ProbabilityGauge } from "@/components/risk/probability-gauge"
import { ShapWaterfall } from "@/components/charts/shap-waterfall"
import type { Application } from "@/lib/types"
import {
  formatCurrency,
  formatPercent,
  SEGMENT_LABEL,
} from "@/lib/format"
import { getDecisionRoomData } from "@/src/features/applications/mock-data/decision-room.mock"
import {
  getApplicationTimeline,
} from "@/src/features/applications/mock-data/advanced-risk.mock"
import { DecisionRoom } from "@/src/features/applications/components/decision-room/decision-room"
import { DecisionPanel } from "@/src/features/applications/components/decision-room/decision-panel"
import { DataReliabilityCard } from "@/src/features/applications/components/reliability/data-reliability-card"
import { ModelAgreementCard } from "@/src/features/applications/components/model/model-agreement-card"
import { CounterfactualSimulator } from "@/src/features/applications/components/counterfactual/counterfactual-simulator"
import { StressTestingPanel } from "@/src/features/applications/components/stress/stress-testing-panel"
import { IntegrityAlertsPanel } from "@/src/features/applications/components/integrity/integrity-alerts-panel"
import { EnhancedTimeline } from "@/src/features/applications/components/timeline/enhanced-timeline"
import {
  EvidenceDrawerProvider,
  useEvidenceDrawer,
} from "@/src/features/applications/components/evidence/evidence-drawer"
import { getEvidenceTraceForFactor } from "@/src/features/applications/mock-data/advanced-risk.mock"

const policyStyles: Record<string, string> = {
  PASS: "text-risk-low",
  FAIL: "text-risk-high",
  BLOCK: "text-risk-high",
  MANUAL_REVIEW: "text-review",
}

export function ApplicationDetail({ application }: { application: Application }) {
  return (
    <EvidenceDrawerProvider>
      <ApplicationDetailInner application={application} />
    </EvidenceDrawerProvider>
  )
}

function ApplicationDetailInner({ application }: { application: Application }) {
  const [tab, setTab] = useState("decision-room")
  const panelRef = useRef<HTMLDivElement>(null)
  const room = useMemo(() => getDecisionRoomData(application), [application])
  const timeline = useMemo(() => getApplicationTimeline(application), [application])
  const { openTrace } = useEvidenceDrawer()

  // Real, backend-computed Decision Room payload (cash-flow, reliability,
  // integrity, model agreement, timeline). Used to replace fabricated values
  // with real ones or explicit "Not available" states.
  const [dr, setDr] = useState<any | null>(null)
  useEffect(() => {
    let active = true
    decisionRoomApi
      .get(application.id)
      .then((d) => active && setDr(d))
      .catch(() => active && setDr({ error: true }))
    return () => {
      active = false
    }
  }, [application.id])
  const cash = dr && !dr.error ? dr.cash_flow : null

  function scrollToDecision() {
    panelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
  }

  return (
    <div className="space-y-6">
      {application.modelVersion.startsWith("demo-") ? (
        <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950">
          Demo scoring mode. This result is not a trained or calibrated AI prediction.
        </div>
      ) : (
        <div className="rounded-lg border border-emerald-300 bg-emerald-50 px-4 py-3 text-sm text-emerald-950">
          Trained artifact model {application.modelVersion}. Review OOD, confidence, evidence, and policy results before deciding.
        </div>
      )}
      <div>
        <Button variant="ghost" size="sm" render={<Link href="/lender/applications" />} className="-ml-2 mb-2">
            <ArrowLeft className="size-4" />
            Back to applications
        </Button>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-semibold tracking-tight text-foreground">
                {application.borrowerName}
              </h1>
              <RiskBadge band={application.riskBand} />
              <StatusBadge status={application.status} />
            </div>
            <p className="text-sm text-muted-foreground">
              {application.id} · {application.reference} · {SEGMENT_LABEL[application.borrowerType]} ·{" "}
              {formatCurrency(application.requestedAmount)} · {application.purpose}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="w-full justify-start overflow-x-auto">
              <TabsTrigger value="decision-room">Decision Room</TabsTrigger>
              <TabsTrigger value="summary">Summary</TabsTrigger>
              <TabsTrigger value="explainability">Explainability</TabsTrigger>
              <TabsTrigger value="reliability">Data reliability</TabsTrigger>
              <TabsTrigger value="models">Model agreement</TabsTrigger>
              <TabsTrigger value="stress">Stress test</TabsTrigger>
              <TabsTrigger value="integrity">Integrity</TabsTrigger>
              <TabsTrigger value="policy">Policy</TabsTrigger>
              <TabsTrigger value="audit">Audit trail</TabsTrigger>
            </TabsList>

            {/* Decision Room */}
            <TabsContent value="decision-room" className="space-y-6 pt-4">
              <DecisionRoom
                application={application}
                room={room}
                onViewRiskAnalysis={() => setTab("explainability")}
                onCompareModels={() => setTab("models")}
                onRunStressTest={() => setTab("stress")}
                onContinueDecision={scrollToDecision}
              />
              <DataReliabilityCard application={application} variant="condensed" />
            </TabsContent>

            {/* Summary */}
            <TabsContent value="summary" className="space-y-6 pt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Risk assessment</CardTitle>
                  <CardDescription>Model {application.modelVersion}</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col items-center gap-6 sm:flex-row sm:items-center sm:justify-around">
                  <ProbabilityGauge
                    value={application.probabilityOfDefault}
                    band={application.riskBand}
                  />
                  <div className="grid grid-cols-2 gap-x-8 gap-y-4">
                    <Metric label="Risk band" value={<RiskBadge band={application.riskBand} />} />
                    <Metric label="Confidence" value={formatPercent(application.confidence, 0)} />
                    <Metric
                      label="Data quality"
                      value={<DataQualityBadge score={application.dataQuality} />}
                    />
                    <Metric
                      label="Recommendation"
                      value={
                        <span className="text-sm font-medium capitalize text-foreground">
                          {application.recommendedAction.replace(/_/g, " ").toLowerCase()}
                        </span>
                      }
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Cash-flow overview</CardTitle>
                  <CardDescription>
                    Transaction-derived analyst evidence (not a PD model input).
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {cash && cash.status === "available" ? (
                    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                      <Metric label="Avg monthly income" value={formatCurrency(cash.average_monthly_income)} />
                      <Metric label="Avg monthly expense" value={formatCurrency(cash.average_monthly_expense)} />
                      <Metric label="Net monthly cash flow" value={formatCurrency(cash.net_monthly_cashflow)} />
                      <Metric label="Avg balance" value={formatCurrency(cash.average_balance)} />
                      <Metric label="Savings rate" value={formatPercent(cash.savings_rate, 0)} />
                      <Metric label="Transactions" value={String(cash.transaction_count)} />
                    </div>
                  ) : (
                    <p className="py-6 text-center text-sm text-muted-foreground">
                      {dr === null ? "Loading…" : "Not available — no transaction data uploaded for this application."}
                    </p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Activity timeline</CardTitle>
                  <CardDescription>Recent events on this application.</CardDescription>
                </CardHeader>
                <CardContent>
                  <EnhancedTimeline events={timeline} variant="compact" limit={5} />
                </CardContent>
              </Card>
            </TabsContent>

            {/* Explainability */}
            <TabsContent value="explainability" className="space-y-6 pt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Why this score?</CardTitle>
                  <CardDescription>
                    Feature contributions to the probability of default. Positive values increase
                    assessed risk; negative values reduce it.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ShapWaterfall factors={application.factors} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Factor detail</CardTitle>
                  <CardDescription>
                    Plain-language explanation for each contributing factor. Select a factor to
                    trace its underlying evidence.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {application.factors.map((f) => (
                    <button
                      key={f.feature}
                      type="button"
                      onClick={() =>
                        openTrace(getEvidenceTraceForFactor(application, f))
                      }
                      className="w-full rounded-lg border border-border p-4 text-left transition-colors hover:border-action/40 hover:bg-muted/40"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-foreground">{f.label}</span>
                        <span
                          className={
                            f.direction === "increases_risk"
                              ? "text-xs font-medium text-risk-high"
                              : "text-xs font-medium text-risk-low"
                          }
                        >
                          {f.direction === "increases_risk" ? "Increases risk" : "Reduces risk"}
                        </span>
                      </div>
                      <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                        {f.explanation}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-6 text-xs text-muted-foreground">
                        <span>
                          Borrower value:{" "}
                          <span className="font-medium text-foreground">{f.borrowerValue}</span>
                        </span>
                        <span>
                          Typical range:{" "}
                          <span className="font-medium text-foreground">{f.expectedRange}</span>
                        </span>
                        <span className="font-medium text-action">View evidence →</span>
                      </div>
                    </button>
                  ))}
                </CardContent>
              </Card>

              <CounterfactualSimulator application={application} />
            </TabsContent>

            {/* Data reliability */}
            <TabsContent value="reliability" className="pt-4">
              <DataReliabilityCard application={application} variant="full" />
            </TabsContent>

            {/* Model agreement */}
            <TabsContent value="models" className="pt-4">
              <ModelAgreementCard application={application} />
            </TabsContent>

            {/* Stress test */}
            <TabsContent value="stress" className="pt-4">
              <StressTestingPanel application={application} />
            </TabsContent>

            {/* Integrity */}
            <TabsContent value="integrity" className="pt-4">
              <IntegrityAlertsPanel application={application} />
            </TabsContent>

            {/* Policy */}
            <TabsContent value="policy" className="pt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Policy engine results</CardTitle>
                  <CardDescription>
                    Deterministic rules evaluated before the recommendation.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {application.policyResults.map((p) => (
                    <div
                      key={p.ruleId}
                      className="flex items-start justify-between gap-4 rounded-lg border border-border p-4"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-foreground">{p.name}</span>
                          <span className="text-xs text-muted-foreground">
                            {p.ruleId} · v{p.version}
                          </span>
                        </div>
                        <p className="mt-1 text-sm text-muted-foreground">{p.detail}</p>
                      </div>
                      <span
                        className={`shrink-0 text-xs font-semibold ${policyStyles[p.result] ?? "text-muted-foreground"}`}
                      >
                        {p.result.replace(/_/g, " ")}
                      </span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Audit */}
            <TabsContent value="audit" className="pt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Audit trail</CardTitle>
                  <CardDescription>
                    Immutable record of every action taken on this application.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <EnhancedTimeline events={timeline} variant="full" />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Decision panel — single decision system, sticky on desktop */}
        <div className="space-y-6">
          <DecisionPanel
            ref={panelRef}
            application={application}
            room={room}
            className="lg:sticky lg:top-6"
          />
        </div>
      </div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <div className="text-sm font-medium text-foreground">{value}</div>
    </div>
  )
}
