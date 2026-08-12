import type { Application, AuditEvent, Borrower } from './types'

export const ANALYSTS = [
  'Aisyah Rahman',
  'Daniel Tan',
  'Priya Nair',
  'Farid Osman',
  'Mei Ling Chong',
]

export const MODEL_VERSION = 'lightgbm_credit_risk 1.2.0'

function baseFactors() {
  return [
    {
      feature: 'income_volatility',
      label: 'Income volatility',
      direction: 'increases_risk' as const,
      impact: 0.091,
      borrowerValue: '0.42',
      expectedRange: '0.10 – 0.30',
      explanation: 'High month-to-month income variation increased assessed risk.',
    },
    {
      feature: 'utility_payment_timeliness',
      label: 'Utility payment timeliness',
      direction: 'reduces_risk' as const,
      impact: -0.063,
      borrowerValue: '96%',
      expectedRange: '80% – 100%',
      explanation: 'Consistent, on-time utility payments reduced assessed risk.',
    },
    {
      feature: 'liquidity_buffer',
      label: 'Liquidity buffer',
      direction: 'increases_risk' as const,
      impact: 0.048,
      borrowerValue: '4 days',
      expectedRange: '14 – 45 days',
      explanation: 'A low liquidity buffer increased assessed risk.',
    },
    {
      feature: 'net_monthly_cash_flow',
      label: 'Net monthly cash flow',
      direction: 'reduces_risk' as const,
      impact: -0.052,
      borrowerValue: 'RM 1,240',
      expectedRange: 'RM 500 – RM 3,000',
      explanation: 'Positive net cash flow reduced assessed risk.',
    },
    {
      feature: 'income_sources',
      label: 'Number of income sources',
      direction: 'reduces_risk' as const,
      impact: -0.031,
      borrowerValue: '3',
      expectedRange: '1 – 4',
      explanation: 'Diversified income sources reduced assessed risk.',
    },
    {
      feature: 'negative_balance_frequency',
      label: 'Negative-balance frequency',
      direction: 'increases_risk' as const,
      impact: 0.027,
      borrowerValue: '2 / month',
      expectedRange: '0 – 1 / month',
      explanation: 'Frequent negative balances increased assessed risk.',
    },
  ]
}

function basePolicy() {
  return [
    {
      ruleId: 'R-001',
      name: 'Consent completeness',
      version: '1.0',
      result: 'PASS' as const,
      detail: 'All required consents are present and unexpired.',
    },
    {
      ruleId: 'R-002',
      name: 'Fraud flag check',
      version: '1.1',
      result: 'PASS' as const,
      detail: 'No fraud indicators detected.',
    },
    {
      ruleId: 'R-003',
      name: 'Data quality threshold',
      version: '1.0',
      result: 'MANUAL_REVIEW' as const,
      detail: 'Data quality score below 0.60 threshold for automated approval.',
    },
    {
      ruleId: 'R-004',
      name: 'Requested amount limit',
      version: '1.0',
      result: 'PASS' as const,
      detail: 'Requested amount within configured limit.',
    },
    {
      ruleId: 'R-005',
      name: 'Risk band gate',
      version: '1.2',
      result: 'MANUAL_REVIEW' as const,
      detail: 'Medium risk band requires analyst review.',
    },
  ]
}

function dataSources(prefix: string) {
  return [
    {
      id: `${prefix}-ds1`,
      type: 'BANK_STATEMENT' as const,
      status: 'VALIDATED' as const,
      fileName: 'maybank_statement_q1.pdf',
      coverageStart: '2025-01-01',
      coverageEnd: '2025-03-31',
      records: 412,
      qualityScore: 0.82,
    },
    {
      id: `${prefix}-ds2`,
      type: 'EWALLET' as const,
      status: 'VALIDATED' as const,
      fileName: 'touchngo_export.csv',
      coverageStart: '2025-01-01',
      coverageEnd: '2025-03-31',
      records: 208,
      qualityScore: 0.74,
    },
    {
      id: `${prefix}-ds3`,
      type: 'UTILITY' as const,
      status: 'NEEDS_ATTENTION' as const,
      fileName: 'tnb_bills.pdf',
      coverageStart: '2024-10-01',
      coverageEnd: '2025-03-31',
      records: 6,
      qualityScore: 0.55,
    },
  ]
}

