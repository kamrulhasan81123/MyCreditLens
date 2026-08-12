import { ArrowDownRight, ArrowUpRight } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface KpiCardProps {
  label: string
  value: string
  icon: React.ElementType
  delta?: { value: string; trend: 'up' | 'down' | 'neutral' }
  trend?: { value: string; direction: 'up' | 'down'; positive?: boolean }
  hint?: string
}

export function KpiCard({ label, value, icon: Icon, delta, trend, hint }: KpiCardProps) {
  const displayTrend =
    trend ??
    (delta && delta.trend !== 'neutral'
      ? {
          value: delta.value,
          direction: delta.trend,
          positive: delta.trend === 'up',
        }
      : undefined)
  const displayHint = hint ?? (delta?.trend === 'neutral' ? delta.value : undefined)

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-1">
          <span className="text-sm text-muted-foreground">{label}</span>
          <span className="text-2xl font-semibold tracking-tight text-foreground">
            {value}
          </span>
        </div>
        <span className="flex size-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
          <Icon className="size-4.5" aria-hidden />
        </span>
      </div>
      {(displayTrend || displayHint) && (
        <div className="mt-3 flex items-center gap-2 text-xs">
          {displayTrend && (
            <span
              className={cn(
                'inline-flex items-center gap-0.5 font-medium',
                displayTrend.positive === false
                  ? 'text-risk-high'
                  : displayTrend.positive
                    ? 'text-risk-low'
                    : 'text-muted-foreground',
              )}
            >
              {displayTrend.direction === 'up' ? (
                <ArrowUpRight className="size-3.5" aria-hidden />
              ) : (
                <ArrowDownRight className="size-3.5" aria-hidden />
              )}
              {displayTrend.value}
            </span>
          )}
          {displayHint && <span className="text-muted-foreground">{displayHint}</span>}
        </div>
      )}
    </Card>
  )
}
