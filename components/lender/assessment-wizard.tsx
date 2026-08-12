"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Check, ChevronLeft, ChevronRight, FileUp, Loader2 } from "lucide-react"
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
import { cn } from "@/lib/utils"
import type { DataSourceType } from "@/lib/types"
import { applicationsApi, consentsApi } from "@/lib/api-client"

const STEPS = ["Borrower", "Loan details", "Data sources", "Consent", "Review"]

const SOURCE_OPTIONS: DataSourceType[] = [
  "BANK_STATEMENT",
  "EWALLET",
  "UTILITY",
  "GIG_INCOME",
  "POS",
  "REMITTANCE",
]

// Map wizard data-source choices to backend consent `data_source_type` strings.
const SOURCE_CONSENT_TYPE: Partial<Record<DataSourceType, string>> = {
  BANK_STATEMENT: "bank_statement",
  EWALLET: "ewallet",
  UTILITY: "utility",
  GIG_INCOME: "gig_income",
  POS: "pos",
  REMITTANCE: "remittance",
}

export function AssessmentWizard() {
  const router = useRouter()
  const [step, setStep] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [segment, setSegment] = useState("")
  const [amount, setAmount] = useState("")
  const [purpose, setPurpose] = useState("")
  const [term, setTerm] = useState("12")
  const [sources, setSources] = useState<DataSourceType[]>(["BANK_STATEMENT"])
  const [consentData, setConsentData] = useState(false)
  const [consentAuto, setConsentAuto] = useState(false)

  function toggleSource(s: DataSourceType) {
    setSources((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]))
  }

  function canProceed() {
    if (step === 0) return name.trim() !== "" && email.trim() !== "" && segment !== ""
    if (step === 1) return amount !== "" && purpose.trim() !== ""
    if (step === 2) return sources.length > 0
    if (step === 3) return consentData && consentAuto
    return true
  }

  function next() {
    if (!canProceed()) {
      toast.error("Please complete the required fields before continuing.")
      return
    }
    setStep((s) => Math.min(s + 1, STEPS.length - 1))
  }

  async function submit() {
    // Real submission: create the application, record consent for each selected
    // source (+ credit-scoring consent), submit it, then navigate to the REAL
    // application id returned by the backend. No fabricated success, no hardcoded
    // id. Errors are surfaced (with retry) rather than silently faked.
    setSubmitting(true)
    setError(null)
    try {
      const app = await applicationsApi.create({
        purpose: purpose.trim(),
        requested_amount: Number(amount),
        requested_term_months: Number(term),
      })
      for (const s of sources) {
        await consentsApi.grant(app.id, SOURCE_CONSENT_TYPE[s] ?? s.toLowerCase())
      }
      await consentsApi.grant(app.id, "credit_scoring")
      await applicationsApi.submit(app.id)
      toast.success("Application created", {
        description: `Reference ${app.reference ?? app.id} entered the scoring pipeline.`,
      })
      router.push(`/lender/applications/${app.id}`)
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to create application"
      setError(msg)
      toast.error("Could not create application", { description: msg })
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      {/* Stepper */}
      <ol className="flex items-center justify-between">
        {STEPS.map((label, i) => {
          const state = i < step ? "done" : i === step ? "current" : "upcoming"
          return (
            <li key={label} className="flex flex-1 items-center last:flex-none">
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "flex size-8 items-center justify-center rounded-full border text-sm font-medium",
                    state === "done" && "border-primary bg-primary text-primary-foreground",
                    state === "current" && "border-primary text-primary",
                    state === "upcoming" && "border-border text-muted-foreground",
                  )}
                >
                  {state === "done" ? <Check className="size-4" /> : i + 1}
                </span>
                <span
                  className={cn(
                    "hidden text-sm font-medium sm:block",
                    state === "upcoming" ? "text-muted-foreground" : "text-foreground",
                  )}
                >
                  {label}
                </span>
              </div>
              {i < STEPS.length - 1 ? (
                <span
                  className={cn(
                    "mx-2 h-px flex-1",
                    i < step ? "bg-primary" : "bg-border",
                  )}
                />
              ) : null}
            </li>
          )
        })}
      </ol>

      <Card>
        <CardHeader>
          <CardTitle>{STEPS[step]}</CardTitle>
          <CardDescription>
            {step === 0 && "Identify the borrower requesting credit."}
            {step === 1 && "Capture the requested loan parameters."}
            {step === 2 && "Select the alternative data sources to analyze."}
            {step === 3 && "Obtain explicit borrower consent before processing."}
            {step === 4 && "Confirm the details before creating the assessment."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {step === 0 && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="Full name" htmlFor="name">
                <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Nurul Izzah" />
              </Field>
              <Field label="Email" htmlFor="email">
                <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="borrower@example.com" />
              </Field>
              <Field label="Borrower segment" htmlFor="segment">
                <Select value={segment} onValueChange={(value) => value && setSegment(value)}>
                  <SelectTrigger id="segment">
                    <SelectValue placeholder="Select segment" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="GIG_WORKER">Gig Worker</SelectItem>
                    <SelectItem value="MICRO_ENTREPRENEUR">Micro-Entrepreneur</SelectItem>
                    <SelectItem value="SMALL_MERCHANT">Small Merchant</SelectItem>
                    <SelectItem value="THIN_FILE">Thin-File</SelectItem>
                    <SelectItem value="SALARIED">Salaried</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
            </div>
          )}

          {step === 1 && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="Requested amount (MYR)" htmlFor="amount">
                <Input id="amount" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="8000" />
              </Field>
              <Field label="Term (months)" htmlFor="term">
                <Select value={term} onValueChange={(value) => value && setTerm(value)}>
                  <SelectTrigger id="term">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {["6", "12", "18", "24", "36"].map((t) => (
                      <SelectItem key={t} value={t}>
                        {t} months
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
              <div className="sm:col-span-2">
                <Field label="Purpose" htmlFor="purpose">
                  <Input id="purpose" value={purpose} onChange={(e) => setPurpose(e.target.value)} placeholder="e.g. Working capital" />
                </Field>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-3">
              {SOURCE_OPTIONS.map((s) => {
                const active = sources.includes(s)
                return (
                  <button
                    key={s}
                    type="button"
                    onClick={() => toggleSource(s)}
                    className={cn(
                      "flex w-full items-center justify-between rounded-lg border px-4 py-3 text-left transition-colors",
                      active ? "border-primary bg-primary/5" : "border-border hover:bg-secondary",
                    )}
                  >
                    <span className="flex items-center gap-3">
                      <FileUp className="size-4 text-muted-foreground" />
                      <span className="text-sm font-medium text-foreground">
                        {DATA_SOURCE_LABEL[s]}
                      </span>
                    </span>
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

          {step === 3 && (
            <div className="space-y-4">
              <label className="flex items-start gap-3 rounded-lg border border-border p-4">
                <Checkbox checked={consentData} onCheckedChange={(v) => setConsentData(v === true)} className="mt-0.5" />
                <span className="text-sm leading-relaxed text-foreground">
                  The borrower consents to the collection and analysis of the selected financial
                  data sources for the purpose of this credit assessment.
                </span>
              </label>
              <label className="flex items-start gap-3 rounded-lg border border-border p-4">
                <Checkbox checked={consentAuto} onCheckedChange={(v) => setConsentAuto(v === true)} className="mt-0.5" />
                <span className="text-sm leading-relaxed text-foreground">
                  The borrower has been informed that an automated model contributes to the credit
                  decision and has the right to request human review of the outcome.
                </span>
              </label>
            </div>
          )}

          {step === 4 && (
            <dl className="divide-y divide-border rounded-lg border border-border">
              <ReviewRow label="Borrower" value={name || "—"} />
              <ReviewRow label="Email" value={email || "—"} />
              <ReviewRow label="Segment" value={segment.replace(/_/g, " ") || "—"} />
              <ReviewRow label="Requested" value={amount ? `RM ${amount}` : "—"} />
              <ReviewRow label="Term" value={`${term} months`} />
              <ReviewRow label="Purpose" value={purpose || "—"} />
              <ReviewRow
                label="Data sources"
                value={sources.map((s) => DATA_SOURCE_LABEL[s]).join(", ")}
              />
              <ReviewRow label="Consent" value="Data + automated-decision consent captured" />
            </dl>
          )}

          {error && step === STEPS.length - 1 ? (
            <div className="rounded-lg border border-destructive/25 bg-destructive/5 p-3 text-sm text-destructive">
              {error} — application creation requires a borrower account with granted
              consent. Retry, or have the borrower complete onboarding.
            </div>
          ) : null}
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          onClick={() => setStep((s) => Math.max(s - 1, 0))}
          disabled={step === 0 || submitting}
        >
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
            Create assessment
          </Button>
        )}
      </div>
    </div>
  )
}

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string
  htmlFor: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
    </div>
  )
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between px-4 py-3">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="text-sm font-medium capitalize text-foreground">{value}</dd>
    </div>
  )
}
