"use client"

import { useState } from "react"
import { Loader2, Waves } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { aiApi, type ApiError } from "@/lib/api-client"
import { formatPercent } from "@/lib/format"
import type { Application } from "@/lib/types"

interface StressScenario {
  scenario: string
  probability_of_default: number
  probability_change: number
  risk_band: string
  is_ood: boolean
}

export function StressTestingPanel({ application }: { application: Application }) {
  const [scenarios, setScenarios] = useState<StressScenario[]>([])
  const [disclaimer, setDisclaimer] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    try {
      const response = await aiApi.stressTests(application.id)
      setScenarios(response.scenarios)
      setDisclaimer(response.disclaimer)
    } catch (caught) {
      setError((caught as ApiError).detail || "Stress testing failed")
    } finally {
      setLoading(false)
    }
  }

  return <Card><CardHeader><CardTitle className="flex items-center gap-2"><Waves className="size-4 text-primary" />Stress testing</CardTitle><CardDescription>Adverse feature shocks scored by the deployed trained model.</CardDescription></CardHeader><CardContent className="space-y-4"><Button onClick={run} disabled={loading}>{loading ? <Loader2 className="size-4 animate-spin" /> : null}Run stress tests</Button>{error ? <div className="rounded-lg border border-destructive/25 bg-destructive/5 p-3 text-sm text-destructive">{error}</div> : null}<div className="grid gap-3 sm:grid-cols-2">{scenarios.map((scenario) => <div key={scenario.scenario} className="border p-4"><p className="text-sm font-medium capitalize">{scenario.scenario.replaceAll("_", " ")}</p><p className="mt-2 text-xl font-semibold">{formatPercent(scenario.probability_of_default)}</p><p className="text-xs text-muted-foreground">Change {(scenario.probability_change * 100).toFixed(1)} points / {scenario.risk_band} risk{scenario.is_ood ? " / OOD review" : ""}</p></div>)}</div>{disclaimer ? <p className="text-xs text-muted-foreground">{disclaimer}</p> : null}</CardContent></Card>
}
