import type { Application } from '@/lib/types'
import type {
  DecisionRoomData,
  ManualReviewReason,
  ModelAgreementLevel,
  ReviewSeverity,
  RiskOverview,
} from '@/src/features/applications/types/advanced-risk.types'

const RISK_BAND_MAP: Record<Application['riskBand'], RiskOverview['riskBand']> = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
}

const ACTION_MAP: Record<string, RiskOverview['recommendedAction']> = {
  APPROVE: 'approve',
  REJECT: 'reject',
  MANUAL_REVIEW: 'manual_review',
  REQUEST_INFORMATION: 'request_information',
  WITHDRAW: 'manual_review',
}

/** Deterministic pseudo-random in [0,1) seeded from the application id. */
function seededUnit(id: string): number {
  let hash = 0
  for (let i = 0; i < id.length; i += 1) {
    hash = (hash * 31 + id.charCodeAt(i)) % 100000
  }
  return hash / 100000
}

function modelAgreementFor(app: Application, unit: number): ModelAgreementLevel {
  // Lower confidence or high risk tends to reduce cross-model agreement.
  const signal = app.confidence - (app.riskBand === 'HIGH' ? 0.15 : 0) - unit * 0.1
  if (signal >= 0.82) return 'strong'
  if (signal >= 0.68) return 'moderate'
  return 'weak'
}

function buildManualReviewReasons(
  app: Application,
  reliability: number,
  agreement: ModelAgreementLevel,
): ManualReviewReason[] {
  const reasons: ManualReviewReason[] = []

  if (agreement === 'weak') {
    reasons.push({
      id: `${app.id}-mr-disagreement`,
      code: 'MODEL_DISAGREEMENT',
      title: 'Model disagreement',
      description:
        'Challenger and champion models produce materially different probability estimates for this borrower.',
      severity: 'critical',
      resolved: false,
    })
  }

  if (reliability < 80) {
    reasons.push({
      id: `${app.id}-mr-reliability`,
      code: 'LOW_DATA_RELIABILITY',
      title: 'Low data reliability',
      description:
        'One or more connected sources have coverage gaps or unresolved consistency checks.',
      severity: reliability < 65 ? 'critical' : 'warning',
      resolved: false,
    })
  }

  // Score close to a risk-band boundary (0.15 / 0.30) implies threshold proximity.
  const pd = app.probabilityOfDefault
  const nearThreshold = Math.min(Math.abs(pd - 0.15), Math.abs(pd - 0.3))
  if (nearThreshold <= 0.03) {
    reasons.push({
      id: `${app.id}-mr-threshold`,
      code: 'NEAR_THRESHOLD',
      title: 'Prediction near decision threshold',
      description: `The score is within ${(nearThreshold * 100).toFixed(1)} percentage points of a policy threshold.`,
      severity: 'warning',
      resolved: false,
    })
  }

  const failingPolicy = app.policyResults.find(
    (p) => p.result === 'MANUAL_REVIEW' || p.result === 'FAIL' || p.result === 'BLOCK',
  )
  if (failingPolicy) {
    reasons.push({
      id: `${app.id}-mr-policy`,
      code: 'POLICY_EXCEPTION',
      title: 'Policy exception',
      description: `${failingPolicy.name}: ${failingPolicy.detail}`,
      severity: failingPolicy.result === 'BLOCK' ? 'critical' : 'warning',
      resolved: false,
    })
  }

  if (app.borrowerType === 'THIN_FILE') {
    reasons.push({
      id: `${app.id}-mr-coverage`,
      code: 'OUTSIDE_COVERAGE',
      title: 'Borrower outside model coverage',
      description:
        'Thin-file borrower with limited historical signal; model coverage confidence is reduced.',
      severity: 'info',
      resolved: false,
    })
  }

  return reasons
}

function severityOf(reasons: ManualReviewReason[]): ReviewSeverity {
  if (reasons.some((r) => r.severity === 'critical')) return 'critical'
  if (reasons.some((r) => r.severity === 'warning')) return 'warning'
  return 'info'
}

/**
 * Derives a fully-typed Decision Room payload for any application.
 * In production this would be fetched from the risk service; here it is
 * deterministically generated so every mock application renders consistently.
 */
export function getDecisionRoomData(app: Application): DecisionRoomData {
  const unit = seededUnit(app.id)
  const reliabilityScore = Math.round(
    Math.min(97, Math.max(38, app.dataQuality * 100 - unit * 12 + 4)),
  )
  const agreement = modelAgreementFor(app, unit)
  const reasons = buildManualReviewReasons(app, reliabilityScore, agreement)

  const overview: RiskOverview = {
    probabilityOfDefault: app.probabilityOfDefault,
    riskBand: RISK_BAND_MAP[app.riskBand],
    confidence: app.confidence,
    recommendedAction: ACTION_MAP[app.recommendedAction] ?? 'manual_review',
    modelVersion: app.modelVersion,
    scoredAt: app.lastUpdated,
    dataReliabilityScore: reliabilityScore,
    modelAgreement: agreement,
  }

  const policyOutcome =
    app.policyResults.find((p) => p.result === 'BLOCK')?.result ??
    app.policyResults.find((p) => p.result === 'FAIL')?.result ??
    app.policyResults.find((p) => p.result === 'MANUAL_REVIEW')?.result ??
    'PASS'

  const decidedStatuses: Application['status'][] = ['APPROVED', 'REJECTED', 'WITHDRAWN', 'ARCHIVED']
  const decisionStatus = decidedStatuses.includes(app.status)
    ? 'decided'
    : app.status === 'MANUAL_REVIEW'
      ? 'in_review'
      : 'pending'

  return {
    applicationId: app.id,
    overview,
    reviewRecommendation: overview.recommendedAction,
    reviewSeverity: severityOf(reasons),
    manualReviewReasons: reasons,
    activeWarningCount: reasons.filter((r) => r.severity !== 'info').length,
    policyOutcome,
    decisionStatus,
  }
}
