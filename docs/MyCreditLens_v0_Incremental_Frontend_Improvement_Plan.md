# MyCreditLens — Incremental Frontend Improvement Plan for v0.app

## 1. Purpose of This Document

This document is an **incremental enhancement plan** for the already completed MyCreditLens frontend.

It must be used together with the existing frontend specification:

- `MyCreditLens_Frontend_UIUX_Development_Plan.md`

The existing application structure, navigation, design system, pages, forms, tables, components, and workflows are already implemented.

The purpose of this document is to help v0.app add selected advanced features **without redesigning, replacing, renaming, or duplicating the existing frontend**.

---

# 2. Critical Instructions for v0.app

## 2.1 Do Not Rebuild the Application

Do not generate a new application from scratch.

Do not:
- Replace the existing dashboard
- Create a second sidebar
- Create duplicate application pages
- Rename current routes
- Replace the existing colour palette
- Introduce a new typography system
- Change the authentication flow
- Redesign existing tables
- Replace the current application-detail tabs
- Move existing features to new routes unless explicitly instructed
- Add placeholder public landing pages
- Remove existing components
- Change current role permissions

The task is to **extend the current frontend only**.

---

## 2.2 Preserve the Existing Design System

Continue using the existing visual system:

### Colours
- Deep Navy: `#0F172A`
- Slate Blue: `#1E3A8A`
- Action Blue: `#2563EB`
- Background: `#F8FAFC`
- Surface: `#FFFFFF`
- Border: `#E2E8F0`
- Secondary Text: `#64748B`
- Primary Text: `#0F172A`
- Low Risk: `#15803D`
- Medium Risk: `#B45309`
- High Risk: `#B91C1C`
- Manual Review: `#6D28D9`
- Information: `#0369A1`

### Typography
- Inter
- Existing type hierarchy
- JetBrains Mono for IDs or technical values

### Components
Continue using:
- shadcn/ui
- Tailwind CSS
- Lucide icons
- Existing cards
- Existing tables
- Existing badges
- Existing dialogs
- Existing tabs
- Existing form components
- Existing toast system

Do not introduce another UI library.

---

## 2.3 Preserve Existing Routes

The enhancements should be added primarily to the existing route:

```text
/lender/applications/[applicationId]
```

Use the existing application-detail page and its current tabs:

- Summary
- Financial Data
- Risk Analysis
- Explainability
- Documents
- Consent
- Analyst Notes
- Audit Trail

Only add a new tab when this document explicitly requires it.

---

## 2.4 Use Mock Data Only

The frontend is already completed before backend integration.

For all new features:
- Use typed mock data
- Keep data in a separate mock-data file
- Create TypeScript interfaces
- Do not hard-code repeated values inside JSX
- Add loading, error, empty, and populated states
- Keep API integration points clearly separated

Recommended location:

```text
src/features/applications/mock-data/
src/features/applications/types/
src/features/applications/components/
```

---

# 3. Enhancement Scope

Implement the following enhancements only:

1. Risk Decision Room
2. Data Reliability Score
3. Model Disagreement and Uncertainty
4. Counterfactual Explanation
5. Cash-Flow Stress Testing
6. Fraud and Inconsistency Indicators
7. Evidence Traceability Drawer
8. Borrower-Friendly Explanation and Appeal
9. Application Timeline Improvement
10. Manual Review and Abstention Reasons

Do not implement graph fraud visualisation, real banking integrations, blockchain, loan disbursement, or live model training in this frontend phase.

---

# 4. Enhancement 1 — Risk Decision Room

## 4.1 Objective

Create a consolidated analyst workspace inside the existing application-detail page.

This must not replace the current tabs. It should be added as the first tab named:

```text
Decision Room
```

Updated tab order:

1. Decision Room
2. Summary
3. Financial Data
4. Risk Analysis
5. Explainability
6. Documents
7. Consent
8. Analyst Notes
9. Audit Trail

---

## 4.2 Layout

Use a responsive 12-column desktop layout.

### Left/Main Area — 8 Columns

Display:

