'use client'

import { useState } from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  Info,
  MessageSquarePlus,
  ShieldQuestion,
  UserPlus,
} from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type {
  ManualReviewReason,
  ReviewSeverity,
} from '@/src/features/applications/types/advanced-risk.types'

const severityConfig: Record<
  ReviewSeverity,
  { icon: React.ElementType; dot: string; text: string; ring: string; label: string }
> = {
  info: {
    icon: Info,
    dot: 'bg-info',
    text: 'text-info',
    ring: 'border-info/25 bg-info/5',
    label: 'Info',
  },
  warning: {
    icon: AlertTriangle,
    dot: 'bg-risk-medium',
    text: 'text-risk-medium',
    ring: 'border-risk-medium/25 bg-risk-medium/5',
    label: 'Warning',
  },
  critical: {
    icon: AlertTriangle,
    dot: 'bg-risk-high',
    text: 'text-risk-high',
    ring: 'border-risk-high/25 bg-risk-high/5',
    label: 'Critical',
  },
}

export function ManualReviewReasonsCard({
  reasons,
  onContinueDecision,
}: {
  reasons: ManualReviewReason[]
  onContinueDecision?: () => void
}) {
  const [resolved, setResolved] = useState<Record<string, boolean>>({})

  const withState = reasons.map((r) => ({ ...r, resolved: resolved[r.id] ?? r.resolved }))
  const outstanding = withState.filter((r) => !r.resolved)
  const overallSeverity: ReviewSeverity = outstanding.some((r) => r.severity === 'critical')
    ? 'critical'
    : outstanding.some((r) => r.severity === 'warning')
      ? 'warning'
      : 'info'

  // Empty state — no manual-review triggers.
  if (reasons.length === 0) {
    return (
      <Card className="border-risk-low/30 bg-risk-low/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <CheckCircle2 className="size-5 text-risk-low" aria-hidden />
            No manual-review triggers
          </CardTitle>
          <CardDescription>
            Automated checks did not flag any conditions requiring manual review for this
            application.
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className="border-review/30">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-2 text-review">
            <ShieldQuestion className="size-5" aria-hidden />
            Manual review required
          </CardTitle>
          <span
            className={cn(
              'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium',
              severityConfig[overallSeverity].ring,
              severityConfig[overallSeverity].text,
            )}
          >
            {outstanding.length} of {reasons.length} outstanding
          </span>
        </div>
        <CardDescription>
          Resolve or acknowledge each requirement before recording a final decision.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <ol className="space-y-3">
          {withState.map((reason, index) => {
            const config = severityConfig[reason.severity]
            const Icon = config.icon
            return (
              <li
                key={reason.id}
                className={cn(
                  'rounded-lg border p-4 transition-colors',
                  reason.resolved ? 'border-border bg-muted/40' : config.ring,
                )}
              >
                <div className="flex items-start gap-3">
                  <span
                    className={cn(
                      'mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold',
                      reason.resolved
                        ? 'bg-risk-low/15 text-risk-low'
                        : cn('bg-background', config.text),
                    )}
                  >
                    {reason.resolved ? <CheckCircle2 className="size-4" aria-hidden /> : index + 1}
                  </span>
                  <div className="min-w-0 flex-1 space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={cn(
                          'text-sm font-medium',
                          reason.resolved ? 'text-muted-foreground line-through' : 'text-foreground',
                        )}
                      >
                        {reason.title}
                      </span>
                      <span
                        className={cn(
                          'inline-flex items-center gap-1 text-[11px] font-medium uppercase tracking-wide',
                          reason.resolved ? 'text-muted-foreground' : config.text,
                        )}
                      >
                        <Icon className="size-3" aria-hidden />
                        {config.label}
                      </span>
                    </div>
                    <p className="text-sm leading-relaxed text-muted-foreground">
                      {reason.description}
                    </p>
                    <div className="flex flex-wrap gap-2 pt-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 text-xs"
                        onClick={() =>
                          setResolved((prev) => ({ ...prev, [reason.id]: !prev[reason.id] }))
                        }
                      >
                        {reason.resolved ? 'Reopen' : 'Resolve requirement'}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 text-xs"
                        onClick={() => toast.info('Reviewer assignment opens in the review queue.')}
                      >
                        <UserPlus className="size-3.5" aria-hidden />
                        Assign reviewer
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 text-xs"
                        onClick={() => toast.info('Add a review note from the Analyst Notes tab.')}
                      >
                        <MessageSquarePlus className="size-3.5" aria-hidden />
                        Add note
                      </Button>
                    </div>
                  </div>
                </div>
              </li>
            )
          })}
        </ol>

        <Button
          className="w-full"
          variant={outstanding.length === 0 ? 'default' : 'outline'}
          onClick={onContinueDecision}
        >
          <ClipboardCheck className="size-4" aria-hidden />
          {outstanding.length === 0 ? 'Continue to decision' : 'Continue decision with open items'}
        </Button>
      </CardContent>
    </Card>
  )
}
