'use client'

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const axisProps = {
  stroke: 'var(--color-muted-foreground)',
  fontSize: 12,
  tickLine: false,
  axisLine: false,
}

const gridProps = {
  strokeDasharray: '3 3',
  stroke: 'var(--color-border)',
  vertical: false,
}

const tooltipStyle = {
  contentStyle: {
    borderRadius: 8,
    border: '1px solid var(--color-border)',
    background: 'var(--color-card)',
    fontSize: 12,
    color: 'var(--color-foreground)',
  },
  labelStyle: { color: 'var(--color-muted-foreground)', marginBottom: 4 },
}

export function ApplicationsAreaChart({
  data,
}: {
  data: { month: string; applications: number; approved: number }[]
}) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ left: -18, right: 8, top: 8 }}>
        <defs>
          <linearGradient id="apps" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--color-chart-1)" stopOpacity={0.3} />
            <stop offset="95%" stopColor="var(--color-chart-1)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey="month" {...axisProps} />
        <YAxis {...axisProps} />
        <Tooltip {...tooltipStyle} />
        <Area
          type="monotone"
          dataKey="applications"
          stroke="var(--color-chart-1)"
          strokeWidth={2}
          fill="url(#apps)"
          name="Applications"
        />
        <Area
          type="monotone"
          dataKey="approved"
          stroke="var(--color-risk-low)"
          strokeWidth={2}
          fill="transparent"
          name="Approved"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export function CategoricalBarChart({
  data,
  dataKey,
  categoryKey,
  height = 260,
  color = 'var(--color-chart-1)',
  useCellFill = false,
}: {
  data: Record<string, unknown>[]
  dataKey: string
  categoryKey: string
  height?: number
  color?: string
  useCellFill?: boolean
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ left: -18, right: 8, top: 8 }}>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey={categoryKey} {...axisProps} interval={0} />
        <YAxis {...axisProps} />
        <Tooltip {...tooltipStyle} cursor={{ fill: 'var(--color-muted)' }} />
        <Bar dataKey={dataKey} radius={[6, 6, 0, 0]} fill={color}>
          {useCellFill &&
            data.map((entry, i) => (
              <Cell key={i} fill={(entry.fill as string) ?? color} />
            ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function SimpleLineChart({
  data,
  dataKey,
  categoryKey,
  height = 260,
  color = 'var(--color-chart-1)',
  domain,
}: {
  data: Record<string, unknown>[]
  dataKey: string
  categoryKey: string
  height?: number
  color?: string
  domain?: [number, number]
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ left: -18, right: 8, top: 8 }}>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey={categoryKey} {...axisProps} />
        <YAxis {...axisProps} domain={domain} />
        <Tooltip {...tooltipStyle} />
        <Line
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          strokeWidth={2}
          dot={{ r: 3 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function CashflowChart({
  data,
}: {
  data: { month: string; inflow: number; outflow: number }[]
}) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ left: -8, right: 8, top: 8 }}>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey="month" {...axisProps} />
        <YAxis {...axisProps} />
        <Tooltip {...tooltipStyle} cursor={{ fill: 'var(--color-muted)' }} />
        <Bar dataKey="inflow" name="Inflow" radius={[4, 4, 0, 0]} fill="var(--color-risk-low)" />
        <Bar dataKey="outflow" name="Outflow" radius={[4, 4, 0, 0]} fill="var(--color-chart-5)" />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function CalibrationChart({
  data,
}: {
  data: { predicted: number; observed: number }[]
}) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ left: -12, right: 8, top: 8 }}>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey="predicted" {...axisProps} />
        <YAxis {...axisProps} />
        <Tooltip {...tooltipStyle} />
        <ReferenceLine
          segment={[
            { x: 0.05, y: 0.05 },
            { x: 0.55, y: 0.55 },
          ]}
          stroke="var(--color-muted-foreground)"
          strokeDasharray="4 4"
        />
        <Line
          type="monotone"
          dataKey="observed"
          stroke="var(--color-chart-1)"
          strokeWidth={2}
          dot={{ r: 3 }}
          name="Observed"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