1. Risk overview
2. Data reliability
3. Model agreement
4. Key explanation factors
5. Fraud and inconsistency alerts
6. Stress-test summary
7. Application timeline

### Right/Sticky Area — 4 Columns

Display:

1. Decision recommendation
2. Manual-review reasons
3. Analyst decision controls
4. Analyst notes
5. Evidence checklist

The right panel should remain sticky below the application header on desktop.

On mobile:
- Use a single-column layout
- Place the decision panel after the risk summary
- Add a sticky bottom action bar

---

## 4.3 Risk Overview Card

Display:

- Probability of default
- Risk band
- Prediction confidence
- Recommended action
- Model version
- Scoring date
- Data reliability score
- Model agreement level

Example:

```text
Probability of Default: 24.8%
Risk Band: Medium
Prediction Confidence: 86%
Recommended Action: Manual Review
Data Reliability: 79%
Model Agreement: Moderate
```

### Buttons

- View Full Risk Analysis
- Compare Models
- Run Stress Test

---

## 4.4 Decision Panel

Display:

- Current recommendation
- Policy-rule result
- Active warning count
- Required review reasons
- Analyst assignment
- Decision status

### Buttons

- Approve
- Reject
- Request Information
- Send to Manual Review

### Rules

Every decision opens the existing decision modal.

The modal must require:
- Decision reason
- Supporting note
- Evidence reviewed checkboxes
- Override confirmation when applicable

Do not create a second decision system.

---

# 5. Enhancement 2 — Data Reliability Score

## 5.1 Objective

Clearly separate data reliability from prediction confidence.

Prediction confidence indicates model certainty.

Data reliability indicates the quality, completeness, consistency, and coverage of the underlying borrower data.

---

## 5.2 Placement

Add the Data Reliability component to:

- Decision Room
- Risk Analysis tab
- Data Review step in New Assessment
- Financial Data tab

---

## 5.3 Component Design

Component name:

```text
DataReliabilityCard
```

Display:

- Overall reliability score from 0 to 100
- Reliability label
- Number of data sources
- Date coverage
- Missing-data rate
- Extraction confidence
- Consistency status

### Reliability Labels

- 85–100: Excellent
- 70–84: Good
- 50–69: Limited
- Below 50: Insufficient

Do not use colour alone. Always show:
- Icon
- Label
- Score
- Supporting description

---

## 5.4 Source Reliability Table

Columns:

- Data Source
- Reliability Score
- Coverage Period
- Records
- Missing Data
- Validation Status
- Main Issue
- Action

Example sources:
- Bank Statement
- E-Wallet
- Utility Payments
- Gig Income
- POS Sales

### Row Actions

- View Source
- View Issues
- Reprocess
- Request Replacement

---

## 5.5 Details Drawer

Clicking a source opens a right-side drawer.

Display:

- Source metadata
- File name
- Upload date
- Date range
- Record count
- Duplicate count
- Missing fields
- Validation warnings
- Extraction confidence
- Data-quality checks

---

# 6. Enhancement 3 — Model Disagreement and Uncertainty

## 6.1 Objective

Show that multiple models may produce different predictions and that the system can abstain from making an automatic recommendation.

---

## 6.2 Placement

Add a new section inside:

- Decision Room
- Risk Analysis tab

Component name:

```text
ModelAgreementCard
```

---

## 6.3 Model Comparison Table

Columns:

- Model
- Probability of Default
- Risk Band
- Confidence
- Calibration Status
- Version

Use example models:

- Logistic Regression
- XGBoost
- Explainable Boosting Machine

Example:

| Model | PD | Risk Band | Confidence |
|---|---:|---|---:|
| Logistic Regression | 19.2% | Medium | 82% |
| XGBoost | 27.8% | Medium | 88% |
| Explainable Boosting Machine | 22.4% | Medium | 84% |

---

## 6.4 Agreement Summary

Display:

- Agreement level: High, Moderate, or Low
- Prediction spread
- Standard deviation
- Whether all models produce the same risk band
- Recommended action

Rules for mock UI:

