'use client'

import { useMemo, useState } from 'react'
import {
  AlertOctagon,
  CheckCircle2,
  FileSearch,
  ShieldAlert,
  ShieldCheck,
  ShieldQuestion,
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { cn } from '@/lib/utils'
import { formatDateTime } from '@/lib/format'
import { toast } from 'sonner'
import type { Application } from '@/lib/types'
import {
  getIntegrityAlerts,
  getEvidenceTraceForAlert,
} from '@/src/features/applications/mock-data/advanced-risk.mock'
import type { IntegrityAlert } from '@/src/features/applications/types/advanced-risk.types'
import { useEvidenceDrawer } from '@/src/features/applications/components/evidence/evidence-drawer'

const severityStyle: Record<
  IntegrityAlert['severity'],
  { badge: string; border: string; icon: string }
> = {
  info: { badge: 'bg-action/10 text-action', border: 'border-action/30', icon: 'text-action' },
  warning: {
    badge: 'bg-risk-medium/10 text-risk-medium',
    border: 'border-risk-medium/30',
    icon: 'text-risk-medium',
  },
  critical: {
    badge: 'bg-risk-high/10 text-risk-high',
    border: 'border-risk-high/30',
    icon: 'text-risk-high',
  },
}

const categoryMeta: Record<
  IntegrityAlert['category'],
  { label: string; icon: React.ComponentType<{ className?: string }> }
> = {
  credit: { label: 'Credit risk', icon: ShieldAlert },
  fraud: { label: 'Fraud signal', icon: AlertOctagon },
  data_integrity: { label: 'Data integrity', icon: FileSearch },
}

export function IntegrityAlertsPanel({ application }: { application: Application }) {
  const initial = useMemo(() => getIntegrityAlerts(application), [application])
  const [alerts, setAlerts] = useState<IntegrityAlert[]>(initial)
  const [dismissing, setDismissing] = useState<IntegrityAlert | null>(null)
  const [reason, setReason] = useState('')
  const { openTrace } = useEvidenceDrawer()

  const active = alerts.filter((a) => !a.dismissed)
  const dismissed = alerts.filter((a) => a.dismissed)

  const counts = {
    credit: active.filter((a) => a.category === 'credit').length,
    fraud: active.filter((a) => a.category === 'fraud').length,
    data_integrity: active.filter((a) => a.category === 'data_integrity').length,
  }

  function confirmDismiss() {
    if (!dismissing || reason.trim().length < 10) return
    setAlerts((prev) =>
      prev.map((a) =>
        a.id === dismissing.id
          ? { ...a, dismissed: true, dismissReason: reason.trim() }
          : a,
      ),
    )
    toast.success('Alert dismissed', { description: 'Recorded to the audit trail.' })
    setDismissing(null)
    setReason('')
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <ShieldQuestion className="size-4 text-action" />
          <CardTitle className="text-base">Integrity &amp; fraud signals</CardTitle>
        </div>
        <CardDescription>
          Fraud and data-integrity signals are tracked separately from the credit risk score so a
          data problem is never mistaken for credit risk.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-3 sm:grid-cols-3">
          {(Object.keys(categoryMeta) as IntegrityAlert['category'][]).map((cat) => {
            const meta = categoryMeta[cat]
            const count = counts[cat]
            const Icon = meta.icon
            return (
              <div
                key={cat}
                className={cn(
                  'rounded-lg border p-3',
                  count > 0 ? 'border-risk-high/30 bg-risk-high/5' : 'border-border bg-muted/30',
                )}
              >
                <div className="flex items-center justify-between">
                  <Icon
                    className={cn('size-4', count > 0 ? 'text-risk-high' : 'text-muted-foreground')}
                  />
                  {count > 0 ? (
                    <Badge className="bg-risk-high/10 text-risk-high">{count}</Badge>
                  ) : (
                    <CheckCircle2 className="size-4 text-risk-low" />
                  )}
                </div>
                <p className="mt-2 text-sm font-medium text-foreground">{meta.label}</p>
                <p className="text-xs text-muted-foreground">
                  {count > 0 ? `${count} active signal${count === 1 ? '' : 's'}` : 'No signals'}
                </p>
              </div>
            )
          })}
        </div>

        {active.length === 0 ? (
          <div className="flex items-center gap-3 rounded-lg border border-risk-low/30 bg-risk-low/5 p-4">
            <ShieldCheck className="size-5 text-risk-low" />
            <div>
              <p className="text-sm font-medium text-foreground">No active integrity concerns</p>
              <p className="text-xs text-muted-foreground">
                All fraud and data-integrity checks passed for this application.
              </p>
            </div>
          </div>
        ) : (
          <ul className="space-y-3">
            {active.map((alert) => {
              const style = severityStyle[alert.severity]
              const Icon = categoryMeta[alert.category].icon
              return (
                <li
                  key={alert.id}
                  className={cn('rounded-lg border bg-card p-4', style.border)}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <Icon className={cn('mt-0.5 size-5 shrink-0', style.icon)} />
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="text-sm font-medium text-foreground">{alert.title}</p>
                          <Badge className={cn('capitalize', style.badge)}>
                            {alert.severity}
                          </Badge>
                        </div>
                        <p className="mt-1 text-sm text-muted-foreground">{alert.description}</p>
                        <p className="mt-2 text-xs text-muted-foreground">
                          Detected {formatDateTime(alert.detectedAt)}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2 border-t border-border/60 pt-3">
                    {alert.hasEvidence && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openTrace(getEvidenceTraceForAlert(application, alert))}
                      >
                        <FileSearch className="size-4" />
                        View evidence
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setDismissing(alert)
                        setReason('')
                      }}
                    >
                      Dismiss with reason
                    </Button>
                  </div>
                </li>
              )
            })}
          </ul>
        )}

        {dismissed.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Dismissed ({dismissed.length})
            </p>
            <ul className="space-y-2">
              {dismissed.map((alert) => (
                <li
                  key={alert.id}
                  className="rounded-lg border border-border bg-muted/30 p-3 text-sm"
                >
                  <p className="font-medium text-muted-foreground line-through">{alert.title}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Reason: {alert.dismissReason}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>

      <Dialog open={!!dismissing} onOpenChange={(o) => !o && setDismissing(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Dismiss integrity signal</DialogTitle>
            <DialogDescription>
              Dismissing “{dismissing?.title}” requires a documented reason. This is recorded to the
              audit trail.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why this signal can be safely dismissed (minimum 10 characters)…"
              rows={4}
            />
            <p className="text-xs text-muted-foreground">{reason.trim().length}/10 characters minimum</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDismissing(null)}>
              Cancel
            </Button>
            <Button onClick={confirmDismiss} disabled={reason.trim().length < 10}>
              Dismiss signal
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
