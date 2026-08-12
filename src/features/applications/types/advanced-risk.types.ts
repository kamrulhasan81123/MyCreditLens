// Shared TypeScript interfaces for the advanced risk / Decision Room features.
// These are additive and do not modify the existing lib/types.ts domain model.

export type ReliabilityLabel = 'excellent' | 'good' | 'limited' | 'insufficient'

export type ModelAgreementLevel = 'strong' | 'moderate' | 'weak'

export type ReviewSeverity = 'info' | 'warning' | 'critical'

/** Consolidated risk snapshot shown at the top of the Decision Room. */
export interface RiskOverview {
  probabilityOfDefault: number
  riskBand: 'low' | 'medium' | 'high'
  confidence: number
  recommendedAction: 'approve' | 'reject' | 'manual_review' | 'request_information'
  modelVersion: string
  scoredAt: string
  dataReliabilityScore: number
  modelAgreement: ModelAgreementLevel
}

export interface DataReliabilitySource {
  id: string
  sourceType: string
  score: number
  label: ReliabilityLabel
  coverageStart: string
  coverageEnd: string
  recordCount: number
  missingRate: number
  validationStatus: 'passed' | 'warning' | 'failed'
  mainIssue?: string
}

export interface ModelPredictionComparison {
  modelId: string
  modelName: string
  version: string
  probabilityOfDefault: number
  riskBand: 'low' | 'medium' | 'high'
  confidence: number
  calibrationStatus: 'good' | 'warning' | 'poor'
}

export interface CounterfactualScenario {
  id: string
  title: string
  feature: string
  currentValue: number
  proposedValue: number
  originalProbability: number
  simulatedProbability: number
  feasibility: 'easy' | 'moderate' | 'difficult'
}

export interface IntegrityAlert {
  id: string
  category: 'credit' | 'fraud' | 'data_integrity'
  severity: 'info' | 'warning' | 'critical'
  title: string
  description: string
  detectedAt: string
  hasEvidence: boolean
  dismissed: boolean
  dismissReason?: string
}

export interface ManualReviewReason {
  id: string
  code: string
  title: string
  description: string
  severity: ReviewSeverity
  resolved: boolean
}

/** Aggregate payload backing the Decision Room for a single application. */
export interface DecisionRoomData {
  applicationId: string
  overview: RiskOverview
  reviewRecommendation: 'approve' | 'reject' | 'manual_review' | 'request_information'
  reviewSeverity: ReviewSeverity
  manualReviewReasons: ManualReviewReason[]
  activeWarningCount: number
  policyOutcome: 'PASS' | 'FAIL' | 'MANUAL_REVIEW' | 'BLOCK'
  decisionStatus: 'pending' | 'in_review' | 'decided'
}

export type StressSeverity = 'baseline' | 'mild' | 'moderate' | 'severe'

export interface StressScenario {
  id: string
  name: string
  severity: StressSeverity
  /** Adjustments applied to the borrower's baseline, as signed percentages. */
  incomeChange: number
  expenseChange: number
  probabilityOfDefault: number
  riskBand: 'low' | 'medium' | 'high'
}

export interface CustomStressInputs {
  incomeChange: number
  expenseChange: number
  remittanceChange: number
  salesChange: number
  requestedAmount: number
  repaymentMonths: number
}

export interface EvidenceSourceRow {
  id: string
  date: string
  source: string
  description: string
  amount: number
  category: string
  included: boolean
  confidence: number
}

export interface EvidenceTrace {
  factorName: string
  effectOnRisk: 'increases_risk' | 'reduces_risk'
  sourceCount: number
  lastCalculated: string
  feature: {
    name: string
    formula: string
    borrowerValue: string
    referenceRange: string
    version: string
  }
  sources: EvidenceSourceRow[]
  lineage: {
    originalSource: string
    processingStep: string
    generatedAt: string
    modelVersion: string
  }
}

export type TimelineEventType =
  | 'application_created'
  | 'application_submitted'
  | 'consent_granted'
  | 'document_uploaded'
  | 'data_validated'
  | 'data_issue_detected'
  | 'features_generated'
  | 'risk_score_generated'
  | 'manual_review_requested'
  | 'information_requested'
  | 'borrower_responded'
  | 'analyst_decision_recorded'
  | 'decision_overridden'
  | 'appeal_submitted'
  | 'appeal_resolved'

export interface TimelineEvent {
  id: string
  type: TimelineEventType
  title: string
  actor: string
  timestamp: string
  description: string
  relatedRecord?: string
}

export interface BorrowerDecisionFactor {
  label: string
  detail: string
  verifiable: boolean
}

export type BorrowerAppealStatus =
  | 'none'
  | 'submitted'
  | 'under_review'
  | 'info_required'
  | 'completed'

export interface BorrowerDecision {
  status: 'approved' | 'declined' | 'more_info' | 'in_review'
  decisionDate: string
  plainLanguage: string
  meaning: string
  dataSourcesUsed: string[]
  factors: BorrowerDecisionFactor[]
  missingInformation: string[]
  moreInfoMayHelp: boolean
  appealStatus: BorrowerAppealStatus
}

export const RELIABILITY_LABEL_COPY: Record<ReliabilityLabel, string> = {
  excellent: 'Excellent',
  good: 'Good',
  limited: 'Limited',
  insufficient: 'Insufficient',
}

export const MODEL_AGREEMENT_COPY: Record<ModelAgreementLevel, string> = {
  strong: 'Strong',
  moderate: 'Moderate',
  weak: 'Weak',
}

export const RECOMMENDED_ACTION_COPY: Record<
  RiskOverview['recommendedAction'],
  string
> = {
  approve: 'Approve',
  reject: 'Reject',
  manual_review: 'Manual Review',
  request_information: 'Request Information',
}

export function reliabilityLabelFromScore(score: number): ReliabilityLabel {
  if (score >= 85) return 'excellent'
  if (score >= 70) return 'good'
  if (score >= 50) return 'limited'
  return 'insufficient'
}