```text
High Agreement:
Prediction spread <= 5 percentage points

Moderate Agreement:
Prediction spread > 5 and <= 12 percentage points

Low Agreement:
Prediction spread > 12 percentage points
```

---

## 6.5 Uncertainty Warning

If agreement is low, show:

```text
Manual review recommended because model predictions differ significantly.
```

Add buttons:

- View Model Details
- Send to Manual Review

---

# 7. Enhancement 4 — Counterfactual Explanation

## 7.1 Objective

Show realistic changes that could move the borrower into a lower-risk category.

This is a decision-support feature, not a promise or guarantee.

---

## 7.2 Placement

Add to the existing Explainability tab below the SHAP explanation section.

Component name:

```text
CounterfactualSimulator
```

---

## 7.3 Default View

Display a card titled:

```text
What Could Improve This Assessment?
```

Show up to three recommended changes.

Example:

1. Reduce monthly income volatility from 32% to 20%
2. Increase average liquidity buffer from RM350 to RM700
3. Improve utility-payment timeliness from 78% to 90%

For each recommendation display:

- Current value
- Suggested value
- Estimated PD before
- Estimated PD after
- Estimated risk-band change
- Feasibility label

---

## 7.4 Interactive Controls

Use sliders or numeric inputs for:

- Monthly income
- Income volatility
- Monthly expenses
- Liquidity buffer
- Utility-payment timeliness
- Requested loan amount

### Buttons

- Recalculate Scenario
- Reset Changes
- Save Scenario
- Compare with Original

---

## 7.5 Result Panel

Display:

- Original PD
- Simulated PD
- Difference
- Original risk band
- Simulated risk band
- Changed factors

Add this warning:

```text
Scenario results are estimates generated for analyst review and do not guarantee approval or future repayment performance.
```

---

# 8. Enhancement 5 — Cash-Flow Stress Testing

## 8.1 Objective

Allow analysts to test how the borrower could perform under adverse financial conditions.

---

## 8.2 Placement

Add a new subsection within the Risk Analysis tab named:

```text
Stress Testing
```

Also show a condensed summary in the Decision Room.

Component name:

```text
StressTestPanel
```

---

## 8.3 Preset Scenarios

Add scenario cards:

1. Income decreases by 10%
2. Income decreases by 20%
3. Monthly expenses increase by 15%
4. Remittance income stops
5. Business sales decrease by 25%
6. Requested loan amount increases

Each card shows:

- Scenario name
- Stress severity
- Resulting PD
- Resulting risk band
- Change from baseline

---

## 8.4 Custom Scenario

Inputs:

- Income change percentage
- Expense change percentage
- Remittance change
- Sales change percentage
- Requested loan amount
- Repayment duration

### Buttons

- Run Custom Stress Test
- Reset
- Save Scenario
- Export Results

---

## 8.5 Comparison Chart

Use a bar chart or line chart showing:

- Baseline PD
- Mild stress
- Moderate stress
- Severe stress

The chart must include accessible text summaries.

---

# 9. Enhancement 6 — Fraud and Inconsistency Indicators

## 9.1 Objective

Separate fraud risk and data inconsistency from credit risk.

Do not merge them into the probability-of-default score.

---

## 9.2 Placement

Add a section to:

- Decision Room
- Financial Data tab
- Data Review step

Component name:

```text
IntegrityAlertsPanel
```

---

## 9.3 Summary Indicators

Display three separate indicators:

- Credit Risk
- Fraud Risk
- Data Integrity Risk

Example:

```text
Credit Risk: Medium
Fraud Risk: Low
Data Integrity Risk: Elevated
```

---

## 9.4 Alert Types

Support the following mock alerts:

- Duplicate statement detected
- Declared income differs from observed inflows
- Missing transaction period
- Repeated transaction identifier
- Unusual end-of-month deposit
- Conflicting employer information
- Modified document metadata
- Multiple records with identical values

---

## 9.5 Alert Card

Each alert displays:

- Severity
- Title
- Description
- Detection source
- Detected time
- Related data source
- Status

### Buttons

- Review Evidence
- Mark Reviewed
- Dismiss with Reason
- Escalate

