'use client'

import {
  AlertTriangle,
  CheckCircle2,
  FileText,
  FilePlus2,
  Gavel,
  GitCompareArrows,
  MessageSquare,
  Send,
  ShieldCheck,
  Sparkles,
  UserCheck,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatDateTime } from '@/lib/format'
import type {
  TimelineEvent,
  TimelineEventType,
} from '@/src/features/applications/types/advanced-risk.types'

const eventMeta: Record<
  TimelineEventType,
  { icon: React.ComponentType<{ className?: string }>; tone: 'default' | 'positive' | 'warning' | 'critical' }
> = {
  application_created: { icon: FilePlus2, tone: 'default' },
  application_submitted: { icon: Send, tone: 'default' },
  consent_granted: { icon: ShieldCheck, tone: 'positive' },
  document_uploaded: { icon: FileText, tone: 'default' },
  data_validated: { icon: CheckCircle2, tone: 'positive' },
  data_issue_detected: { icon: AlertTriangle, tone: 'warning' },
  features_generated: { icon: Sparkles, tone: 'default' },
  risk_score_generated: { icon: Sparkles, tone: 'default' },
  manual_review_requested: { icon: UserCheck, tone: 'warning' },
  information_requested: { icon: MessageSquare, tone: 'warning' },
  borrower_responded: { icon: MessageSquare, tone: 'default' },
  analyst_decision_recorded: { icon: Gavel, tone: 'positive' },
  decision_overridden: { icon: GitCompareArrows, tone: 'critical' },
  appeal_submitted: { icon: Send, tone: 'warning' },
  appeal_resolved: { icon: CheckCircle2, tone: 'positive' },
}

const toneStyle: Record<string, { ring: string; icon: string }> = {
  default: { ring: 'border-border bg-card', icon: 'text-muted-foreground' },
  positive: { ring: 'border-risk-low/40 bg-risk-low/5', icon: 'text-risk-low' },
  warning: { ring: 'border-risk-medium/40 bg-risk-medium/5', icon: 'text-risk-medium' },
  critical: { ring: 'border-risk-high/40 bg-risk-high/5', icon: 'text-risk-high' },
}

export function EnhancedTimeline({
  events,
  variant = 'full',
  limit,
}: {
  events: TimelineEvent[]
  variant?: 'full' | 'compact'
  limit?: number
}) {
  const shown = limit ? events.slice(0, limit) : events

  if (shown.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
        No activity recorded yet.
      </p>
    )
  }

  return (
    <ol className="relative">
      {shown.map((event, index) => {
        const meta = eventMeta[event.type]
        const tone = toneStyle[meta.tone]
        const Icon = meta.icon
        const isLast = index === shown.length - 1
        return (
          <li key={event.id} className="relative flex gap-3 pb-4 last:pb-0">
            <div className="flex flex-col items-center">
              <span
                className={cn(
                  'flex size-8 shrink-0 items-center justify-center rounded-full border',
                  tone.ring,
                )}
              >
                <Icon className={cn('size-4', tone.icon)} />
              </span>
              {!isLast && <span className="mt-1 w-px flex-1 bg-border" />}
            </div>
            <div className={cn('flex-1', variant === 'full' ? 'pb-1' : 'pb-0')}>
              <div className="flex flex-wrap items-center justify-between gap-x-3">
                <p className="text-sm font-medium text-foreground">{event.title}</p>
                <time className="text-xs text-muted-foreground">
                  {formatDateTime(event.timestamp)}
                </time>
              </div>
              {variant === 'full' && (
                <p className="mt-0.5 text-sm text-muted-foreground">{event.description}</p>
              )}
              <p className="mt-0.5 text-xs text-muted-foreground">
                {event.actor}
                {event.relatedRecord && variant === 'full' ? ` · ${event.relatedRecord}` : ''}
              </p>
            </div>
          </li>
        )
      })}
    </ol>
  )
}
