"use client"

import { useState } from "react"
import { ArrowRight, Loader2, Sparkles } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { aiApi, type ApiError } from "@/lib/api-client"
import { formatPercent } from "@/lib/format"
import type { Application } from "@/lib/types"

interface Scenario {
  feature: string
  current_value: number
  suggested_value: number
  current_probability: number
  projected_probability: number
  probability_reduction: number
  target_reached: boolean
}

export function CounterfactualSimulator({ application }: { application: Application }) {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [disclaimer, setDisclaimer] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    try {
      const response = await aiApi.counterfactuals(application.id, 0.3)
      setScenarios(response.scenarios)
      setDisclaimer(response.disclaimer)
    } catch (caught) {
      setError((caught as ApiError).detail || "Counterfactual analysis failed")
    } finally {
      setLoading(false)
    }
  }

  return <Card><CardHeader><CardTitle className="flex items-center gap-2"><Sparkles className="size-4 text-primary" />Model counterfactuals</CardTitle><CardDescription>Constrained sensitivity analysis using the deployed trained model.</CardDescription></CardHeader><CardContent className="space-y-4"><Button onClick={run} disabled={loading}>{loading ? <Loader2 className="size-4 animate-spin" /> : null}Run counterfactual analysis</Button>{error ? <div className="rounded-lg border border-destructive/25 bg-destructive/5 p-3 text-sm text-destructive">{error}</div> : null}<div className="grid gap-3 sm:grid-cols-2">{scenarios.map((scenario) => <div key={scenario.feature} className="border p-4"><p className="text-sm font-medium capitalize">{scenario.feature.replaceAll("_", " ")}</p><p className="mt-1 text-xs text-muted-foreground">{scenario.current_value.toFixed(2)} <ArrowRight className="inline size-3" /> {scenario.suggested_value.toFixed(2)}</p><p className="mt-2 text-sm">PD {formatPercent(scenario.current_probability)} <ArrowRight className="inline size-3" /> <span className="font-medium text-risk-low">{formatPercent(scenario.projected_probability)}</span></p></div>)}</div>{disclaimer ? <p className="text-xs text-muted-foreground">{disclaimer}</p> : null}</CardContent></Card>
}
