import {
  AlertTriangle,
  CheckCircle2,
  CircleHelp,
  Clock,
  FileCheck2,
  Info,
  ShieldAlert,
  ShieldCheck,
  XCircle,
} from 'lucide-react'
import type {
  ApplicationStatus,
  DataSourceStatus,
  RiskBand,
} from '@/lib/types'
import { RISK_BAND_LABEL, STATUS_LABEL } from '@/lib/format'
import { cn } from '@/lib/utils'

const riskStyles: Record<RiskBand, string> = {
  LOW: 'bg-risk-low/10 text-risk-low border-risk-low/25',
  MEDIUM: 'bg-risk-medium/10 text-risk-medium border-risk-medium/25',
  HIGH: 'bg-risk-high/10 text-risk-high border-risk-high/25',
}

const riskIcon: Record<RiskBand, React.ElementType> = {
  LOW: ShieldCheck,
  MEDIUM: ShieldAlert,
  HIGH: AlertTriangle,
}

export function RiskBadge({
  band,
  className,
}: {
  band: RiskBand
  className?: string
}) {
  const Icon = riskIcon[band]
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium',
        riskStyles[band],
        className,
      )}
    >
      <Icon className="size-3.5" aria-hidden />
      {RISK_BAND_LABEL[band]}
    </span>
  )
}

const statusStyles: Record<string, string> = {
  APPROVED: 'bg-risk-low/10 text-risk-low border-risk-low/25',
  REJECTED: 'bg-risk-high/10 text-risk-high border-risk-high/25',
  MANUAL_REVIEW: 'bg-review/10 text-review border-review/25',
  INFORMATION_REQUESTED: 'bg-info/10 text-info border-info/25',
  VALIDATION_FAILED: 'bg-risk-high/10 text-risk-high border-risk-high/25',
  SCORED: 'bg-primary/10 text-primary border-primary/25',
  SCORING: 'bg-primary/10 text-primary border-primary/25',
  READY_FOR_SCORING: 'bg-primary/10 text-primary border-primary/25',
  SUBMITTED: 'bg-secondary text-secondary-foreground border-border',
  DATA_PENDING: 'bg-risk-medium/10 text-risk-medium border-risk-medium/25',
  DRAFT: 'bg-muted text-muted-foreground border-border',
  WITHDRAWN: 'bg-muted text-muted-foreground border-border',
  ARCHIVED: 'bg-muted text-muted-foreground border-border',
}

export function StatusBadge({
  status,
  className,
}: {
  status: ApplicationStatus
  className?: string
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium',
        statusStyles[status] ?? 'bg-muted text-muted-foreground border-border',
        className,
      )}
    >
      {STATUS_LABEL[status]}
    </span>
  )
}

export function DataQualityBadge({
  score,
  className,
}: {
  score: number
  className?: string
}) {
  const level =
    score >= 0.8 ? 'good' : score >= 0.6 ? 'fair' : 'poor'
  const styles =
    level === 'good'
      ? 'bg-risk-low/10 text-risk-low border-risk-low/25'
      : level === 'fair'
        ? 'bg-risk-medium/10 text-risk-medium border-risk-medium/25'
        : 'bg-risk-high/10 text-risk-high border-risk-high/25'
  const Icon =
    level === 'good' ? CheckCircle2 : level === 'fair' ? Info : AlertTriangle
  const label =
    level === 'good' ? 'Good' : level === 'fair' ? 'Fair' : 'Poor'
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium',
        styles,
        className,
      )}
    >
      <Icon className="size-3.5" aria-hidden />
      {label} · {(score * 100).toFixed(0)}%
    </span>
  )
}

const sourceStatusMap: Record<
  DataSourceStatus,
  { label: string; styles: string; icon: React.ElementType }
> = {
  CONNECTED: {
    label: 'Connected',
    styles: 'bg-risk-low/10 text-risk-low border-risk-low/25',
    icon: CheckCircle2,
  },
  VALIDATED: {
    label: 'Validated',
    styles: 'bg-risk-low/10 text-risk-low border-risk-low/25',
    icon: FileCheck2,
  },
  PENDING: {
    label: 'Pending',
    styles: 'bg-risk-medium/10 text-risk-medium border-risk-medium/25',
    icon: Clock,
  },
  FAILED: {
    label: 'Failed',
    styles: 'bg-risk-high/10 text-risk-high border-risk-high/25',
    icon: XCircle,
  },
  EXPIRED: {
    label: 'Expired',
    styles: 'bg-muted text-muted-foreground border-border',
    icon: CircleHelp,
  },
  NEEDS_ATTENTION: {
    label: 'Needs attention',
    styles: 'bg-risk-medium/10 text-risk-medium border-risk-medium/25',
    icon: AlertTriangle,
  },
}

export function SourceStatusBadge({
  status,
  className,
}: {
  status: DataSourceStatus
  className?: string
}) {
  const config = sourceStatusMap[status]
  const Icon = config.icon
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium',
        config.styles,
        className,
      )}
    >
      <Icon className="size-3.5" aria-hidden />
      {config.label}
    </span>
  )
}
