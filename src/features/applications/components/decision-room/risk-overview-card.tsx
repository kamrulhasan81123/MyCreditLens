'use client'

import { BarChart3, GitCompareArrows, LineChart } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { RiskBadge } from '@/components/risk/badges'
import { formatDateTime, formatPercent } from '@/lib/format'
import { cn } from '@/lib/utils'
import {
  MODEL_AGREEMENT_COPY,
  RECOMMENDED_ACTION_COPY,
  RELIABILITY_LABEL_COPY,
  reliabilityLabelFromScore,
  type RiskOverview,
} from '@/src/features/applications/types/advanced-risk.types'

const BAND_MAP = { low: 'LOW', medium: 'MEDIUM', high: 'HIGH' } as const

const agreementStyles: Record<RiskOverview['modelAgreement'], string> = {
  strong: 'text-risk-low',
  moderate: 'text-risk-medium',
  weak: 'text-risk-high',
}

const actionStyles: Record<RiskOverview['recommendedAction'], string> = {
  approve: 'text-risk-low',
  reject: 'text-risk-high',
  manual_review: 'text-review',
  request_information: 'text-info',
}

export function RiskOverviewCard({
  overview,
  onViewRiskAnalysis,
  onCompareModels,
  onRunStressTest,
}: {
  overview: RiskOverview
  onViewRiskAnalysis?: () => void
  onCompareModels?: () => void
  onRunStressTest?: () => void
}) {
  const reliabilityLabel = reliabilityLabelFromScore(overview.dataReliabilityScore)

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <CardTitle>Risk overview</CardTitle>
        <RiskBadge band={BAND_MAP[overview.riskBand]} />
      </CardHeader>
      <CardContent className="space-y-6">
        <dl className="grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-4">
          <Stat
            label="Probability of default"
            value={formatPercent(overview.probabilityOfDefault, 1)}
            emphasis
          />
          <Stat label="Prediction confidence" value={formatPercent(overview.confidence, 0)} />
          <Stat
            label="Recommended action"
            value={RECOMMENDED_ACTION_COPY[overview.recommendedAction]}
            valueClassName={actionStyles[overview.recommendedAction]}
          />
          <Stat
            label="Data reliability"
            value={`${overview.dataReliabilityScore} · ${RELIABILITY_LABEL_COPY[reliabilityLabel]}`}
          />
          <Stat
            label="Model agreement"
            value={MODEL_AGREEMENT_COPY[overview.modelAgreement]}
            valueClassName={agreementStyles[overview.modelAgreement]}
          />
          <Stat label="Model version" value={overview.modelVersion} mono />
          <Stat
            label="Scored"
            value={formatDateTime(overview.scoredAt)}
            className="col-span-2"
          />
        </dl>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={onViewRiskAnalysis}>
            <BarChart3 className="size-4" aria-hidden />
            View full risk analysis
          </Button>
          <Button variant="outline" size="sm" onClick={onCompareModels}>
            <GitCompareArrows className="size-4" aria-hidden />
            Compare models
          </Button>
          <Button variant="outline" size="sm" onClick={onRunStressTest}>
            <LineChart className="size-4" aria-hidden />
            Run stress test
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function Stat({
  label,
  value,
  emphasis,
  mono,
  valueClassName,
  className,
}: {
  label: string
  value: string
  emphasis?: boolean
  mono?: boolean
  valueClassName?: string
  className?: string
}) {
  return (
    <div className={cn('space-y-1', className)}>
      <dt className="flex items-center gap-1 text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </dt>
      <dd
        className={cn(
          'font-medium text-foreground',
          emphasis ? 'text-2xl tabular-nums' : 'text-sm',
          mono && 'break-all font-mono text-xs',
          valueClassName,
        )}
      >
        {value}
      </dd>
    </div>
  )
}

export function RiskOverviewCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk overview</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-5 sm:grid-cols-4" aria-hidden>
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="space-y-2">
              <div className="h-3 w-20 rounded bg-muted" />
              <div className="h-5 w-16 rounded bg-muted" />
            </div>
          ))}
        </div>
        <span className="sr-only">Loading risk overview</span>
      </CardContent>
    </Card>
  )
}