Dismissal must require a reason.

---

# 10. Enhancement 7 — Evidence Traceability Drawer

## 10.1 Objective

Allow an analyst to trace an explanation from:

```text
Decision Factor → Engineered Feature → Source Transaction or Document
```

---

## 10.2 Trigger Locations

Add a `View Evidence` action beside:

- SHAP factors
- Counterfactual recommendations
- Fraud alerts
- Policy-rule results
- Income and cash-flow metrics

---

## 10.3 Drawer Structure

Component name:

```text
EvidenceTraceDrawer
```

### Header
- Factor name
- Effect on risk
- Source count
- Last calculated

### Section 1: Feature Calculation
Display:
- Feature name
- Formula summary
- Borrower value
- Reference range
- Feature version

### Section 2: Source Evidence
Table columns:
- Date
- Source
- Description
- Amount
- Category
- Included in Calculation
- Confidence

### Section 3: Data Lineage
Display:
- Original source
- Processing step
- Feature-generation date
- Model version

### Buttons

- Open Source Record
- Add Analyst Note
- Flag Data Issue
- Export Evidence

---

# 11. Enhancement 8 — Borrower-Friendly Explanation and Appeal

## 11.1 Objective

Add a transparent borrower-facing decision explanation and reconsideration workflow.

---

## 11.2 Borrower Application Status Page

Enhance the existing borrower application-status page.

When a decision exists, display:

- Application status
- Decision date
- Plain-language explanation
- Data sources used
- Important contributing factors
- Missing information
- Next available action

Do not show:
- Raw SHAP values
- Internal fraud investigation details
- Internal policy thresholds
- Analyst-only notes

---

## 11.3 Borrower Explanation Card

Component name:

```text
BorrowerDecisionExplanation
```

Display:

- What the decision means
- Main factors considered
- Information the borrower can verify
- Whether more information may help
- Contact or support action

### Buttons

- View Bahasa Melayu Version
- Download Explanation
- Correct My Information
- Request Reconsideration

---

## 11.4 Appeal Modal

Fields:

- Appeal reason
- Information believed to be incorrect
- Additional explanation
- Supporting-document upload
- Consent confirmation

### Buttons

- Submit Reconsideration Request
- Save Draft
- Cancel

After submission, display status:

- Submitted
- Under Review
- Additional Information Required
- Completed

---

# 12. Enhancement 9 — Application Timeline Improvement

## 12.1 Objective

Improve the existing audit-style lifecycle timeline without replacing the full Audit Trail tab.

---

## 12.2 Placement

Show a compact timeline in:
- Decision Room
- Summary tab
- Borrower application-status page

Use the full timeline in:
- Audit Trail tab

---

## 12.3 Timeline Events

Support:

- Application created
- Application submitted
- Consent granted
- Document uploaded
- Data validated
- Data issue detected
- Features generated
- Risk score generated
- Manual review requested
- Information requested
- Borrower responded
- Analyst decision recorded
- Decision overridden
- Appeal submitted
- Appeal resolved

Each item shows:

- Icon
- Event title
- Actor
- Timestamp
- Description
- Related action

---

## 12.4 Timeline Buttons

- View Full Audit Trail
- Open Related Record
- Export Timeline

---

# 13. Enhancement 10 — Manual Review and Abstention Reasons

## 13.1 Objective

Make manual-review recommendations explicit and explainable.

---

## 13.2 Review Reasons

Support:

- Low data reliability
- Model disagreement
- Prediction near decision threshold
- Borrower outside model coverage
- Missing critical data
- Fraud or integrity alert
- Policy exception
- Analyst escalation

---

## 13.3 Component

Component name:

```text
ManualReviewReasonsCard
```

Display:

- Recommendation
- Number of review reasons
- Severity
- Required actions
- Completion state

Example:

```text
Manual Review Required

Reasons:
1. Model prediction spread is 14.2 percentage points.
2. E-wallet data contains a three-week coverage gap.
3. The score is within 2 percentage points of the policy threshold.
```

### Buttons

- Assign Reviewer
- Add Review Note
- Resolve Requirement
- Continue Decision

