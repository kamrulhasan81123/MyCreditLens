'use client'

import { useState } from 'react'
import {
  CircleAlert,
  CircleCheck,
  CircleX,
  Database,
  ShieldCheck,
} from 'lucide-react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { DATA_SOURCE_LABEL, formatPercent } from '@/lib/format'
import {
  RELIABILITY_LABEL_COPY,
  type DataReliabilitySource,
  type ReliabilityLabel,
} from '@/src/features/applications/types/advanced-risk.types'
import {
  getDataReliability,
  type DataReliabilitySummary,
} from '@/src/features/applications/mock-data/advanced-risk.mock'
import type { Application } from '@/lib/types'
import { cn } from '@/lib/utils'

const LABEL_STYLES: Record<ReliabilityLabel, string> = {
  excellent: 'text-risk-low',
  good: 'text-risk-low',
  limited: 'text-risk-medium',
  insufficient: 'text-risk-high',
}

const VALIDATION_META: Record<
  DataReliabilitySource['validationStatus'],
  { icon: typeof CircleCheck; className: string; label: string }
> = {
  passed: { icon: CircleCheck, className: 'text-risk-low', label: 'Passed' },
  warning: { icon: CircleAlert, className: 'text-risk-medium', label: 'Warning' },
  failed: { icon: CircleX, className: 'text-risk-high', label: 'Failed' },
}

function labelForType(type: string): string {
  return DATA_SOURCE_LABEL[type as keyof typeof DATA_SOURCE_LABEL] ?? type
}

export function DataReliabilityCard({
  application,
  summary: summaryProp,
  variant = 'full',
  className,
}: {
  application?: Application
  summary?: DataReliabilitySummary
  variant?: 'full' | 'condensed'
  className?: string
}) {
  const [active, setActive] = useState<DataReliabilitySource | null>(null)
  const summary = summaryProp ?? (application ? getDataReliability(application) : undefined)

  if (!summary) return null

  const label = labelFromScore(summary.overallScore)

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="size-4 text-primary" />
              Data reliability
            </CardTitle>
            <CardDescription>
              Quality, completeness and consistency of the underlying borrower data.
            </CardDescription>
          </div>
          <div className="text-right">
            <div className="text-2xl font-semibold tabular-nums text-foreground">
              {summary.overallScore}
              <span className="text-sm text-muted-foreground">/100</span>
            </div>
            <div className={cn('text-xs font-medium', LABEL_STYLES[label])}>
              {RELIABILITY_LABEL_COPY[label]}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <Progress value={summary.overallScore} aria-label={`Reliability score ${summary.overallScore} of 100`} />

        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3">
          <Stat label="Data sources" value={String(summary.sourceCount)} />
          <Stat label="Date coverage" value={`${summary.coverageMonths} months`} />
          <Stat label="Missing-data rate" value={formatPercent(summary.missingRate, 1)} />
          <Stat label="Extraction confidence" value={formatPercent(summary.extractionConfidence, 0)} />
          <Stat
            label="Consistency"
            value={
              summary.consistency === 'consistent'
                ? 'Consistent'
                : summary.consistency === 'minor_issues'
                  ? 'Minor issues'
                  : 'Inconsistent'
            }
          />
        </dl>

        {variant === 'full' && (
          <div className="overflow-x-auto rounded-lg border border-border">
            <Table>
              <TableHeader>
                <TableRow className="bg-secondary/60">
                  <TableHead>Data source</TableHead>
                  <TableHead className="text-right">Score</TableHead>
                  <TableHead>Coverage</TableHead>
                  <TableHead className="text-right">Records</TableHead>
                  <TableHead className="text-right">Missing</TableHead>
                  <TableHead>Validation</TableHead>
                  <TableHead>Main issue</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {summary.sources.map((s) => {
                  const meta = VALIDATION_META[s.validationStatus]
                  const Icon = meta.icon
                  return (
                    <TableRow key={s.id}>
                      <TableCell className="font-medium text-foreground">
                        {labelForType(s.sourceType)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{s.score}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {s.coverageStart} – {s.coverageEnd}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{s.recordCount}</TableCell>
                      <TableCell className="text-right tabular-nums">
                        {formatPercent(s.missingRate, 1)}
                      </TableCell>
                      <TableCell>
                        <span className={cn('inline-flex items-center gap-1.5 text-xs font-medium', meta.className)}>
                          <Icon className="size-3.5" />
                          {meta.label}
                        </span>
                      </TableCell>
                      <TableCell className="max-w-[180px] text-xs text-muted-foreground">
                        {s.mainIssue ?? '—'}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm" onClick={() => setActive(s)}>
                          View source
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>

      <Sheet open={active !== null} onOpenChange={(open) => !open && setActive(null)}>
        <SheetContent className="w-full overflow-y-auto sm:max-w-md">
          {active && (
            <>
              <SheetHeader>
                <SheetTitle className="flex items-center gap-2">
                  <Database className="size-4 text-primary" />
                  {labelForType(active.sourceType)}
                </SheetTitle>
                <SheetDescription>
                  Reliability score {active.score}/100 · {RELIABILITY_LABEL_COPY[active.label]}
                </SheetDescription>
              </SheetHeader>
              <div className="space-y-4 px-4 pb-6">
                <DrawerRow label="Coverage period" value={`${active.coverageStart} – ${active.coverageEnd}`} />
                <DrawerRow label="Record count" value={String(active.recordCount)} />
                <DrawerRow label="Missing-data rate" value={formatPercent(active.missingRate, 1)} />
                <DrawerRow
                  label="Validation status"
                  value={VALIDATION_META[active.validationStatus].label}
                />
                <DrawerRow label="Main issue" value={active.mainIssue ?? 'None detected'} />
                <div className="flex flex-wrap gap-2 pt-2">
                  <Button variant="outline" size="sm">View issues</Button>
                  <Button variant="outline" size="sm">Reprocess</Button>
                  <Button variant="outline" size="sm">Request replacement</Button>
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </Card>
  )
}

function labelFromScore(score: number): ReliabilityLabel {
  if (score >= 85) return 'excellent'
  if (score >= 70) return 'good'
  if (score >= 50) return 'limited'
  return 'insufficient'
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-0.5">
      <dt className="text-xs uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className="text-sm font-medium text-foreground">{value}</dd>
    </div>
  )
}

function DrawerRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border pb-3">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-right text-sm font-medium text-foreground">{value}</span>
    </div>
  )
}