function consents(prefix: string) {
  return [
    {
      id: `${prefix}-c1`,
      scope: 'Bank statement analysis',
      sourceType: 'BANK_STATEMENT' as const,
      version: 'v2.1',
      grantedAt: '2025-03-02T09:12:00Z',
      expiresAt: '2025-09-02T09:12:00Z',
      revokedAt: null,
      status: 'GRANTED' as const,
    },
    {
      id: `${prefix}-c2`,
      scope: 'E-wallet transaction analysis',
      sourceType: 'EWALLET' as const,
      version: 'v2.1',
      grantedAt: '2025-03-02T09:13:00Z',
      expiresAt: '2025-09-02T09:13:00Z',
      revokedAt: null,
      status: 'GRANTED' as const,
    },
    {
      id: `${prefix}-c3`,
      scope: 'Automated risk analysis disclosure',
      sourceType: 'MANUAL' as const,
      version: 'v2.1',
      grantedAt: '2025-03-02T09:14:00Z',
      expiresAt: null,
      revokedAt: null,
      status: 'GRANTED' as const,
    },
  ]
}

function audit(prefix: string): AuditEvent[] {
  return [
    {
      id: `${prefix}-a1`,
      timestamp: '2025-03-02T09:10:00Z',
      user: 'borrower',
      action: 'CONSENT_GRANTED',
      entityType: 'Consent',
      entityId: `${prefix}-c1`,
      ip: '175.144.2.10',
      result: 'SUCCESS',
    },
    {
      id: `${prefix}-a2`,
      timestamp: '2025-03-02T10:02:00Z',
      user: 'Daniel Tan',
      action: 'DATA_SOURCE_VALIDATED',
      entityType: 'DataSource',
      entityId: `${prefix}-ds1`,
      ip: '10.0.4.22',
      result: 'SUCCESS',
    },
    {
      id: `${prefix}-a3`,
      timestamp: '2025-03-02T10:20:00Z',
      user: 'system',
      action: 'SCORE_GENERATED',
      entityType: 'Prediction',
      entityId: `${prefix}-pred`,
      ip: '10.0.4.9',
      result: 'SUCCESS',
    },
    {
      id: `${prefix}-a4`,
      timestamp: '2025-03-02T11:05:00Z',
      user: 'Aisyah Rahman',
      action: 'SENT_TO_MANUAL_REVIEW',
      entityType: 'Application',
      entityId: prefix,
      ip: '10.0.4.31',
      result: 'SUCCESS',
    },
  ]
}

const RAW: Array<Partial<Application> & { id: string }> = [
  {
    id: 'APP-2041',
    borrowerName: 'Nurul Izzah',
    borrowerType: 'GIG_WORKER',
    requestedAmount: 8000,
    purpose: 'Working capital',
    status: 'MANUAL_REVIEW',
    probabilityOfDefault: 0.184,
    confidence: 0.87,
    dataQuality: 0.58,
    incomeMonthly: 3200,
    expenseMonthly: 1960,
  },
  {
    id: 'APP-2042',
    borrowerName: 'Chandran Raj',
    borrowerType: 'SMALL_MERCHANT',
    requestedAmount: 15000,
    purpose: 'Inventory purchase',
    status: 'SCORED',
    probabilityOfDefault: 0.092,
    confidence: 0.91,
    dataQuality: 0.86,
    incomeMonthly: 7400,
    expenseMonthly: 4100,
  },
  {
    id: 'APP-2043',
    borrowerName: 'Siti Aminah',
    borrowerType: 'MICRO_ENTREPRENEUR',
    requestedAmount: 5000,
    purpose: 'Equipment',
    status: 'APPROVED',
    probabilityOfDefault: 0.071,
    confidence: 0.93,
    dataQuality: 0.9,
    incomeMonthly: 4200,
    expenseMonthly: 2300,
  },
  {
    id: 'APP-2044',
    borrowerName: 'Ahmad Faizal',
    borrowerType: 'THIN_FILE',
    requestedAmount: 12000,
    purpose: 'Vehicle for delivery',
    status: 'REJECTED',
    probabilityOfDefault: 0.412,
    confidence: 0.79,
    dataQuality: 0.63,
    incomeMonthly: 2600,
    expenseMonthly: 2450,
  },
  {
    id: 'APP-2045',
    borrowerName: 'Grace Wong',
    borrowerType: 'GIG_WORKER',
    requestedAmount: 6500,
    purpose: 'Emergency expense',
    status: 'INFORMATION_REQUESTED',
    probabilityOfDefault: 0.243,
    confidence: 0.72,
    dataQuality: 0.49,
    incomeMonthly: 2900,
    expenseMonthly: 2100,
  },
  {
    id: 'APP-2046',
    borrowerName: 'Ravi Kumar',
    borrowerType: 'SMALL_MERCHANT',
    requestedAmount: 22000,
    purpose: 'Shop renovation',
    status: 'SUBMITTED',
    probabilityOfDefault: 0.131,
    confidence: 0.84,
    dataQuality: 0.77,
    incomeMonthly: 9100,
    expenseMonthly: 5200,
  },
  {
    id: 'APP-2047',
    borrowerName: 'Farah Diana',
    borrowerType: 'MICRO_ENTREPRENEUR',
    requestedAmount: 4000,
    purpose: 'Raw materials',
    status: 'READY_FOR_SCORING',
    probabilityOfDefault: 0.108,
    confidence: 0.88,
    dataQuality: 0.81,
    incomeMonthly: 3800,
    expenseMonthly: 2000,
  },
  {
    id: 'APP-2048',
    borrowerName: 'Tan Wei Sheng',
    borrowerType: 'SALARIED',
    requestedAmount: 18000,
    purpose: 'Debt consolidation',
    status: 'SCORED',
    probabilityOfDefault: 0.334,
    confidence: 0.81,
    dataQuality: 0.7,
    incomeMonthly: 5600,
    expenseMonthly: 4900,
  },
]

