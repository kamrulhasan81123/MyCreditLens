import Link from 'next/link'
import {
  Building2,
  Cloud,
  Gauge,
  PlugZap,
  ScaleIcon,
  Store,
  TrendingUp,
  UserCheck,
  Wallet,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

const USE_CASES = [
  { icon: Store, title: 'Micro-merchant financing', text: 'Assess small retailers using POS turnover and cash-flow stability.' },
  { icon: Wallet, title: 'Gig-worker lending', text: 'Score ride-hailing and delivery workers on income consistency.' },
  { icon: Building2, title: 'Micro-entrepreneur credit', text: 'Evaluate home businesses with limited formal credit history.' },
]

const BENEFITS = [
  { icon: Gauge, title: 'Faster, consistent triage', text: 'Automated scoring and policy checks prioritise the work queue so analysts focus on the cases that need judgement.' },
  { icon: UserCheck, title: 'Defensible decisions', text: 'Every decision is backed by an explanation, policy result, and audit record.' },
  { icon: ScaleIcon, title: 'Fairness visibility', text: 'Monitor approval-rate and error-rate gaps across borrower segments continuously.' },
  { icon: TrendingUp, title: 'Portfolio insight', text: 'Track predicted default, approval rates, and risk exposure across the book.' },
]

const DEPLOYMENT = [
  { icon: PlugZap, title: 'REST API', text: 'Score applications programmatically with scoped API keys and webhooks.' },
  { icon: Cloud, title: 'Flexible hosting', text: 'Run as a modular monolith on managed infrastructure or your own VPC.' },
]

export default function ForLendersPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      <div className="max-w-2xl">
        <h1 className="text-4xl font-semibold tracking-tight text-navy text-balance">
          Underwriting infrastructure for alternative-data lending
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
          Extend credit to underserved borrowers with explainable scoring,
          policy controls, and a human-in-the-loop review workflow.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Button size="lg" render={<Link href="/sign-in" />}>
            Book a Product Demo
          </Button>
          <Button size="lg" variant="outline" render={<Link href="/lender/api" />}>
            View API Capabilities
          </Button>
        </div>
      </div>

      <section className="mt-14">
        <h2 className="text-2xl font-semibold tracking-tight text-navy">Use cases</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {USE_CASES.map((u) => (
            <Card key={u.title} className="p-6">
              <span className="flex size-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                <u.icon className="size-5" aria-hidden />
              </span>
              <h3 className="mt-4 font-semibold text-foreground">{u.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{u.text}</p>
            </Card>
          ))}
        </div>
      </section>

      <section className="mt-14">
        <h2 className="text-2xl font-semibold tracking-tight text-navy">Workflow benefits</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {BENEFITS.map((b) => (
            <Card key={b.title} className="flex gap-4 p-6">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                <b.icon className="size-5" aria-hidden />
              </span>
              <div>
                <h3 className="font-semibold text-foreground">{b.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{b.text}</p>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section className="mt-14">
        <h2 className="text-2xl font-semibold tracking-tight text-navy">Integration & deployment</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {DEPLOYMENT.map((d) => (
            <Card key={d.title} className="flex gap-4 p-6">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                <d.icon className="size-5" aria-hidden />
              </span>
              <div>
                <h3 className="font-semibold text-foreground">{d.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{d.text}</p>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <Card className="mt-14 flex flex-col items-center gap-4 bg-navy p-10 text-center text-white">
        <h2 className="text-2xl font-semibold tracking-tight text-balance">
          Ready to see it in your workflow?
        </h2>
        <p className="max-w-xl text-slate-300">
          Explore the lender console with realistic sample applications and
          decisions.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Button size="lg" render={<Link href="/lender" />}>
            Open Lender Dashboard
          </Button>
          <Button
            size="lg"
            variant="outline"
            className="border-white/20 bg-white/5 text-white hover:bg-white/10"
            render={<Link href="/sign-in" />}
          >
            Book a Demo
          </Button>
        </div>
      </Card>
    </div>
  )
}
