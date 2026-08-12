'use client'

import { forwardRef, useState } from 'react'
import {
  CheckCircle2,
  FileText,
  MinusCircle,
  ShieldCheck,
  XCircle,
} from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import type { Application, DecisionType } from '@/lib/types'
import type { DecisionRoomData } from '@/src/features/applications/types/advanced-risk.types'
import { decisionsApi, type ApiError } from '@/lib/api-client'

const policyStyles: Record<string, string> = {
  PASS: 'text-risk-low',
  FAIL: 'text-risk-high',
  BLOCK: 'text-risk-high',
  MANUAL_REVIEW: 'text-review',
}

const statusCopy: Record<DecisionRoomData['decisionStatus'], string> = {
  pending: 'Pending decision',
  in_review: 'In manual review',
  decided: 'Decision recorded',
}

/**
 * The single decision system for an application. Rendered in the sticky
 * right column and reused by the Decision Room. Do not create a second one.
 */
export const DecisionPanel = forwardRef<HTMLDivElement, {
  application: Application
  room: DecisionRoomData
  className?: string
}>(function DecisionPanel({ application, room, className }, ref) {
  const [decision, setDecision] = useState<DecisionType | null>(null)
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const overridesRecommendation =
    decision !== null && decision !== application.recommendedAction

  async function submitDecision() {
    if (!decision) {
      toast.error('Select a decision before submitting.')
      return
    }
    if (reason.trim().length < 10) {
      toast.error('Please provide a decision rationale (min 10 characters).')
      return
    }
    if (overridesRecommendation && !reason.toLowerCase().includes('override')) {
      // Soft nudge — override still allowed, but flagged in the audit trail.
      toast.warning('This decision overrides the model recommendation and will be flagged.')
    }
    const decisionMap: Record<DecisionType, string> = {
      APPROVE: 'approved',
      REJECT: 'rejected',
      MANUAL_REVIEW: 'manual_review',
      REQUEST_INFORMATION: 'information_requested',
      WITHDRAW: 'manual_review',
    }
    setSubmitting(true)
    try {
      await decisionsApi.create({
        application_id: application.id,
        decision: decisionMap[decision],
        reason,
        override_reason: overridesRecommendation ? reason : undefined,
      })
      toast.success(`Decision recorded: ${decision.replace(/_/g, ' ').toLowerCase()}`, {
        description: 'The decision and rationale were written to the audit trail.',
      })
      setReason('')
      setDecision(null)
    } catch (caught) {
      toast.error((caught as ApiError).detail || 'Decision could not be recorded')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Card ref={ref} className={cn(className)}>
      <CardHeader>
        <CardTitle>Decision</CardTitle>
        <CardDescription>
          Recommended:{' '}
          <span className="font-medium capitalize text-foreground">
            {application.recommendedAction.replace(/_/g, ' ').toLowerCase()}
          </span>
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Decision context — plan 4.4 */}
        <dl className="grid grid-cols-2 gap-x-4 gap-y-3 rounded-lg border border-border bg-muted/30 p-3 text-xs">
          <div className="space-y-0.5">
            <dt className="text-muted-foreground">Policy result</dt>
            <dd className={cn('font-semibold', policyStyles[room.policyOutcome])}>
              {room.policyOutcome.replace(/_/g, ' ')}
            </dd>
          </div>
          <div className="space-y-0.5">
            <dt className="text-muted-foreground">Active warnings</dt>
            <dd
              className={cn(
                'font-semibold',
                room.activeWarningCount > 0 ? 'text-risk-medium' : 'text-risk-low',
              )}
            >
              {room.activeWarningCount}
            </dd>
          </div>
          <div className="space-y-0.5">
            <dt className="text-muted-foreground">Review reasons</dt>
            <dd className="font-semibold text-foreground">{room.manualReviewReasons.length}</dd>
          </div>
          <div className="space-y-0.5">
            <dt className="text-muted-foreground">Status</dt>
            <dd className="font-semibold text-foreground">{statusCopy[room.decisionStatus]}</dd>
          </div>
        </dl>

        <div className="grid grid-cols-1 gap-2">
          <DecisionButton
            active={decision === 'APPROVE'}
            onClick={() => setDecision('APPROVE')}
            icon={CheckCircle2}
            label="Approve"
            tone="low"
          />
          <DecisionButton
            active={decision === 'MANUAL_REVIEW'}
            onClick={() => setDecision('MANUAL_REVIEW')}
            icon={ShieldCheck}
            label="Send to manual review"
            tone="review"
          />
          <DecisionButton
            active={decision === 'REQUEST_INFORMATION'}
            onClick={() => setDecision('REQUEST_INFORMATION')}
            icon={FileText}
            label="Request information"
            tone="info"
          />
          <DecisionButton
            active={decision === 'REJECT'}
            onClick={() => setDecision('REJECT')}
            icon={XCircle}
            label="Reject"
            tone="high"
          />
        </div>

        {overridesRecommendation ? (
          <div className="flex items-start gap-2 rounded-lg border border-review/30 bg-review/10 p-3 text-xs text-review">
            <MinusCircle className="mt-0.5 size-4 shrink-0" aria-hidden />
            <span>
              This decision overrides the model recommendation. A rationale is required and will be
              flagged in the audit trail.
            </span>
          </div>
        ) : null}

        <Separator />

        <div className="space-y-2">
          <Label htmlFor="decision-reason">Decision rationale</Label>
          <Textarea
            id="decision-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Document the reasoning for this decision. This is stored for audit and regulatory review."
            rows={4}
          />
        </div>

        <Button className="w-full" onClick={submitDecision} disabled={submitting}>
          {submitting ? 'Submitting...' : 'Submit decision'}
        </Button>
        <p className="text-center text-xs text-muted-foreground">
          Analyst: {application.assignedAnalyst}
        </p>
      </CardContent>
    </Card>
  )
})

const toneStyles: Record<string, string> = {
  low: 'data-[active=true]:border-risk-low data-[active=true]:bg-risk-low/10 data-[active=true]:text-risk-low',
  high: 'data-[active=true]:border-risk-high data-[active=true]:bg-risk-high/10 data-[active=true]:text-risk-high',
  review: 'data-[active=true]:border-review data-[active=true]:bg-review/10 data-[active=true]:text-review',
  info: 'data-[active=true]:border-info data-[active=true]:bg-info/10 data-[active=true]:text-info',
}

function DecisionButton({
  active,
  onClick,
  icon: Icon,
  label,
  tone,
}: {
  active: boolean
  onClick: () => void
  icon: React.ElementType
  label: string
  tone: string
}) {
  return (
    <button
      type="button"
      data-active={active}
      onClick={onClick}
      className={cn(
        'flex items-center gap-2 rounded-lg border border-border px-4 py-2.5 text-left text-sm font-medium text-foreground transition-colors hover:bg-secondary',
        toneStyles[tone],
      )}
    >
      <Icon className="size-4" aria-hidden />
      {label}
    </button>
  )
}
