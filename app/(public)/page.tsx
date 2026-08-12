import Image from 'next/image'
import Link from 'next/link'
import {
  BarChart3,
  CheckCircle2,
  Eye,
  FileText,
  Fingerprint,
  Gauge,
  Layers,
  Lock,
  ScanLine,
  ShieldCheck,
  UserCheck,
  Users,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

const TRUST = ['Consent-based', 'Explainable', 'Human-reviewed']

const STEPS = [
  { icon: ShieldCheck, title: 'Consent', text: 'Borrower grants scoped, revocable consent for each data source.' },
  { icon: Layers, title: 'Data', text: 'Alternative financial data is uploaded or connected securely.' },
  { icon: Gauge, title: 'Score', text: 'A transparent model produces a calibrated default probability.' },
  { icon: Eye, title: 'Explain', text: 'SHAP-based reason codes explain every factor behind the score.' },
  { icon: UserCheck, title: 'Decide', text: 'A human analyst reviews and records the final decision.' },
]

const CAPABILITIES = [
  { icon: BarChart3, title: 'Alternative-data features', text: 'Income stability, cash-flow, utility payment behaviour, and gig-income signals engineered from raw records.' },
  { icon: Gauge, title: 'Calibrated risk scores', text: 'Probability of default with confidence and configurable risk bands, not arbitrary scores.' },
  { icon: Eye, title: 'Explainable by default', text: 'Every score carries SHAP factor contributions and plain-language reason codes.' },
  { icon: UserCheck, title: 'Human-in-the-loop', text: 'Analysts approve, reject, escalate, or override — with a reason on every decision.' },
  { icon: FileText, title: 'Tamper-evident audit', text: 'Append-only audit trail across consent, scoring, decisions, and overrides.' },
  { icon: ShieldCheck, title: 'Fairness monitoring', text: 'Selection rate, disparate impact, and error-rate gaps tracked per borrower segment.' },
]

const GOVERNANCE = [
  { icon: Lock, title: 'Data minimisation', text: 'Only data needed for assessment is collected, and sensitive attributes are isolated for fairness testing only.' },
  { icon: Fingerprint, title: 'Field-level protection', text: 'Sensitive borrower fields are encrypted and masked by default across the interface.' },
  { icon: FileText, title: 'Complete traceability', text: 'Model version, policy version, and data lineage are recorded for every decision.' },
]

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="border-b border-border bg-card">
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:py-24">
          <div className="flex flex-col gap-6">
            <span className="inline-flex w-fit items-center gap-2 rounded-full border border-border bg-accent px-3 py-1 text-xs font-medium text-accent-foreground">
              <ScanLine className="size-3.5" aria-hidden />
              Explainable alternative-data credit intelligence
            </span>
            <h1 className="text-balance text-4xl font-semibold leading-tight tracking-tight text-navy sm:text-5xl">
              Explainable credit intelligence for borrowers traditional models
              overlook.
            </h1>
            <p className="text-pretty text-lg leading-relaxed text-muted-foreground">
              Assess thin-file borrowers using alternative financial data,
              transparent machine learning, and human-controlled underwriting
              workflows.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <Button size="lg" render={<Link href="/sign-in" />}>
                Request a Demo
              </Button>
              <Button size="lg" variant="outline" render={<Link href="/how-it-works" />}>
                Explore the Platform
              </Button>
              <Button size="lg" variant="ghost" render={<Link href="/borrower" />}>
                Borrower Sign In
              </Button>
            </div>
            <ul className="flex flex-wrap gap-4 pt-2">
              {TRUST.map((t) => (
                <li key={t} className="inline-flex items-center gap-2 text-sm text-muted-foreground">
                  <CheckCircle2 className="size-4 text-risk-low" aria-hidden />
                  {t}
                </li>
              ))}
            </ul>
          </div>
          <div className="relative">
            <div className="overflow-hidden rounded-xl border border-border shadow-sm">
              <Image
                src="/dashboard-preview.png"
                alt="Preview of the MyCreditLens lender dashboard showing KPIs, charts, and an application queue"
                width={1200}
                height={900}
                className="h-auto w-full"
                priority
              />
            </div>
          </div>
        </div>
      </section>

      {/* Problem statement */}
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <div className="grid gap-8 lg:grid-cols-[1.2fr_1fr] lg:items-center">
          <div className="flex flex-col gap-4">
            <h2 className="text-3xl font-semibold tracking-tight text-navy">
              Thin-file borrowers are invisible to traditional scoring.
            </h2>
            <p className="text-pretty leading-relaxed text-muted-foreground">
              Gig workers, micro-entrepreneurs, and small merchants often lack a
              conventional credit history. Traditional models reject them by
              default — not because they are risky, but because they are
              unmeasured. MyCreditLens uses consented alternative data to make
              responsible, explainable assessments possible.
            </p>
          </div>
          <Card className="p-6">
            <div className="grid grid-cols-2 gap-6">
              {[
                { icon: Users, stat: '5', label: 'Borrower segments supported' },
                { icon: Layers, stat: '40+', label: 'Engineered risk features' },
                { icon: Eye, stat: '100%', label: 'Scores with explanations' },
                { icon: FileText, stat: 'Full', label: 'Decision audit trail' },
              ].map((s) => (
                <div key={s.label} className="flex flex-col gap-1">
                  <s.icon className="size-5 text-primary" aria-hidden />
                  <span className="text-2xl font-semibold text-navy">{s.stat}</span>
                  <span className="text-sm text-muted-foreground">{s.label}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </section>

      {/* How it works */}
      <section className="border-y border-border bg-card">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-semibold tracking-tight text-navy">
              How it works
            </h2>
            <p className="mt-3 text-muted-foreground">
              A transparent pipeline from consent to a human-recorded decision.
            </p>
          </div>
          <ol className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {STEPS.map((step, i) => (
              <li key={step.title}>
                <Card className="h-full p-5">
                  <div className="flex items-center gap-2">
                    <span className="flex size-8 items-center justify-center rounded-lg bg-accent text-sm font-semibold text-accent-foreground">
                      {i + 1}
                    </span>
                    <step.icon className="size-4.5 text-primary" aria-hidden />
                  </div>
                  <h3 className="mt-3 font-semibold text-foreground">{step.title}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                    {step.text}
                  </p>
                </Card>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Capabilities */}
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <div className="max-w-2xl">
          <h2 className="text-3xl font-semibold tracking-tight text-navy">
            Core capabilities
          </h2>
          <p className="mt-3 text-muted-foreground">
            Everything an underwriting team needs to assess alternative-data
            borrowers responsibly.
          </p>
        </div>
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {CAPABILITIES.map((c) => (
            <Card key={c.title} className="p-6">
              <span className="flex size-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                <c.icon className="size-5" aria-hidden />
              </span>
              <h3 className="mt-4 font-semibold text-foreground">{c.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                {c.text}
              </p>
            </Card>
          ))}
        </div>
      </section>

      {/* Explainable AI band */}
      <section className="border-y border-border bg-navy text-white">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:items-center">
          <div className="flex flex-col gap-4">
            <span className="inline-flex w-fit items-center gap-2 rounded-full border border-white/15 px-3 py-1 text-xs font-medium text-slate-200">
              <Eye className="size-3.5" aria-hidden />
              Explainable AI
            </span>
            <h2 className="text-3xl font-semibold tracking-tight text-balance">
              Every score is accountable to a reason.
            </h2>
            <p className="leading-relaxed text-slate-300">
              We never present a risk score without context. Each assessment
              shows the risk band, probability of default, confidence, top
              positive and negative factors, data quality, and model version —
              so analysts and borrowers understand exactly why.
            </p>
            <Button variant="outline" size="lg" className="w-fit border-white/20 bg-white/5 text-white hover:bg-white/10" render={<Link href="/responsible-ai" />}>
              Read our Responsible AI approach
            </Button>
          </div>
          <div className="grid gap-3">
            {[
              'High income volatility increased assessed risk.',
              'Consistent utility payments reduced assessed risk.',
              'A low liquidity buffer increased assessed risk.',
            ].map((r, i) => (
              <div
                key={r}
                className="flex items-center gap-3 rounded-lg border border-white/10 bg-white/5 px-4 py-3"
              >
                <span className={`size-2.5 shrink-0 rounded-full ${i === 1 ? 'bg-risk-low' : 'bg-risk-high'}`} />
                <span className="text-sm text-slate-100">{r}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Governance */}
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <div className="max-w-2xl">
          <h2 className="text-3xl font-semibold tracking-tight text-navy">
            Security and governance
          </h2>
          <p className="mt-3 text-muted-foreground">
            Built with responsible data handling and traceability at the core.
          </p>
        </div>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {GOVERNANCE.map((g) => (
            <Card key={g.title} className="p-6">
              <span className="flex size-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                <g.icon className="size-5" aria-hidden />
              </span>
              <h3 className="mt-4 font-semibold text-foreground">{g.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                {g.text}
              </p>
            </Card>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-border bg-card">
        <div className="mx-auto max-w-4xl px-4 py-16 text-center sm:px-6">
          <h2 className="text-3xl font-semibold tracking-tight text-navy text-balance">
            Bring explainable underwriting to your lending team.
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-muted-foreground">
            See how MyCreditLens fits into your review workflow with a guided
            walkthrough of the lender console.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Button size="lg" render={<Link href="/sign-in" />}>
              Request a Demo
            </Button>
            <Button size="lg" variant="outline" render={<Link href="/for-lenders" />}>
              For Lenders
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}
