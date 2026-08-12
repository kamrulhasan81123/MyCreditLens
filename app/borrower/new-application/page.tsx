"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Check, ChevronLeft, ChevronRight, Loader2 } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { DATA_SOURCE_LABEL } from "@/lib/format"
import type { DataSourceType } from "@/lib/types"
import { cn } from "@/lib/utils"
import { applicationsApi, consentsApi, type ApiError } from "@/lib/api-client"

const STEPS = ["Loan", "Connect data", "Consent"]
const SOURCE_OPTIONS: DataSourceType[] = ["BANK_STATEMENT", "EWALLET", "UTILITY", "GIG_INCOME"]
const SOURCE_API_VALUE: Record<DataSourceType, string> = {
  BANK_STATEMENT: "bank_statement",
  EWALLET: "transaction_csv",
  UTILITY: "utility",
  GIG_INCOME: "transaction_csv",
  POS: "transaction_csv",
  REMITTANCE: "transaction_csv",
  MANUAL: "transaction_csv",
}

export default function BorrowerNewApplication() {
  const router = useRouter()
  const [step, setStep] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [amount, setAmount] = useState("")
  const [purpose, setPurpose] = useState("")
  const [sources, setSources] = useState<DataSourceType[]>([])
  const [consent, setConsent] = useState(false)

  function toggle(s: DataSourceType) {
    setSources((p) => (p.includes(s) ? p.filter((x) => x !== s) : [...p, s]))
  }

  function next() {
    if (step === 0 && (amount === "" || purpose === "")) {
      toast.error("Enter an amount and purpose.")
      return
    }
    if (step === 1 && sources.length === 0) {
      toast.error("Connect at least one data source.")
      return
    }
    setStep((s) => Math.min(s + 1, STEPS.length - 1))
  }

  async function submit() {
    if (!consent) {
      toast.error("Please provide consent to continue.")
      return
    }
    setSubmitting(true)
    try {
      const application = await applicationsApi.create({
        purpose,
        requested_amount: Number(amount),
        requested_term_months: 12,
      })
      await Promise.all(
        [...new Set(sources.map((source) => SOURCE_API_VALUE[source]))].map((sourceType) =>
          consentsApi.grant(application.id, sourceType),
        ),
      )
      await applicationsApi.submit(application.id)
      toast.success("Application submitted", { description: "We'll notify you as it progresses." })
      router.push("/borrower")
    } catch (error) {
      const apiError = error as ApiError
      toast.error("Application could not be submitted", {
        description: apiError.detail || "Review the form and try again.",
      })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">New application</h1>
        <p className="text-sm text-muted-foreground">Apply for credit in three simple steps.</p>
      </div>

      <ol className="flex items-center gap-2">
        {STEPS.map((label, i) => (
          <li key={label} className="flex flex-1 items-center gap-2">
            <span
              className={cn(
                "flex size-7 items-center justify-center rounded-full border text-xs font-medium",
                i < step && "border-primary bg-primary text-primary-foreground",
                i === step && "border-primary text-primary",
                i > step && "border-border text-muted-foreground",
              )}
            >
              {i < step ? <Check className="size-3.5" /> : i + 1}
            </span>
            <span className={cn("text-sm", i === step ? "font-medium text-foreground" : "text-muted-foreground")}>
              {label}
            </span>
          </li>
        ))}
      </ol>

      <Card>
        <CardHeader>
          <CardTitle>{STEPS[step]}</CardTitle>
          <CardDescription>
            {step === 0 && "How much would you like to borrow?"}
            {step === 1 && "Securely connect the accounts you'd like us to consider."}
            {step === 2 && "Review and confirm consent."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {step === 0 && (
            <>
              <div className="space-y-2">
                <Label htmlFor="amount">Amount (MYR)</Label>
                <Input id="amount" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="5000" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="purpose">Purpose</Label>
                <Select value={purpose} onValueChange={(value) => value && setPurpose(value)}>
                  <SelectTrigger id="purpose">
                    <SelectValue placeholder="Select purpose" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Working capital">Working capital</SelectItem>
                    <SelectItem value="Equipment">Equipment</SelectItem>
                    <SelectItem value="Inventory">Inventory</SelectItem>
                    <SelectItem value="Emergency expense">Emergency expense</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </>
          )}

          {step === 1 && (
            <div className="space-y-3">
              {SOURCE_OPTIONS.map((s) => {
                const active = sources.includes(s)
                return (
                  <button
                    key={s}
                    type="button"
                    onClick={() => toggle(s)}
                    className={cn(
                      "flex w-full items-center justify-between rounded-lg border px-4 py-3 text-left transition-colors",
                      active ? "border-primary bg-primary/5" : "border-border hover:bg-secondary",
                    )}
                  >
                    <span className="text-sm font-medium text-foreground">{DATA_SOURCE_LABEL[s]}</span>
                    <span
                      className={cn(
                        "flex size-5 items-center justify-center rounded-full border",
                        active ? "border-primary bg-primary text-primary-foreground" : "border-border",
                      )}
                    >
                      {active ? <Check className="size-3" /> : null}
                    </span>
                  </button>
                )
              })}
            </div>
          )}

          {step === 2 && (
            <label className="flex items-start gap-3 rounded-lg border border-border p-4">
              <Checkbox checked={consent} onCheckedChange={(v) => setConsent(v === true)} className="mt-0.5" />
              <span className="text-sm leading-relaxed text-foreground">
                I consent to MyCreditLens analyzing my selected financial data for this application,
                and I understand an automated model contributes to the decision. I can withdraw
                consent at any time.
              </span>
            </label>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={() => setStep((s) => Math.max(s - 1, 0))} disabled={step === 0 || submitting}>
          <ChevronLeft className="size-4" />
          Back
        </Button>
        {step < STEPS.length - 1 ? (
          <Button onClick={next}>
            Continue
            <ChevronRight className="size-4" />
          </Button>
        ) : (
          <Button onClick={submit} disabled={submitting}>
            {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
            Submit application
          </Button>
        )}
      </div>
    </div>
  )
}