export const APPLICATIONS: Application[] = RAW.map((r, i) => {
  const pd = r.probabilityOfDefault as number
  const riskBand = pd < 0.15 ? 'LOW' : pd < 0.3 ? 'MEDIUM' : 'HIGH'
  const recommended =
    riskBand === 'LOW'
      ? 'APPROVE'
      : riskBand === 'HIGH'
        ? 'REJECT'
        : 'MANUAL_REVIEW'
  return {
    reference: `REF-${2025000 + i}`,
    purpose: r.purpose ?? 'Working capital',
    riskBand,
    assignedAnalyst: ANALYSTS[i % ANALYSTS.length],
    submittedAt: `2025-03-0${(i % 8) + 1}T08:30:00Z`,
    lastUpdated: `2025-03-0${(i % 8) + 2}T14:15:00Z`,
    modelVersion: MODEL_VERSION,
    recommendedAction: recommended,
    factors: baseFactors(),
    policyResults: basePolicy(),
    dataSources: dataSources(r.id),
    consents: consents(r.id),
    decisions: [],
    audit: audit(r.id),
    netCashFlow: (r.incomeMonthly ?? 0) - (r.expenseMonthly ?? 0),
    ...r,
  } as Application
})

export function getApplication(id: string): Application | undefined {
  return APPLICATIONS.find((a) => a.id === id)
}

export const BORROWERS: Borrower[] = [
  {
    id: 'BRW-101',
    name: 'Nurul Izzah',
    segment: 'GIG_WORKER',
    applications: 2,
    latestRiskBand: 'MEDIUM',
    activeApplication: 'APP-2041',
    lastUpdated: '2025-03-03T14:15:00Z',
    email: 'nurul.izzah@example.com',
    occupation: 'Ride-hailing driver',
  },
  {
    id: 'BRW-102',
    name: 'Chandran Raj',
    segment: 'SMALL_MERCHANT',
    applications: 1,
    latestRiskBand: 'LOW',
    activeApplication: 'APP-2042',
    lastUpdated: '2025-03-03T11:05:00Z',
    email: 'chandran.raj@example.com',
    occupation: 'Grocery store owner',
  },
  {
    id: 'BRW-103',
    name: 'Siti Aminah',
    segment: 'MICRO_ENTREPRENEUR',
    applications: 3,
    latestRiskBand: 'LOW',
    activeApplication: null,
    lastUpdated: '2025-02-28T09:40:00Z',
    email: 'siti.aminah@example.com',
    occupation: 'Home baker',
  },
  {
    id: 'BRW-104',
    name: 'Ahmad Faizal',
    segment: 'THIN_FILE',
    applications: 1,
    latestRiskBand: 'HIGH',
    activeApplication: 'APP-2044',
    lastUpdated: '2025-03-01T16:20:00Z',
    email: 'ahmad.faizal@example.com',
    occupation: 'Delivery rider',
  },
  {
    id: 'BRW-105',
    name: 'Grace Wong',
    segment: 'GIG_WORKER',
    applications: 2,
    latestRiskBand: 'MEDIUM',
    activeApplication: 'APP-2045',
    lastUpdated: '2025-03-02T10:00:00Z',
    email: 'grace.wong@example.com',
    occupation: 'Freelance designer',
  },
  {
    id: 'BRW-106',
    name: 'Ravi Kumar',
    segment: 'SMALL_MERCHANT',
    applications: 1,
    latestRiskBand: 'MEDIUM',
    activeApplication: 'APP-2046',
    lastUpdated: '2025-03-02T13:30:00Z',
    email: 'ravi.kumar@example.com',
    occupation: 'Hardware shop owner',
  },
]

