import type { Application } from '@/lib/types'
import {
  reliabilityLabelFromScore,
  type BorrowerDecision,
  type CounterfactualScenario,
  type CustomStressInputs,
  type DataReliabilitySource,
  type EvidenceTrace,
  type IntegrityAlert,
  type ModelPredictionComparison,
  type StressScenario,
  type TimelineEvent,
} from '@/src/features/applications/types/advanced-risk.types'

/** Deterministic pseudo-random in [0,1) seeded from an arbitrary string. */
function seed(input: string): number {
  let hash = 2166136261
  for (let i = 0; i < input.length; i += 1) {
    hash ^= input.charCodeAt(i)
    hash = Math.imul(hash, 16777619)
  }
  return (hash >>> 0) / 4294967295
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

function riskBandFromPd(pd: number): 'low' | 'medium' | 'high' {
  if (pd < 0.15) return 'low'
  if (pd < 0.3) return 'medium'
  return 'high'
}

/* ------------------------------------------------------------------ */
/* Enhancement 2 — Data Reliability                                    */
/* ------------------------------------------------------------------ */

export interface DataReliabilitySummary {
  overallScore: number
  sourceCount: number
  coverageMonths: number
  missingRate: number
  extractionConfidence: number
  consistency: 'consistent' | 'minor_issues' | 'inconsistent'
  sources: DataReliabilitySource[]
}

export function getDataReliability(app: Application): DataReliabilitySummary {
  const sources: DataReliabilitySource[] = app.dataSources.map((d, i) => {
    const u = seed(`${app.id}-${d.id}-rel`)
    const score = Math.round(clamp(d.qualityScore * 100 - u * 14 + 3, 34, 98))
    const missingRate = Number(clamp((1 - d.qualityScore) * 0.4 + u * 0.05, 0, 0.35).toFixed(3))
    const validationStatus =
      d.status === 'FAILED'
        ? 'failed'
        : score < 70 || missingRate > 0.15
          ? 'warning'
          : 'passed'
    const issues = [
      'Coverage gap in most recent month',
      'Duplicate transactions detected',
      'Low extraction confidence on 2 pages',
      'Declared income differs from inflows',
      'Category mapping incomplete',
    ]
    return {
      id: d.id,
      sourceType: d.type,
      score,
      label: reliabilityLabelFromScore(score),
      coverageStart: d.coverageStart,
      coverageEnd: d.coverageEnd,
      recordCount: d.records,
      missingRate,
      validationStatus,
      mainIssue: validationStatus === 'passed' ? undefined : issues[i % issues.length],
    }
  })

  const overallScore = sources.length
    ? Math.round(sources.reduce((s, r) => s + r.score, 0) / sources.length)
    : 0
  const missingRate = sources.length
    ? Number((sources.reduce((s, r) => s + r.missingRate, 0) / sources.length).toFixed(3))
    : 0
  const failing = sources.filter((s) => s.validationStatus !== 'passed').length

  return {
    overallScore,
    sourceCount: sources.length,
    coverageMonths: 6,
    missingRate,
    extractionConfidence: Number(clamp(0.95 - missingRate, 0.6, 0.99).toFixed(2)),
    consistency: failing === 0 ? 'consistent' : failing <= 1 ? 'minor_issues' : 'inconsistent',
    sources,
  }
}

/* ------------------------------------------------------------------ */
/* Enhancement 3 — Model Disagreement                                  */
/* ------------------------------------------------------------------ */

export interface ModelAgreementSummary {
  level: 'strong' | 'moderate' | 'weak'
  spread: number
  standardDeviation: number
  sameRiskBand: boolean
  recommendedAction: string
  models: ModelPredictionComparison[]
}

export function getModelComparisons(app: Application): ModelAgreementSummary {
  const base = app.probabilityOfDefault
  const u = seed(`${app.id}-models`)
  const spreadFactor = app.confidence < 0.75 ? 0.14 : app.confidence < 0.85 ? 0.07 : 0.03

  const defs = [
    { modelId: 'lr', modelName: 'Logistic Regression', version: 'v3.1.0', offset: -spreadFactor * 0.7 },
    { modelId: 'xgb', modelName: 'XGBoost', version: 'v4.2.1', offset: spreadFactor * 0.9 },
    { modelId: 'ebm', modelName: 'Explainable Boosting Machine', version: 'v2.0.4', offset: (u - 0.5) * spreadFactor },
  ]

  const models: ModelPredictionComparison[] = defs.map((m) => {
    const pd = Number(clamp(base + m.offset, 0.01, 0.95).toFixed(3))
    return {
      modelId: m.modelId,
      modelName: m.modelName,
      version: m.version,
      probabilityOfDefault: pd,
      riskBand: riskBandFromPd(pd),
      confidence: Number(clamp(app.confidence + (seed(m.modelId + app.id) - 0.5) * 0.1, 0.6, 0.98).toFixed(2)),
      calibrationStatus: pd > 0.5 ? 'warning' : 'good',
    }
  })

  const pds = models.map((m) => m.probabilityOfDefault)
  const spread = Number(((Math.max(...pds) - Math.min(...pds)) * 100).toFixed(1))
  const mean = pds.reduce((s, p) => s + p, 0) / pds.length
  const sd = Number((Math.sqrt(pds.reduce((s, p) => s + (p - mean) ** 2, 0) / pds.length) * 100).toFixed(1))
  const level = spread <= 5 ? 'strong' : spread <= 12 ? 'moderate' : 'weak'
  const sameRiskBand = new Set(models.map((m) => m.riskBand)).size === 1

  return {
    level,
    spread,
    standardDeviation: sd,
    sameRiskBand,
    recommendedAction:
      level === 'weak'
        ? 'Send to manual review — predictions differ significantly.'
        : level === 'moderate'
          ? 'Proceed with analyst confirmation.'
          : 'Automatic recommendation is reliable.',
    models,
  }
}

/* ------------------------------------------------------------------ */
/* Enhancement 4 — Counterfactuals                                     */
/* ------------------------------------------------------------------ */

export function getCounterfactuals(app: Application): CounterfactualScenario[] {
  const pd = app.probabilityOfDefault
  const defs = [
    {
      id: 'income-volatility',
      title: 'Reduce monthly income volatility',
      feature: 'Income volatility',
      currentValue: 32,
      proposedValue: 20,
      impact: 0.06,
      feasibility: 'moderate' as const,
    },
    {
      id: 'liquidity-buffer',
      title: 'Increase average liquidity buffer',
      feature: 'Liquidity buffer (RM)',
      currentValue: 350,
      proposedValue: 700,
      impact: 0.045,
      feasibility: 'difficult' as const,
    },
    {
      id: 'utility-timeliness',
      title: 'Improve utility-payment timeliness',
      feature: 'Utility timeliness (%)',
      currentValue: 78,
      proposedValue: 90,
      impact: 0.035,
      feasibility: 'easy' as const,
    },
  ]

  return defs.map((d) => {
    const simulated = Number(clamp(pd - d.impact, 0.02, 0.95).toFixed(3))
    return {
      id: `${app.id}-${d.id}`,
      title: d.title,
      feature: d.feature,
      currentValue: d.currentValue,
      proposedValue: d.proposedValue,
      originalProbability: pd,
      simulatedProbability: simulated,
      feasibility: d.feasibility,
    } satisfies CounterfactualScenario
  })
}

/** Pure simulator used by the interactive controls. */
export function simulatePd(
  basePd: number,
  inputs: {
    incomeChange: number
    volatilityChange: number
    expenseChange: number
    liquidityChange: number
    timelinessChange: number
  },
): number {
  const delta =
    -inputs.incomeChange * 0.0015 +
    inputs.volatilityChange * 0.0012 +
    inputs.expenseChange * 0.0013 -
    inputs.liquidityChange * 0.0008 -
    inputs.timelinessChange * 0.0011
  return Number(clamp(basePd + delta, 0.01, 0.97).toFixed(3))
}

/* ------------------------------------------------------------------ */
/* Enhancement 5 — Stress Testing                                      */
/* ------------------------------------------------------------------ */

export function getStressScenarios(app: Application): StressScenario[] {
  const base = app.probabilityOfDefault
  const defs: Array<{
    id: string
    name: string
    severity: StressScenario['severity']
    income: number
    expense: number
  }> = [
    { id: 'baseline', name: 'Baseline', severity: 'baseline', income: 0, expense: 0 },
    { id: 'income-10', name: 'Income −10%', severity: 'mild', income: -10, expense: 0 },
    { id: 'income-20', name: 'Income −20%', severity: 'moderate', income: -20, expense: 0 },
    { id: 'expense-15', name: 'Expenses +15%', severity: 'mild', income: 0, expense: 15 },
    { id: 'remittance-stop', name: 'Remittance stops', severity: 'severe', income: -28, expense: 0 },
    { id: 'sales-25', name: 'Sales −25%', severity: 'severe', income: -25, expense: 5 },
  ]

  return defs.map((d) => {
    const pd = stressPd(base, d.income, d.expense)
    return {
      id: `${app.id}-${d.id}`,
      name: d.name,
      severity: d.severity,
      incomeChange: d.income,
      expenseChange: d.expense,
      probabilityOfDefault: pd,
      riskBand: riskBandFromPd(pd),
    }
  })
}

function stressPd(basePd: number, incomeChange: number, expenseChange: number): number {
  const delta = -incomeChange * 0.0022 + expenseChange * 0.0025
  return Number(clamp(basePd + delta, 0.01, 0.98).toFixed(3))
}

/** Interactive custom stress scenario, returned as a full StressScenario. */
export function computeCustomStress(
  app: Application,
  inputs: CustomStressInputs,
): StressScenario {
  const delta =
    -inputs.incomeChange * 0.0022 +
    inputs.expenseChange * 0.0025 +
    -inputs.remittanceChange * 0.0018 +
    -inputs.salesChange * 0.0016 +
    (inputs.requestedAmount / Math.max(app.requestedAmount, 1) - 1) * 0.08
  const pd = Number(clamp(app.probabilityOfDefault + delta, 0.01, 0.98).toFixed(3))
  return {
    id: `${app.id}-custom`,
    name: 'Custom',
    severity: 'moderate',
    incomeChange: inputs.incomeChange,
    expenseChange: inputs.expenseChange,
    probabilityOfDefault: pd,
    riskBand: riskBandFromPd(pd),
  }
}

/* ------------------------------------------------------------------ */
/* Enhancement 6 — Integrity / Fraud Alerts                            */
/* ------------------------------------------------------------------ */

export function getIntegrityAlerts(app: Application): IntegrityAlert[] {
  const pool: Array<Omit<IntegrityAlert, 'id' | 'dismissed'>> = [
    {
      category: 'fraud',
      severity: 'critical',
      title: 'Declared income differs from observed inflows',
      description:
        'Declared monthly income is 24% higher than the average observed deposit inflow across connected accounts.',
      detectedAt: app.lastUpdated,
      hasEvidence: true,
    },
    {
      category: 'data_integrity',
      severity: 'warning',
      title: 'Duplicate statement detected',
      description: 'Two uploaded bank statements share identical opening and closing balances.',
      detectedAt: app.lastUpdated,
      hasEvidence: true,
    },
    {
      category: 'data_integrity',
      severity: 'info',
      title: 'Missing transaction period',
      description: 'No transactions recorded between the 12th and 19th of the most recent month.',
      detectedAt: app.lastUpdated,
      hasEvidence: false,
    },
    {
      category: 'fraud',
      severity: 'warning',
      title: 'Modified document metadata',
      description: 'PDF metadata indicates the document was edited after the statement date.',
      detectedAt: app.lastUpdated,
      hasEvidence: true,
    },
  ]

  const count = app.riskBand === 'HIGH' ? 3 : app.riskBand === 'MEDIUM' ? 2 : 1
  return pool.slice(0, count).map((a, i) => ({
    ...a,
    id: `${app.id}-alert-${i}`,
    dismissed: false,
  }))
}

/* ------------------------------------------------------------------ */
/* Enhancement 7 — Evidence Traceability                               */
/* ------------------------------------------------------------------ */

interface EvidenceSourceRowInternal {
  desc: string
  amount: number
  category: string
  included: boolean
}

function buildEvidenceTrace(
  app: Application,
  opts: {
    factorName: string
    effectOnRisk: EvidenceTrace['effectOnRisk']
    featureName: string
    formula: string
    borrowerValue: string
    referenceRange: string
  },
): EvidenceTrace {
  const rows: EvidenceSourceRowInternal[] = [
    { desc: 'Salary credit — employer transfer', amount: 4200, category: 'Income', included: true },
    { desc: 'E-wallet cash-in', amount: 300, category: 'Income', included: true },
    { desc: 'Utility bill — electricity', amount: -180, category: 'Utilities', included: true },
    { desc: 'Duplicate deposit (excluded)', amount: 900, category: 'Income', included: false },
    { desc: 'POS settlement', amount: 1250, category: 'Business', included: true },
  ]

  return {
    factorName: opts.factorName,
    effectOnRisk: opts.effectOnRisk,
    sourceCount: rows.filter((r) => r.included).length,
    lastCalculated: app.lastUpdated,
    feature: {
      name: opts.featureName,
      formula: opts.formula,
      borrowerValue: opts.borrowerValue,
      referenceRange: opts.referenceRange,
      version: 'fe-v2.3.0',
    },
    sources: rows.map((r, i) => ({
      id: `${app.id}-ev-${i}`,
      date: app.dataSources[0]?.coverageEnd ?? app.lastUpdated,
      source: app.dataSources[0]?.fileName ?? 'bank_statement.pdf',
      description: r.desc,
      amount: r.amount,
      category: r.category,
      included: r.included,
      confidence: Number(clamp(0.98 - i * 0.05 - seed(app.id + i) * 0.05, 0.6, 0.99).toFixed(2)),
    })),
    lineage: {
      originalSource: app.dataSources[0]?.fileName ?? 'bank_statement.pdf',
      processingStep: 'Extraction → categorisation → feature aggregation',
      generatedAt: app.lastUpdated,
      modelVersion: app.modelVersion,
    },
  }
}

export function getEvidenceTraceForFactor(
  app: Application,
  factor: Application['factors'][number],
): EvidenceTrace {
  return buildEvidenceTrace(app, {
    factorName: factor.label,
    effectOnRisk: factor.direction === 'increases_risk' ? 'increases_risk' : 'reduces_risk',
    featureName: factor.feature,
    formula: 'mean(monthly_inflows) − mean(monthly_outflows) over trailing 6 months',
    borrowerValue: factor.borrowerValue,
    referenceRange: factor.expectedRange,
  })
}

export function getEvidenceTraceForAlert(
  app: Application,
  alert: IntegrityAlert,
): EvidenceTrace {
  return buildEvidenceTrace(app, {
    factorName: alert.title,
    effectOnRisk: 'increases_risk',
    featureName: 'integrity_signal',
    formula: 'rule-based anomaly detection over extracted transactions',
    borrowerValue: alert.category.replace(/_/g, ' '),
    referenceRange: 'no anomalies expected',
  })
}

/* ------------------------------------------------------------------ */
/* Enhancement 9 — Timeline                                            */
/* ------------------------------------------------------------------ */

export function getApplicationTimeline(app: Application): TimelineEvent[] {
  const events: Array<Omit<TimelineEvent, 'id'>> = [
    {
      type: 'application_created',
      title: 'Application created',
      actor: app.borrowerName,
      timestamp: app.submittedAt,
      description: `Application ${app.reference} created for ${app.purpose}.`,
    },
    {
      type: 'consent_granted',
      title: 'Consent granted',
      actor: app.borrowerName,
      timestamp: app.submittedAt,
      description: 'Borrower granted consent to access alternative financial data.',
    },
    {
      type: 'document_uploaded',
      title: 'Documents uploaded',
      actor: app.borrowerName,
      timestamp: app.submittedAt,
      description: `${app.dataSources.length} data source(s) connected.`,
    },
    {
      type: 'data_validated',
      title: 'Data validated',
      actor: 'System',
      timestamp: app.lastUpdated,
      description: 'Automated validation and consistency checks completed.',
    },
    {
      type: 'features_generated',
      title: 'Features generated',
      actor: 'Feature service',
      timestamp: app.lastUpdated,
      description: 'Engineered features produced for scoring.',
    },
    {
      type: 'risk_score_generated',
      title: 'Risk score generated',
      actor: `Model ${app.modelVersion}`,
      timestamp: app.lastUpdated,
      description: `Probability of default ${(app.probabilityOfDefault * 100).toFixed(1)}%.`,
      relatedRecord: app.id,
    },
  ]

  if (app.status === 'MANUAL_REVIEW') {
    events.push({
      type: 'manual_review_requested',
      title: 'Manual review requested',
      actor: 'System',
      timestamp: app.lastUpdated,
      description: 'Application routed to an analyst for manual review.',
    })
  }

  if (['APPROVED', 'REJECTED'].includes(app.status)) {
    events.push({
      type: 'analyst_decision_recorded',
      title: 'Analyst decision recorded',
      actor: app.assignedAnalyst ?? 'Analyst',
      timestamp: app.lastUpdated,
      description: `Decision: ${app.status.toLowerCase()}.`,
      relatedRecord: app.id,
    })
  }

  return events.map((e, i) => ({ ...e, id: `${app.id}-tl-${i}` }))
}

/* ------------------------------------------------------------------ */
/* Enhancement 8 — Borrower decision explanation                       */
/* ------------------------------------------------------------------ */

export function getBorrowerDecision(app: Application): BorrowerDecision {
  const status =
    app.status === 'APPROVED'
      ? 'approved'
      : app.status === 'REJECTED'
        ? 'declined'
        : app.status === 'MANUAL_REVIEW'
          ? 'in_review'
          : 'more_info'

  const meaningCopy: Record<BorrowerDecision['status'], string> = {
    approved: 'Your application met our assessment criteria and has been approved.',
    declined:
      'Based on the information reviewed, we were unable to approve this application at this time.',
    in_review:
      'Your application is being reviewed by a specialist. No action is needed from you right now.',
    more_info: 'We need a little more information before we can complete your assessment.',
  }

  return {
    status,
    decisionDate: app.lastUpdated,
    meaning: meaningCopy[status],
    plainLanguage:
      'We looked at how money moves in and out of your accounts over the last six months, how regularly your income arrives, and how consistently you pay recurring bills. These patterns help us understand affordability.',
    dataSourcesUsed: app.dataSources.map((d) => d.type),
    factors: [
      {
        label: 'Income regularity',
        detail: 'How consistent and predictable your incoming payments were.',
        verifiable: true,
      },
      {
        label: 'Spending vs income',
        detail: 'The balance between your monthly income and regular expenses.',
        verifiable: true,
      },
      {
        label: 'Bill payment timeliness',
        detail: 'Whether recurring bills such as utilities were paid on time.',
        verifiable: true,
      },
    ],
    missingInformation:
      status === 'more_info'
        ? ['One month of bank statements appears incomplete', 'Utility account not yet linked']
        : [],
    moreInfoMayHelp: status !== 'approved',
    appealStatus: 'none',
  }
}
