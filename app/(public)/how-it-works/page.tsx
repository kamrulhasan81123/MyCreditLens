import Link from 'next/link'
import {
  FileCheck2,
  Gauge,
  Layers,
  ScanLine,
  ShieldCheck,
  UserCheck,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

const STEPS = [
  {
    icon: ShieldCheck,
    title: 'Borrower gives consent',
    text: 'The borrower grants scoped, versioned, and revocable consent for each alternative data source. A score request fails if required consent is missing or expired.',
  },
  {
    icon: Layers,
    title: 'Data is uploaded or connected',
    text: 'Bank statements, e-wallet exports, utility history, and gig income are ingested, hashed, validated, and normalised with full data lineage.',
  },
  {
    icon: ScanLine,
    title: 'Financial features are generated',
    text: 'Income stability, cash-flow, payment behaviour, and business-activity features are engineered with documented formulas and valid ranges.',
  },
  {
    icon: Gauge,
    title: 'Risk model produces a score',
    text: 'A calibrated gradient-boosting model outputs a probability of default, a configurable risk band, and a confidence level — never an arbitrary score.',
  },
  {
    icon: FileCheck2,
    title: 'SHAP explanation is generated',
    text: 'Factor contributions are converted into controlled reason codes. An LLM may only rewrite approved factors — it never invents new reasons.',
  },
  {
    icon: UserCheck,
    title: 'Analyst reviews the case',
    text: 'A credit analyst reviews the score, explanation, policy results, and data quality before acting. The system never makes the final decision automatically.',
  },
  {
    icon: FileCheck2,
    title: 'Final decision is recorded',
    text: 'Approve, reject, escalate, or override — every decision captures the reason, model version, policy version, and timestamp in a tamper-evident audit trail.',
  },
]

export default function HowItWorksPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6">
      <div className="max-w-2xl">
        <h1 className="text-4xl font-semibold tracking-tight text-navy text-balance">
          How MyCreditLens works
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
          A transparent, consent-first pipeline that keeps a human in control of
          every lending decision.
        </p>
      </div>

      <ol className="mt-12 flex flex-col gap-4">
        {STEPS.map((step, i) => (
          <li key={step.title}>
            <Card className="flex flex-col gap-4 p-6 sm:flex-row sm:items-start">
              <div className="flex items-center gap-3 sm:w-56 sm:shrink-0">
                <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-sm font-semibold text-primary-foreground">
                  {i + 1}
                </span>
                <span className="flex size-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                  <step.icon className="size-5" aria-hidden />
                </span>
              </div>
              <div>
                <h2 className="font-semibold text-foreground">{step.title}</h2>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                  {step.text}
                </p>
              </div>
            </Card>
          </li>
        ))}
      </ol>

      <div className="mt-12 flex flex-wrap gap-3">
        <Button size="lg" render={<Link href="/lender/applications/APP-2041" />}>
          View Sample Assessment
        </Button>
        <Button size="lg" variant="outline" render={<Link href="/sign-in" />}>
          Request Demo
        </Button>
      </div>
    </div>
  )
}