export const GLOBAL_AUDIT: AuditEvent[] = APPLICATIONS.flatMap((a) => a.audit)

// Time-series helpers for charts
export const APPLICATIONS_OVER_TIME = [
  { month: 'Oct', applications: 42, approved: 24 },
  { month: 'Nov', applications: 51, approved: 30 },
  { month: 'Dec', applications: 47, approved: 26 },
  { month: 'Jan', applications: 63, approved: 38 },
  { month: 'Feb', applications: 72, approved: 41 },
  { month: 'Mar', applications: 58, approved: 33 },
]

export const RISK_BAND_DISTRIBUTION = [
  { band: 'Low', count: 128, fill: 'var(--color-risk-low)' },
  { band: 'Medium', count: 74, fill: 'var(--color-risk-medium)' },
  { band: 'High', count: 39, fill: 'var(--color-risk-high)' },
]

export const PD_DISTRIBUTION = [
  { bucket: '0-0.1', count: 62 },
  { bucket: '0.1-0.2', count: 88 },
  { bucket: '0.2-0.3', count: 54 },
  { bucket: '0.3-0.4', count: 27 },
  { bucket: '0.4-0.5', count: 12 },
  { bucket: '0.5+', count: 7 },
]

export const SEGMENT_DISTRIBUTION = [
  { segment: 'Gig Worker', count: 96 },
  { segment: 'Micro-Entrepreneur', count: 71 },
  { segment: 'Small Merchant', count: 54 },
  { segment: 'Thin-File', count: 38 },
  { segment: 'Salaried', count: 22 },
]

export const CASHFLOW_TREND = [
  { month: 'Oct', inflow: 3100, outflow: 2400 },
  { month: 'Nov', inflow: 2900, outflow: 2600 },
  { month: 'Dec', inflow: 3400, outflow: 2200 },
  { month: 'Jan', inflow: 2700, outflow: 2500 },
  { month: 'Feb', inflow: 3600, outflow: 2100 },
  { month: 'Mar', inflow: 3200, outflow: 1960 },
]

export const FEATURE_DRIFT = [
  { feature: 'income_volatility', psi: 0.08 },
  { feature: 'liquidity_buffer', psi: 0.21 },
  { feature: 'net_cash_flow', psi: 0.05 },
  { feature: 'utility_timeliness', psi: 0.12 },
  { feature: 'negative_balance_freq', psi: 0.27 },
]

export const CALIBRATION_CURVE = [
  { predicted: 0.05, observed: 0.04 },
  { predicted: 0.15, observed: 0.17 },
  { predicted: 0.25, observed: 0.23 },
  { predicted: 0.35, observed: 0.38 },
  { predicted: 0.45, observed: 0.42 },
  { predicted: 0.55, observed: 0.57 },
]

export const PERFORMANCE_OVER_TIME = [
  { month: 'Oct', auc: 0.82 },
  { month: 'Nov', auc: 0.83 },
  { month: 'Dec', auc: 0.81 },
  { month: 'Jan', auc: 0.8 },
  { month: 'Feb', auc: 0.79 },
  { month: 'Mar', auc: 0.78 },
]

export const FAIRNESS_BY_SEGMENT = [
  {
    segment: 'Gig Worker',
    approvalRate: 0.58,
    fpr: 0.11,
    fnr: 0.14,
    sample: 96,
  },
  {
    segment: 'Micro-Entrepreneur',
    approvalRate: 0.64,
    fpr: 0.09,
    fnr: 0.12,
    sample: 71,
  },
  {
    segment: 'Small Merchant',
    approvalRate: 0.69,
    fpr: 0.08,
    fnr: 0.1,
    sample: 54,
  },
  {
    segment: 'Thin-File',
    approvalRate: 0.47,
    fpr: 0.15,
    fnr: 0.18,
    sample: 38,
  },
]

export const API_KEYS = [
  {
    id: 'key_1',
    name: 'Production Scoring',
    created: '2025-01-12T00:00:00Z',
    lastUsed: '2025-03-03T09:12:00Z',
    status: 'ACTIVE',
    permissions: 'scoring:read, scoring:write',
  },
  {
    id: 'key_2',
    name: 'Analytics Read-Only',
    created: '2025-02-01T00:00:00Z',
    lastUsed: '2025-03-02T18:40:00Z',
    status: 'ACTIVE',
    permissions: 'monitoring:read',
  },
  {
    id: 'key_3',
    name: 'Legacy Integration',
    created: '2024-11-20T00:00:00Z',
    lastUsed: '2025-01-05T12:00:00Z',
    status: 'REVOKED',
    permissions: 'applications:read',
  },
]
