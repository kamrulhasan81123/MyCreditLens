import type { RiskBand } from '@/lib/types'

const bandColor: Record<RiskBand, string> = {
  LOW: 'var(--color-risk-low)',
  MEDIUM: 'var(--color-risk-medium)',
  HIGH: 'var(--color-risk-high)',
}

export function ProbabilityGauge({
  value,
  band,
  size = 200,
}: {
  value: number
  band: RiskBand
  size?: number
}) {
  const radius = size / 2 - 16
  const circumference = Math.PI * radius
  const dash = circumference * value
  const color = bandColor[band]

  return (
    <div
      className="relative"
      style={{ width: size, height: size / 2 + 24 }}
      role="img"
      aria-label={`Probability of default ${(value * 100).toFixed(1)} percent, ${band} risk band`}
    >
      <svg width={size} height={size / 2 + 24} viewBox={`0 0 ${size} ${size / 2 + 24}`}>
        <path
          d={`M 16 ${size / 2} A ${radius} ${radius} 0 0 1 ${size - 16} ${size / 2}`}
          fill="none"
          stroke="var(--color-muted)"
          strokeWidth={14}
          strokeLinecap="round"
        />
        <path
          d={`M 16 ${size / 2} A ${radius} ${radius} 0 0 1 ${size - 16} ${size / 2}`}
          fill="none"
          stroke={color}
          strokeWidth={14}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference}`}
        />
      </svg>
      <div className="absolute inset-x-0 bottom-0 flex flex-col items-center">
        <span className="text-3xl font-semibold tabular-nums text-foreground">
          {(value * 100).toFixed(1)}%
        </span>
        <span className="text-xs text-muted-foreground">
          Probability of default
        </span>
      </div>
    </div>
  )
}
