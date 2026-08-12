'use client'

import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { ArrowRight, Database, FileText, GitBranch, Info } from 'lucide-react'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { cn } from '@/lib/utils'
import { formatCurrency, formatDateTime } from '@/lib/format'
import type { EvidenceTrace } from '@/src/features/applications/types/advanced-risk.types'

interface EvidenceDrawerContextValue {
  openTrace: (trace: EvidenceTrace) => void
}

const EvidenceDrawerContext = createContext<EvidenceDrawerContextValue | null>(null)

export function useEvidenceDrawer() {
  const ctx = useContext(EvidenceDrawerContext)
  if (!ctx) {
    throw new Error('useEvidenceDrawer must be used within an EvidenceDrawerProvider')
  }
  return ctx
}

export function EvidenceDrawerProvider({ children }: { children: React.ReactNode }) {
  const [trace, setTrace] = useState<EvidenceTrace | null>(null)
  const [open, setOpen] = useState(false)

  const openTrace = useCallback((next: EvidenceTrace) => {
    setTrace(next)
    setOpen(true)
  }, [])

  const value = useMemo(() => ({ openTrace }), [openTrace])

  return (
    <EvidenceDrawerContext.Provider value={value}>
      {children}
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent className="w-full gap-0 overflow-y-auto p-0 sm:max-w-xl">
          {trace && <EvidenceContent trace={trace} />}
        </SheetContent>
      </Sheet>
    </EvidenceDrawerContext.Provider>
  )
}

function EvidenceContent({ trace }: { trace: EvidenceTrace }) {
  const increasesRisk = trace.effectOnRisk === 'increases_risk'
  return (
    <>
      <SheetHeader className="border-b border-border p-5">
        <div className="flex items-center gap-2">
          <SheetTitle>{trace.factorName}</SheetTitle>
          <Badge
            className={cn(
              increasesRisk ? 'bg-risk-high/10 text-risk-high' : 'bg-risk-low/10 text-risk-low',
            )}
          >
            {increasesRisk ? 'Increases risk' : 'Reduces risk'}
          </Badge>
        </div>
        <SheetDescription>
          Traced from {trace.sourceCount} source record{trace.sourceCount === 1 ? '' : 's'} · last
          calculated {formatDateTime(trace.lastCalculated)}
        </SheetDescription>
      </SheetHeader>

      <div className="space-y-6 p-5">
        <section>
          <SectionTitle icon={Info} label="Feature definition" />
          <dl className="rounded-lg border border-border bg-muted/30 p-4 text-sm">
            <Row label="Feature" value={trace.feature.name} mono />
            <Row label="Formula" value={trace.feature.formula} mono />
            <Row label="Borrower value" value={trace.feature.borrowerValue} />
            <Row label="Reference range" value={trace.feature.referenceRange} />
            <Row label="Version" value={trace.feature.version} mono last />
          </dl>
        </section>

        <section>
          <SectionTitle icon={Database} label={`Source records (${trace.sources.length})`} />
          <div className="overflow-hidden rounded-lg border border-border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">Used</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {trace.sources.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                      {new Date(row.date).toLocaleDateString('en-GB', {
                        day: '2-digit',
                        month: 'short',
                      })}
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-foreground">{row.source}</span>
                      <span className="block text-xs text-muted-foreground">
                        {row.description}
                      </span>
                    </TableCell>
                    <TableCell className="text-right text-sm tabular-nums text-foreground">
                      {formatCurrency(row.amount)}
                    </TableCell>
                    <TableCell className="text-right">
                      {row.included ? (
                        <Badge className="bg-risk-low/10 text-risk-low">Yes</Badge>
                      ) : (
                        <Badge className="bg-muted text-muted-foreground">Excluded</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>

        <section>
          <SectionTitle icon={GitBranch} label="Data lineage" />
          <ol className="space-y-3">
            <LineageStep
              icon={FileText}
              title="Original source"
              detail={trace.lineage.originalSource}
            />
            <LineageStep
              icon={ArrowRight}
              title="Processing step"
              detail={trace.lineage.processingStep}
            />
            <LineageStep
              icon={Database}
              title="Feature generated"
              detail={`${formatDateTime(trace.lineage.generatedAt)} · model ${trace.lineage.modelVersion}`}
              last
            />
          </ol>
        </section>
      </div>
    </>
  )
}

function SectionTitle({
  icon: Icon,
  label,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
}) {
  return (
    <div className="mb-2 flex items-center gap-2">
      <Icon className="size-4 text-action" />
      <h3 className="text-sm font-semibold text-foreground">{label}</h3>
    </div>
  )
}

function Row({
  label,
  value,
  mono,
  last,
}: {
  label: string
  value: string
  mono?: boolean
  last?: boolean
}) {
  return (
    <div
      className={cn(
        'flex items-start justify-between gap-4 py-1.5',
        !last && 'border-b border-border/60',
      )}
    >
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd
        className={cn(
          'text-right text-foreground',
          mono ? 'break-all font-mono text-xs' : 'text-sm',
        )}
      >
        {value}
      </dd>
    </div>
  )
}

function LineageStep({
  icon: Icon,
  title,
  detail,
  last,
}: {
  icon: React.ComponentType<{ className?: string }>
  title: string
  detail: string
  last?: boolean
}) {
  return (
    <li className="relative flex gap-3 pl-1">
      <div className="flex flex-col items-center">
        <span className="flex size-7 items-center justify-center rounded-full border border-border bg-card">
          <Icon className="size-3.5 text-action" />
        </span>
        {!last && <span className="mt-1 h-full w-px flex-1 bg-border" />}
      </div>
      <div className={cn(!last && 'pb-3')}>
        <p className="text-sm font-medium text-foreground">{title}</p>
        <p className="text-xs text-muted-foreground">{detail}</p>
      </div>
    </li>
  )
}
