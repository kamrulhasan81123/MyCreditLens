'use client'

import type { Factor } from '@/lib/types'
import { cn } from '@/lib/utils'

export function ShapWaterfall({ factors }: { factors: Factor[] }) {
  const sorted = [...factors].sort(
    (a, b) => Math.abs(b.impact) - Math.abs(a.impact),
  )
  const max = Math.max(...sorted.map((f) => Math.abs(f.impact)), 0.01)

  return (
    <div className="flex flex-col gap-3" aria-label="SHAP feature contributions">
      {sorted.map((f) => {
        const increases = f.direction === 'increases_risk'
        const width = (Math.abs(f.impact) / max) * 100
        return (
          <div key={f.feature} className="grid grid-cols-[1fr_auto] items-center gap-3">
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-foreground">
                  {f.label}
                </span>
                <span
                  className={cn(
                    'font-mono text-xs tabular-nums',
                    increases ? 'text-risk-high' : 'text-risk-low',
                  )}
                >
                  {increases ? '+' : ''}
                  {f.impact.toFixed(3)}
                </span>
              </div>
              <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className={cn(
                    'absolute inset-y-0 rounded-full',
                    increases ? 'left-1/2 bg-risk-high' : 'right-1/2 bg-risk-low',
                  )}
                  style={{ width: `${width / 2}%` }}
                />
                <div className="absolute inset-y-0 left-1/2 w-px bg-border" />
              </div>
            </div>
          </div>
        )
      })}
      <div className="flex items-center justify-between pt-1 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <span className="size-2.5 rounded-full bg-risk-low" /> Reduces risk
        </span>
        <span className="inline-flex items-center gap-1.5">
          Increases risk <span className="size-2.5 rounded-full bg-risk-high" />
        </span>
      </div>
    </div>
  )
}
