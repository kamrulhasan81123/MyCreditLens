export type RiskBand = 'LOW' | 'MEDIUM' | 'HIGH'

export type ApplicationStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'DATA_PENDING'
  | 'VALIDATION_FAILED'
  | 'READY_FOR_SCORING'
  | 'SCORING'
  | 'SCORED'
  | 'MANUAL_REVIEW'
  | 'INFORMATION_REQUESTED'
  | 'APPROVED'
  | 'REJECTED'
  | 'APPEALED'
  | 'WITHDRAWN'
  | 'ARCHIVED'

export type BorrowerSegment =
  | 'GIG_WORKER'
  | 'MICRO_ENTREPRENEUR'
  | 'SMALL_MERCHANT'
  | 'THIN_FILE'
  | 'SALARIED'

export type DataSourceType =
  | 'BANK_STATEMENT'
  | 'EWALLET'
  | 'UTILITY'
  | 'GIG_INCOME'
  | 'POS'
  | 'REMITTANCE'
  | 'MANUAL'

export type DataSourceStatus =
  | 'CONNECTED'
  | 'PENDING'
  | 'FAILED'
  | 'EXPIRED'
  | 'NEEDS_ATTENTION'
  | 'VALIDATED'

export type DecisionType =
  | 'APPROVE'
  | 'REJECT'
  | 'MANUAL_REVIEW'
  | 'REQUEST_INFORMATION'
  | 'WITHDRAW'

export interface Factor {
  feature: string
  label: string
  direction: 'increases_risk' | 'reduces_risk'
  impact: number
  borrowerValue: string
  expectedRange: string
  explanation: string
}

export interface PolicyResult {
  ruleId: string
  name: string
  version: string
  result: 'PASS' | 'FAIL' | 'MANUAL_REVIEW' | 'BLOCK'
  detail: string
}

export interface DataSource {
  id: string
  type: DataSourceType
  status: DataSourceStatus
  fileName: string
  coverageStart: string
  coverageEnd: string
  records: number
  qualityScore: number
}

export interface Consent {
  id: string
  scope: string
  sourceType: DataSourceType
  version: string
  grantedAt: string | null
  expiresAt: string | null
  revokedAt: string | null
  status: 'GRANTED' | 'PENDING' | 'REVOKED' | 'EXPIRED'
}

export interface AuditEvent {
  id: string
  timestamp: string
  user: string
  action: string
  entityType: string
  entityId: string
  ip: string
  result: 'SUCCESS' | 'FAILURE'
}

export interface Decision {
  id: string
  decision: DecisionType
  reason: string
  analyst: string
  override: boolean
  overrideReason?: string
  createdAt: string
}

export interface Application {
  id: string
  reference: string
  borrowerName: string
  borrowerType: BorrowerSegment
  requestedAmount: number
  purpose: string
  status: ApplicationStatus
  probabilityOfDefault: number
  riskBand: RiskBand
  confidence: number
  dataQuality: number
  assignedAnalyst: string
  submittedAt: string
  lastUpdated: string
  modelVersion: string
  recommendedAction: DecisionType
  factors: Factor[]
  policyResults: PolicyResult[]
  dataSources: DataSource[]
  consents: Consent[]
  decisions: Decision[]
  audit: AuditEvent[]
  incomeMonthly: number
  expenseMonthly: number
  netCashFlow: number
}

export interface Borrower {
  id: string
  name: string
  segment: BorrowerSegment
  applications: number
  latestRiskBand: RiskBand
  activeApplication: string | null
  lastUpdated: string
  email: string
  occupation: string
}
