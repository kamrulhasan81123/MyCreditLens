'use client'

import { useState } from 'react'
import {
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Info,
  MessageCircleQuestion,
  ThumbsUp,
  XCircle,
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
import { formatDate } from '@/lib/format'
import { toast } from 'sonner'
import type {
  BorrowerAppealStatus,
  BorrowerDecision,
} from '@/src/features/applications/types/advanced-risk.types'

const statusMeta: Record<
  BorrowerDecision['status'],
  { label: string; icon: React.ComponentType<{ className?: string }>; badge: string; accent: string }
> = {
  approved: {
    label: 'Approved',
    icon: CheckCircle2,
    badge: 'bg-risk-low/10 text-risk-low',
    accent: 'border-risk-low/30 bg-risk-low/5',
  },
  declined: {
    label: 'Not approved',
    icon: XCircle,
    badge: 'bg-risk-high/10 text-risk-high',
    accent: 'border-risk-high/30 bg-risk-high/5',
  },
  more_info: {
    label: 'More information needed',
    icon: Info,
    badge: 'bg-risk-medium/10 text-risk-medium',
    accent: 'border-risk-medium/30 bg-risk-medium/5',
  },
  in_review: {
    label: 'Under review',
    icon: ClipboardList,
    badge: 'bg-action/10 text-action',
    accent: 'border-action/30 bg-action/5',
  },
}

const appealStatusCopy: Record<BorrowerAppealStatus, string> = {
  none: '',
  submitted: 'Your request for a review has been submitted.',
  under_review: 'Your review request is being looked at by our team.',
  info_required: 'We need a little more information to complete your review.',
  completed: 'Your review has been completed.',
}

export function BorrowerDecisionExplanation({ decision }: { decision: BorrowerDecision }) {
  const meta = statusMeta[decision.status]
  const StatusIcon = meta.icon
  const [appealOpen, setAppealOpen] = useState(false)
  const [appealStatus, setAppealStatus] = useState<BorrowerAppealStatus>(decision.appealStatus)
  const [note, setNote] = useState('')

  const canAppeal =
    (decision.status === 'declined' || decision.status === 'more_info') &&
    appealStatus === 'none'

  function submitAppeal() {
    if (note.trim().length < 15) return
    setAppealStatus('submitted')
    setAppealOpen(false)
    setNote('')
    toast.success('Review request submitted', {
      description: 'We will get back to you within 3 business days.',
    })
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Your application outcome</CardTitle>
          <Badge className={cn('gap-1', meta.badge)}>
            <StatusIcon className="size-3.5" />
            {meta.label}
          </Badge>
        </div>
        <CardDescription>Decision recorded {formatDate(decision.decisionDate)}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className={cn('rounded-lg border p-4', meta.accent)}>
          <p className="text-sm leading-relaxed text-foreground">{decision.plainLanguage}</p>
          <p className="mt-2 text-sm text-muted-foreground">{decision.meaning}</p>
        </div>

        <div>
          <h3 className="mb-2 text-sm font-semibold text-foreground">
            What we looked at
          </h3>
          <ul className="space-y-2">
            {decision.factors.map((factor) => (
              <li
                key={factor.label}
                className="flex items-start gap-2 rounded-lg border border-border bg-muted/30 p-3"
              >
                <ThumbsUp className="mt-0.5 size-4 shrink-0 text-action" />
                <div>
                  <p className="text-sm font-medium text-foreground">{factor.label}</p>
                  <p className="text-xs text-muted-foreground">{factor.detail}</p>
                </div>
              </li>
            ))}
          </ul>
          <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
            <Info className="size-3.5" />
            Based on the data sources you connected: {decision.dataSourcesUsed.join(', ')}.
          </p>
        </div>

        {decision.missingInformation.length > 0 && (
          <div className="rounded-lg border border-risk-medium/30 bg-risk-medium/5 p-4">
            <h3 className="text-sm font-semibold text-foreground">
              What could help your application
            </h3>
            <ul className="mt-2 space-y-1.5">
              {decision.missingInformation.map((item) => (
                <li key={item} className="flex items-start gap-2 text-sm text-muted-foreground">
                  <ChevronRight className="mt-0.5 size-4 shrink-0 text-risk-medium" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {appealStatus !== 'none' && (
          <div className="flex items-start gap-2 rounded-lg border border-action/30 bg-action/5 p-3">
            <ClipboardList className="mt-0.5 size-4 shrink-0 text-action" />
            <p className="text-sm text-muted-foreground">{appealStatusCopy[appealStatus]}</p>
          </div>
        )}

        {canAppeal && (
          <div className="flex flex-col gap-2 border-t border-border pt-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              Think something was missed? You can ask us to take another look.
            </p>
            <Button variant="outline" onClick={() => setAppealOpen(true)}>
              <MessageCircleQuestion className="size-4" />
              Request a review
            </Button>
          </div>
        )}
      </CardContent>

      <Dialog open={appealOpen} onOpenChange={setAppealOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Request a review</DialogTitle>
            <DialogDescription>
              Tell us what you&apos;d like us to reconsider. If your circumstances have changed or
              you have extra information, add it here.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="For example: my income has increased since I applied, or I have additional bank statements to share…"
              rows={5}
            />
            <p className="text-xs text-muted-foreground">
              {note.trim().length}/15 characters minimum
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAppealOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submitAppeal} disabled={note.trim().length < 15}>
              Submit request
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
