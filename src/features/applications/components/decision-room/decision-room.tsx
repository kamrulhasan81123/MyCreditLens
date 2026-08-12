'use client'

import { RiskOverviewCard } from './risk-overview-card'
import { ManualReviewReasonsCard } from './manual-review-reasons-card'
import type { Application } from '@/lib/types'
import type { DecisionRoomData } from '@/src/features/applications/types/advanced-risk.types'

/**
 * Consolidated analyst workspace shown as the first tab of the application
 * detail page. The sticky decision panel lives in the page's right column,
 * so this component fills the main/left area only.
 *
 * Later phases add: data reliability, model agreement, key factors, integrity
 * alerts, stress-test summary, and the application timeline.
 */
export function DecisionRoom({
  application,
  room,
  onViewRiskAnalysis,
  onCompareModels,
  onRunStressTest,
  onContinueDecision,
}: {
  application: Application
  room: DecisionRoomData
  onViewRiskAnalysis?: () => void
  onCompareModels?: () => void
  onRunStressTest?: () => void
  onContinueDecision?: () => void
}) {
  return (
    <div className="space-y-6">
      <RiskOverviewCard
        overview={room.overview}
        onViewRiskAnalysis={onViewRiskAnalysis}
        onCompareModels={onCompareModels}
        onRunStressTest={onRunStressTest}
      />

      <ManualReviewReasonsCard
        reasons={room.manualReviewReasons}
        onContinueDecision={onContinueDecision}
      />

      {/* Decision recommendation and controls are provided by the sticky
          DecisionPanel in the page's right column (single decision system).
          On mobile it appears directly below this workspace. */}
      <p className="sr-only">
        Analyst decision controls for {application.borrowerName} are available in the decision
        panel.
      </p>
    </div>
  )
}
