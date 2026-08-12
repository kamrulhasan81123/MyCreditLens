'use client'

import { GitCompareArrows, TriangleAlert } from 'lucide-react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { RiskBadge } from '@/components/risk/badges'
import { formatPercent } from '@/lib/format'
import { MODEL_AGREEMENT_COPY } from '@/src/features/applications/types/advanced-risk.types'
import {
  getModelComparisons,
  type ModelAgreementSummary,
} from '@/src/features/applications/mock-data/advanced-risk.mock'
import type { Application } from '@/lib/types'
import { cn } from '@/lib/utils'

const BAND_MAP = { low: 'LOW', medium: 'MEDIUM', high: 'HIGH' } as const

const LEVEL_STYLES: Record<ModelAgreementSummary['level'], string> = {
  strong: 'text-risk-low',
  moderate: 'text-risk-medium',
  weak: 'text-risk-high',
}

const CALIBRATION_STYLES: Record<string, string> = {
  good: 'text-risk-low',
  warning: 'text-risk-medium',
  poor: 'text-risk-high',
}

export function ModelAgreementCard({
  application,
  summary: summaryProp,
  onSendToReview,
  className,
}: {
  application?: Application
  summary?: ModelAgreementSummary
  onSendToReview?: () => void
  className?: string
}) {
  const summary = summaryProp ?? (application ? getModelComparisons(application) : undefined)
  if (!summary) return null

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <GitCompareArrows className="size-4 text-primary" />
              Model agreement &amp; uncertainty
            </CardTitle>
            <CardDescription>
              Multiple models score this borrower. The system can abstain when they disagree.
            </CardDescription>
          </div>
          <div className="text-right">
            <div className={cn('text-lg font-semibold', LEVEL_STYLES[summary.level])}>
              {MODEL_AGREEMENT_COPY[summary.level]} agreement
            </div>
            <div className="text-xs text-muted-foreground">
              Spread {summary.spread} pts · SD {summary.standardDeviation} pts
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="overflow-x-auto rounded-lg border border-border">
          <Table>
            <TableHeader>
              <TableRow className="bg-secondary/60">
                <TableHead>Model</TableHead>
                <TableHead className="text-right">PD</TableHead>
                <TableHead>Risk band</TableHead>
                <TableHead className="text-right">Confidence</TableHead>
                <TableHead>Calibration</TableHead>
                <TableHead>Version</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {summary.models.map((m) => (
                <TableRow key={m.modelId}>
                  <TableCell className="font-medium text-foreground">{m.modelName}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatPercent(m.probabilityOfDefault, 1)}
                  </TableCell>
                  <TableCell>
                    <RiskBadge band={BAND_MAP[m.riskBand]} />
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatPercent(m.confidence, 0)}
                  </TableCell>
                  <TableCell>
                    <span className={cn('text-xs font-medium capitalize', CALIBRATION_STYLES[m.calibrationStatus])}>
                      {m.calibrationStatus}
                    </span>
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">{m.version}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <div className="rounded-lg border border-border bg-secondary/40 p-4 text-sm">
          <p className="text-foreground">
            All models agree on risk band:{' '}
            <span className="font-medium">{summary.sameRiskBand ? 'Yes' : 'No'}</span>
          </p>
          <p className="mt-1 text-muted-foreground">{summary.recommendedAction}</p>
        </div>

        {summary.level === 'weak' && (
          <div className="flex flex-col gap-3 rounded-lg border border-risk-high/30 bg-risk-high/10 p-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="flex items-start gap-2 text-sm text-foreground">
              <TriangleAlert className="mt-0.5 size-4 shrink-0 text-risk-high" />
              Manual review recommended because model predictions differ significantly.
            </p>
            <div className="flex shrink-0 gap-2">
              <Button variant="outline" size="sm">View model details</Button>
              <Button size="sm" onClick={onSendToReview}>
                Send to manual review
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
