import Link from 'next/link'
import { CheckCircle2, TriangleAlert } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

const PRINCIPLES = [
  {
    principle: 'Explainability',
    implementation: 'SHAP-based factor contributions with controlled reason-code templates for every score.',
    evidence: 'Explainability tab on each assessment + downloadable reports.',
    status: 'Implemented',
  },
  {
    principle: 'Fairness testing',
    implementation: 'Selection rate, disparate impact ratio, and error-rate gaps computed per borrower segment.',
    evidence: 'Fairness dashboard with per-group sample sizes.',
    status: 'Implemented',
  },
  {
    principle: 'Data minimisation',
    implementation: 'Only data required for assessment is collected; sensitive attributes are isolated for fairness evaluation only.',
    evidence: 'Consent scopes + field-level access controls.',
    status: 'Implemented',
  },
  {
    principle: 'Human oversight',
    implementation: 'Analysts retain final decision authority with mandatory reasons and override justifications.',
    evidence: 'Decision panel + audit trail on every application.',
    status: 'Implemented',
  },
  {
    principle: 'Model monitoring',
    implementation: 'Prediction and feature drift (PSI), calibration, and performance tracked over time.',
    evidence: 'Model monitoring dashboard with alerts.',
    status: 'Implemented',
  },
  {
    principle: 'Auditability',
    implementation: 'Append-only, optionally hash-chained audit records across all sensitive events.',
    evidence: 'Audit log with record integrity verification.',
    status: 'Implemented',
  },
]

export default function ResponsibleAiPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      <div className="max-w-2xl">
        <h1 className="text-4xl font-semibold tracking-tight text-navy text-balance">
          Responsible AI
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
          MyCreditLens is built so that automation supports — never replaces —
          human judgement, and so that every decision can be explained and
          audited.
        </p>
      </div>

      <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {PRINCIPLES.map((p) => (
          <Card key={p.principle} className="flex flex-col gap-3 p-6">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-foreground">{p.principle}</h2>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-risk-low/25 bg-risk-low/10 px-2.5 py-0.5 text-xs font-medium text-risk-low">
                <CheckCircle2 className="size-3.5" aria-hidden />
                {p.status}
              </span>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Implementation
              </p>
              <p className="mt-1 text-sm leading-relaxed text-foreground">
                {p.implementation}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Evidence
              </p>
              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                {p.evidence}
              </p>
            </div>
          </Card>
        ))}
      </div>

      <Card className="mt-8 border-risk-medium/30 bg-risk-medium/5 p-6">
        <div className="flex gap-3">
          <TriangleAlert className="size-5 shrink-0 text-risk-medium" aria-hidden />
          <div>
            <h2 className="font-semibold text-foreground">Limitations</h2>
            <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
              MyCreditLens is an academic prototype. It is not a certified
              banking system or a legally approved automated lending platform.
              Fairness metrics require careful interpretation and no model should
              be labelled &ldquo;fair&rdquo; based on a single metric. Alternative-data
              features can act as proxies for socioeconomic status and are
              reviewed accordingly.
            </p>
          </div>
        </div>
      </Card>

      <div className="mt-10 flex flex-wrap gap-3">
        <Button size="lg" render={<Link href="/for-lenders" />}>
          Read Governance Framework
        </Button>
        <Button size="lg" variant="outline" render={<Link href="/sign-in" />}>
          Contact Compliance Team
        </Button>
      </div>
    </div>
  )
}