---

# 14. Shared TypeScript Interfaces

Create shared types similar to:

```ts
export interface DataReliabilitySource {
  id: string
  sourceType: string
  score: number
  label: "excellent" | "good" | "limited" | "insufficient"
  coverageStart: string
  coverageEnd: string
  recordCount: number
  missingRate: number
  validationStatus: "passed" | "warning" | "failed"
  mainIssue?: string
}

export interface ModelPredictionComparison {
  modelId: string
  modelName: string
  version: string
  probabilityOfDefault: number
  riskBand: "low" | "medium" | "high"
  confidence: number
  calibrationStatus: "good" | "warning" | "poor"
}

export interface CounterfactualScenario {
  id: string
  title: string
  feature: string
  currentValue: number
  proposedValue: number
  originalProbability: number
  simulatedProbability: number
  feasibility: "easy" | "moderate" | "difficult"
}

export interface IntegrityAlert {
  id: string
  severity: "low" | "medium" | "high" | "critical"
  type: string
  title: string
  description: string
  sourceId?: string
  status: "open" | "reviewed" | "dismissed" | "escalated"
  detectedAt: string
}

export interface ManualReviewReason {
  id: string
  code: string
  title: string
  description: string
  severity: "info" | "warning" | "critical"
  resolved: boolean
}
```

---

# 15. Recommended Component Structure

```text
src/features/applications/
├── components/
│   ├── decision-room/
│   │   ├── decision-room.tsx
│   │   ├── risk-overview-card.tsx
│   │   ├── decision-panel.tsx
│   │   └── manual-review-reasons-card.tsx
│   ├── reliability/
│   │   ├── data-reliability-card.tsx
│   │   ├── source-reliability-table.tsx
│   │   └── source-reliability-drawer.tsx
│   ├── uncertainty/
│   │   ├── model-agreement-card.tsx
│   │   └── model-comparison-table.tsx
│   ├── explainability/
│   │   ├── counterfactual-simulator.tsx
│   │   └── evidence-trace-drawer.tsx
│   ├── stress-testing/
│   │   ├── stress-test-panel.tsx
│   │   ├── preset-scenario-card.tsx
│   │   └── stress-comparison-chart.tsx
│   ├── integrity/
│   │   ├── integrity-alerts-panel.tsx
│   │   └── integrity-alert-card.tsx
│   ├── timeline/
│   │   └── enhanced-application-timeline.tsx
│   └── borrower/
│       ├── borrower-decision-explanation.tsx
│       └── reconsideration-modal.tsx
├── mock-data/
│   ├── decision-room.mock.ts
│   ├── reliability.mock.ts
│   ├── model-comparison.mock.ts
│   ├── counterfactual.mock.ts
│   ├── stress-tests.mock.ts
│   └── integrity-alerts.mock.ts
└── types/
    └── advanced-risk.types.ts
```

---

# 16. v0.app Implementation Sequence

Do not ask v0.app to implement everything in one generation.

Use the following sequence.

## Prompt 1 — Decision Room Shell

Implement:
- New Decision Room tab
- Desktop and mobile layout
- Risk overview card
- Sticky decision panel
- Manual-review reasons card

Do not implement charts or simulators yet.

---

## Prompt 2 — Data Reliability

Implement:
- DataReliabilityCard
- SourceReliabilityTable
- SourceReliabilityDrawer
- Add condensed reliability status to Decision Room

---

## Prompt 3 — Model Disagreement

Implement:
- ModelAgreementCard
- Model comparison table
- Agreement status
- Manual-review warning

---

## Prompt 4 — Counterfactual Simulator

Implement only inside the existing Explainability tab:
- Recommended changes
- Sliders
- Comparison result
- Warning text

---

## Prompt 5 — Stress Testing

Implement only inside the existing Risk Analysis tab:
- Preset scenarios
- Custom scenario form
- Comparison chart
- Decision Room summary

---

## Prompt 6 — Integrity Alerts

Implement:
- Separate credit, fraud, and data-integrity indicators
- Alert cards
- Review actions
- Evidence button

---

## Prompt 7 — Evidence Traceability

Implement:
- EvidenceTraceDrawer
- Trigger buttons from explanation factors, alerts, and policy results

---

## Prompt 8 — Borrower Explanation and Appeal

Implement only in borrower portal:
- Borrower explanation card
- Language toggle
- Correction action
- Reconsideration modal
- Appeal status

---

## Prompt 9 — Enhanced Timeline

Implement:
- Compact timeline
- Full timeline
- New event types
- Existing audit-link integration

---

## Prompt 10 — Final Integration Pass

Check:
- Consistent spacing
- No duplicate cards
- No duplicate routes
- Responsive layout
- Accessibility
- Empty states
- Loading states
- Error states
- Mock-data separation

Do not redesign the application.

---

# 17. Copy-Paste Master Prompt for v0.app

```text
You are extending an existing production-style Next.js, TypeScript, Tailwind CSS, and shadcn/ui application named MyCreditLens.

IMPORTANT:
The complete frontend already exists. Do not rebuild the application, do not create a new dashboard, do not replace the sidebar, do not rename routes, do not change the design system, and do not duplicate existing pages or workflows.

Preserve:
- Existing lender dashboard
- Existing borrower portal
- Existing application detail page
- Existing tabs
- Existing decision modal
- Existing navigation
- Existing colours, typography, spacing, cards, tables, and buttons
- Existing role-based interfaces

Current application detail route:
`/lender/applications/[applicationId]`

Current tabs:
Summary, Financial Data, Risk Analysis, Explainability, Documents, Consent, Analyst Notes, Audit Trail.

For this task, add only the requested enhancement as an incremental component within the existing application.

Technical requirements:
- Next.js App Router
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- Lucide icons
- Recharts when charts are required
- Typed mock data
- Reusable components
- Responsive design
- WCAG-friendly labels and focus states
- Loading, empty, populated, and error states
- No backend implementation
- No API calls
- No alternative UI library
- No redesign of unrelated sections

Use the existing design language:
- Deep navy `#0F172A`
- Action blue `#2563EB`
- Background `#F8FAFC`
- White cards
- Slate borders
- Green/amber/red risk states
- Purple manual-review status
- Inter typography
- 12px card radius
- Restrained enterprise-fintech appearance

Only implement the specific feature described after this instruction.
```

After this master prompt, paste only one enhancement prompt at a time.

---

# 18. Acceptance Criteria

The enhancement work is complete only when:

- Existing routes remain unchanged
- Existing pages still function
- No duplicate navigation is introduced
- New features use the existing design system
- Each feature has typed mock data
- Every card has loading and empty states
- Error states are visible
- Mobile layout is usable
- Decision actions still use the existing decision flow
- Risk, fraud, and data quality remain visually separate
- Counterfactual outputs include a non-guarantee warning
- Borrower views do not expose internal analyst data
- Manual-review reasons are clearly displayed
- Evidence can be traced from factor to source
- Accessibility labels are included
- Components are reusable
- No backend code is generated
- No unrelated page is redesigned

---

# 19. Features Explicitly Excluded From This v0.app Phase

Do not ask v0.app to implement:

- Real model inference
- Training pipelines
- Live SHAP calculation
- Open banking
- Live e-wallet connections
- Real OCR
- Real fraud detection
- Neo4j graph visualisation
- Loan pricing optimisation
- Loan disbursement
- Blockchain
- Real notifications
- Production API integration
- Authentication replacement
- Database design
- Backend services

These belong to backend integration or future development phases.

---

# 20. Final v0.app Strategy

The correct strategy is:

```text
Existing Frontend
      ↓
Add One Isolated Enhancement
      ↓
Review and Merge
      ↓
Add Next Enhancement
      ↓
Final Consistency Pass
```

Do not give v0.app the entire project specification and all improvements in one prompt.

The safest approach is to provide:
1. The master preservation prompt
2. One enhancement section
3. The exact existing page or tab to modify
4. Acceptance criteria for that enhancement

This prevents v0.app from rebuilding the application or generating conflicting layouts.
