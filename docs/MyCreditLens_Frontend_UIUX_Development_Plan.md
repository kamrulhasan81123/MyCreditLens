# MyCreditLens — Frontend UI/UX Development Plan

## 1. Product Overview

**Product name:** MyCreditLens  
**Project type:** Explainable alternative-data microcredit risk platform  
**Primary users:** Credit analysts, lender administrators, compliance reviewers, and borrowers  
**Primary objective:** Allow lenders to onboard thin-file borrowers, ingest alternative financial data, generate explainable risk scores, review applications, and maintain a complete audit trail.

The frontend must feel trustworthy, professional, regulated, and data-driven. It should not look like a crypto dashboard, casual fintech app, or experimental AI product. Every interface should communicate clarity, traceability, caution, and responsible decision-making.

---

## 2. Product Design Principles

### 2.1 Trust Before Visual Excitement
The interface should prioritise credibility over flashy effects. Use clean layouts, restrained colour usage, predictable navigation, clear data labels, and visible decision explanations.

### 2.2 Explain Every Important Decision
Risk scores must never appear without context. Every score should be supported by:
- Risk band
- Probability of default
- Confidence level
- Top positive factors
- Top negative factors
- Data quality indicator
- Model version
- Decision timestamp

### 2.3 Human-in-the-Loop
The system must not visually suggest that AI automatically makes final lending decisions. The analyst must retain control through:
- Approve
- Reject
- Request more information
- Send for manual review
- Override with reason

### 2.4 Progressive Disclosure
Do not show all technical details at once. Present:
1. Summary
2. Key factors
3. Detailed explanation
4. Raw data and model diagnostics

### 2.5 Accessibility
Target WCAG 2.1 AA:
- Minimum 4.5:1 contrast ratio
- Keyboard navigation
- Visible focus states
- Form labels
- Error summaries
- Screen-reader-friendly charts and tables
- Do not use colour as the only risk indicator

---

## 3. Recommended Frontend Technology

- Next.js 15+
- React 19+
- TypeScript
- Tailwind CSS
- shadcn/ui or Radix UI
- React Hook Form
- Zod
- TanStack Query
- TanStack Table
- Recharts or Plotly
- Zustand for lightweight local UI state
- NextAuth/Auth.js or custom JWT session integration
- Lucide Icons
- date-fns
- Playwright
- Vitest
- Storybook

---

## 4. Branding and Visual System

## 4.1 Brand Positioning
MyCreditLens should communicate:
- Financial inclusion
- Responsible AI
- Transparency
- Precision
- Human review
- Compliance readiness

## 4.2 Colour Palette

### Primary
- Deep Navy: `#0F172A`
- Slate Blue: `#1E3A8A`
- Action Blue: `#2563EB`

### Neutral
- Background: `#F8FAFC`
- Surface: `#FFFFFF`
- Border: `#E2E8F0`
- Secondary Text: `#64748B`
- Primary Text: `#0F172A`

### Status Colours
- Low Risk: `#15803D`
- Medium Risk: `#B45309`
- High Risk: `#B91C1C`
- Manual Review: `#6D28D9`
- Information: `#0369A1`

Status colours must always be paired with a label and icon.

## 4.3 Typography

Recommended font:
- Primary: Inter
- Alternative: Manrope
- Monospace for IDs and API keys: JetBrains Mono

### Type Scale
- Display: 36px / 44px
- H1: 30px / 38px
- H2: 24px / 32px
- H3: 20px / 28px
- Body: 16px / 24px
- Small: 14px / 20px
- Caption: 12px / 16px

## 4.4 Border Radius
- Cards: 12px
- Inputs: 8px
- Buttons: 8px
- Modals: 16px
- Pills: 999px

## 4.5 Shadow
Use subtle shadows only:
- Cards: `0 1px 3px rgba(15, 23, 42, 0.08)`
- Modals: `0 20px 50px rgba(15, 23, 42, 0.16)`

---

## 5. Application Roles

### 5.1 Lender Administrator
Can:
- Manage users
- Configure policies
- View all applications
- Manage API settings
- Review model versions
- Access audit logs

### 5.2 Credit Analyst
Can:
- Review applications
- Generate scores
- View explanations
- Approve, reject, or escalate
- Add notes

### 5.3 Compliance Reviewer
Can:
- View decisions
- Review overrides
- Check fairness reports
- View consent records
- Access audit logs

### 5.4 Borrower
Can:
- Create an application
- Provide consent
- Upload documents
- View application status
- Respond to requests for additional information

---

## 6. Global Application Structure

### 6.1 Public Navigation
- Home
- How It Works
- Responsible AI
- For Lenders
- Borrower Portal
- Sign In
- Request Demo

### 6.2 Lender Dashboard Navigation
- Overview
- Applications
- Borrowers
- Risk Analysis
- Portfolio
- Model Monitoring
- Fairness
- Audit Logs
- API & Integrations
- Settings

### 6.3 Borrower Portal Navigation
- Dashboard
- New Application
- Connected Data
- Documents
- Consent
- Messages
- Profile

---

# 7. Public Website Pages

## 7.1 Home Page

### Purpose
Explain the platform clearly and establish trust.

### Sections
1. Hero
2. Problem statement
3. How it works
4. Core capabilities
5. Explainable AI section
6. Financial inclusion impact
7. Security and governance
8. Lender CTA
9. Footer

### Hero Content
**Headline:**  
Explainable credit intelligence for borrowers traditional models overlook.

**Subheadline:**  
Assess thin-file borrowers using alternative financial data, transparent machine learning, and human-controlled underwriting workflows.

### Primary Buttons
- Request a Demo
- Explore the Platform

### Secondary Button
- Borrower Sign In

### UI Notes
- Hero should include a clean dashboard preview
- No exaggerated claims
- Add small trust indicators such as “Consent-based”, “Explainable”, and “Human-reviewed”

---

## 7.2 How It Works Page

### Steps
1. Borrower gives consent
2. Data is uploaded or connected
3. Financial features are generated
4. Risk model produces a score
5. SHAP explanation is generated
6. Analyst reviews the case
7. Final decision is recorded

### Buttons
- View Sample Assessment
- Request Demo

---

## 7.3 Responsible AI Page

### Sections
- Explainability
- Fairness testing
- Data minimisation
- Human oversight
- Model monitoring
- Auditability
- Limitations

### Important UI
Use cards with:
- Principle
- Implementation
- Evidence
- Status

### Buttons
- Read Governance Framework
- Contact Compliance Team

---

## 7.4 For Lenders Page

### Sections
- Use cases
- Workflow benefits
- API integration
- Portfolio monitoring
- Manual review
- Governance
- Deployment options

### Buttons
- Book a Product Demo
- View API Capabilities

---

## 7.5 Sign In Page

### Fields
- Work email
- Password
- Remember me
- MFA code when enabled

### Buttons
- Sign In
- Continue with Organisation SSO
- Forgot Password

### States
- Invalid credentials
- Locked account
- MFA required
- Session expired

---

# 8. Lender Dashboard Pages

## 8.1 Overview Dashboard

### Purpose
Give an operational summary of applications, portfolio quality, and review workload.

### Top KPI Cards
- New Applications
- Pending Review
- Approval Rate
- Average Default Probability
- High-Risk Applications
- Data Quality Alerts

### Main Charts
- Applications over time
- Approval vs rejection
- Risk band distribution
- Default probability distribution
- Applications by borrower segment

### Work Queue
Table columns:
- Application ID
- Borrower
- Segment
- Submitted date
- Risk band
- Data quality
- Assigned analyst
- Status
- Action

### Buttons
- New Assessment
- Export Report
- View All Applications

---

## 8.2 Applications Page

### Filters
- Status
- Risk band
- Date range
- Borrower type
- Assigned analyst
- Data quality
- Model version
- Decision outcome

### Search
Search by:
- Application ID
- Borrower name
- Business name
- Email
- Reference number

### Table Columns
- Application ID
- Borrower
- Borrower type
- Requested amount
- Risk score
- Risk band
- Status
- Submitted
- Analyst
- Last updated

### Row Actions
- Open Application
- Assign Analyst
- Request Information
- Export Assessment
- Archive

### Bulk Actions
- Assign Analyst
- Export CSV
- Change Priority
- Send for Review

---

## 8.3 New Assessment Page

### Step 1: Borrower Information
Fields:
- Full name
- Nationality
- Date of birth
- Occupation category
- Employment type
- Business type
- Monthly income estimate
- Requested loan amount
- Loan purpose

Buttons:
- Save Draft
- Continue

### Step 2: Consent
Consent items:
- Bank statement analysis
- E-wallet transaction analysis
- Utility payment analysis
- Gig income analysis
- POS or marketplace analysis
- Data retention agreement
- Automated risk analysis disclosure

Buttons:
- Download Consent Form
- Record Consent
- Continue

### Step 3: Data Sources
Options:
- Upload CSV
- Upload bank statement
- Upload e-wallet statement
- Upload gig income report
- Upload utility history
- Enter manually

Each source card should show:
- Source type
- Status
- Date range
- File name
- Validation result
- Remove action

Buttons:
- Add Data Source
- Validate Data
- Continue

### Step 4: Data Review
Display:
- Total records
- Missing values
- Duplicate transactions
- Date coverage
- Currency
- Detected anomalies
- Data quality score

Buttons:
- Fix Issues
- Accept and Continue
- Download Validation Report

### Step 5: Generate Score
Display pre-score checklist:
- Consent complete
- Required fields complete
- Data quality threshold passed
- Fraud checks complete
- Policy rules evaluated

Buttons:
- Generate Risk Score
- Save for Later

### Step 6: Results
Display:
- Probability of default
- Risk band
- Confidence
- Recommended action
- Top factors
- Policy rule results
- Model version

Buttons:
- Approve
- Reject
- Manual Review
- Request More Information
- Download Report

---

## 8.4 Application Detail Page

### Header
- Borrower name
- Application ID
- Status badge
- Requested amount
- Submission date
- Assigned analyst
- Priority

### Tabs
- Summary
- Financial Data
- Risk Analysis
- Explainability
- Documents
- Consent
- Analyst Notes
- Audit Trail

### Summary Tab
Cards:
- Borrower profile
- Loan request
- Income summary
- Expense summary
- Data sources
- Data quality
- Current recommendation

### Sticky Decision Panel
Buttons:
- Approve
- Reject
- Send to Manual Review
- Request Information

Every decision action opens a modal requiring:
- Decision reason
- Optional internal note
- Supporting evidence
- Override checkbox if needed

---

## 8.5 Risk Analysis Tab

### Components
- Risk score gauge
- Probability of default
- Risk band badge
- Confidence level
- Policy rule result
- Model version
- Scoring timestamp

### Charts
- Monthly inflow/outflow trend
- Income consistency
- Balance stability
- Utility payment behaviour
- Transaction volatility
- Debt service proxy

### Buttons
- Recalculate Score
- Compare Model Versions
- Export Risk Report

---

## 8.6 Explainability Tab

### Sections
1. Plain-language explanation
2. Top positive factors
3. Top negative factors
4. SHAP waterfall chart
5. Feature contribution table
6. Global model context
7. Explanation limitations

### Feature Table Columns
- Feature
- Borrower value
- Expected range
- Contribution direction
- Contribution strength
- Explanation

### Buttons
- Generate Borrower-Friendly Explanation
- Generate Bahasa Melayu Version
- Download Explanation Report
- Flag Explanation Issue

---

## 8.7 Financial Data Tab

### Sections
- Income
- Expenses
- E-wallet activity
- Utility payments
- Remittances
- Business activity
- Cash-flow trends

### Table Columns
- Date
- Description
- Category
- Amount
- Direction
- Source
- Confidence
- Flag

### Actions
- Edit Category
- Exclude Transaction
- Mark as Anomaly
- Add Analyst Note
- Re-run Features

---

## 8.8 Borrowers Page

### Cards and Table
- Borrower name
- Segment
- Number of applications
- Latest risk band
- Active application
- Last updated

### Buttons
- Add Borrower
- Open Profile
- Start New Assessment
- Export Borrower Data

---

## 8.9 Borrower Profile Page

### Tabs
- Overview
- Applications
- Connected Data
- Documents
- Consent History
- Communication
- Audit Trail

### Overview Cards
- Identity summary
- Employment or business summary
- Historical risk scores
- Previous decisions
- Data quality trend
- Consent status

---

## 8.10 Portfolio Page

### KPI Cards
- Total assessed applications
- Total approved amount
- Approval rate
- Average predicted default
- High-risk exposure
- Manual review rate

### Charts
- Portfolio risk distribution
- Risk by borrower segment
- Approval rate over time
- Predicted default by loan size
- Data quality distribution
- Model version distribution

### Buttons
- Export Portfolio Report
- Compare Periods
- Create Saved View

---

## 8.11 Model Monitoring Page

### Cards
- Active model
- Model version
- Last deployment
- AUC
- Calibration score
- Drift status
- Data freshness

### Charts
- Feature drift
- Prediction drift
- Model performance over time
- Calibration curve
- Segment performance

### Alerts
- Feature drift detected
- Approval-rate shift
- Missing data increase
- Performance degradation
- Unexpected score distribution

### Buttons
- View Model Card
- Compare Versions
- Acknowledge Alert
- Download Monitoring Report

---

## 8.12 Fairness Page

### Metrics
- Approval rate by segment
- False-positive rate
- False-negative rate
- Selection rate
- Disparate impact ratio
- Average score by segment

### Filters
- Model version
- Date range
- Borrower segment
- Decision status

### UI Requirements
- Clear warning that metrics require careful interpretation
- Do not label a model “fair” based on one metric
- Show sample size for each group

### Buttons
- Export Fairness Report
- Compare Model Versions
- Add Review Note

---

## 8.13 Audit Logs Page

### Table Columns
- Timestamp
- User
- Action
- Entity
- Entity ID
- Before
- After
- IP address
- Result

### Filters
- User
- Action type
- Date range
- Application ID
- Model version
- Decision override

### Buttons
- Export Logs
- View Event Detail
- Verify Record Integrity

---

## 8.14 API & Integrations Page

### Sections
- API keys
- Webhooks
- Data source connectors
- Usage
- Error logs
- Documentation

### API Key Card
- Key name
- Created date
- Last used
- Status
- Permissions

### Buttons
- Create API Key
- Revoke Key
- Rotate Key
- Add Webhook
- Test Connection
- View Documentation

---

## 8.15 Settings Page

### Tabs
- Organisation
- Users and Roles
- Lending Policy
- Risk Bands
- Notifications
- Security
- Data Retention
- Branding

### Risk Band Configuration
Fields:
- Low-risk threshold
- Medium-risk threshold
- High-risk threshold
- Manual-review threshold

### Buttons
- Save Changes
- Reset Defaults
- Publish Policy Version

---

# 9. Borrower Portal Pages

## 9.1 Borrower Dashboard

### Cards
- Application status
- Required actions
- Documents submitted
- Connected data sources
- Consent status
- Messages

### Buttons
- Continue Application
- Upload Document
- View Request
- Contact Support

---

## 9.2 New Application

### Steps
1. Personal details
2. Employment or business details
3. Loan request
4. Financial data
5. Consent
6. Review and submit

### UX Requirements
- Progress indicator
- Save draft
- Mobile-first layout
- Inline validation
- Plain-language consent
- Clear explanation of why each data item is needed

---

## 9.3 Connected Data Page

### Data Source Cards
- Bank statement
- E-wallet
- Gig platform
- Utility history
- POS or marketplace
- Remittance history

### Status Labels
- Connected
- Pending
- Failed
- Expired
- Needs attention

### Buttons
- Connect
- Upload
- Reconnect
- Remove
- View Permissions

---

## 9.4 Documents Page

### Supported Documents
- Identity document
- Bank statement
- Utility bill
- Business registration
- Gig income statement
- POS report

### Buttons
- Upload Document
- Replace
- Delete
- Preview

### Upload States
- Uploading
- Processing
- Verified
- Rejected
- Needs clearer copy

---

## 9.5 Consent Page

### Display
- Consent purpose
- Data source
- Granted date
- Expiry date
- Retention period
- Revocation status

### Buttons
- View Consent
- Download Copy
- Revoke Consent
- Renew Consent

Revocation must show its consequences before confirmation.

---

## 9.6 Messages Page

### Features
- Analyst requests
- Missing document notices
- Clarification requests
- Decision notifications

### Buttons
- Reply
- Upload Requested Document
- Mark as Read

---

# 10. Core Reusable Components

- AppShell
- Sidebar
- Topbar
- Breadcrumbs
- KPI Card
- Risk Badge
- Status Badge
- Data Quality Badge
- Probability Gauge
- SHAP Waterfall Chart
- Feature Contribution Table
- Decision Panel
- Audit Timeline
- Data Source Card
- Consent Card
- File Upload
- Stepper
- Empty State
- Error State
- Skeleton Loader
- Confirmation Modal
- Override Modal
- Export Menu
- Filter Drawer
- Saved View Selector
- Activity Timeline
- Notification Center

---

# 11. Button System

## Primary Buttons
Used for the most important action:
- Generate Risk Score
- Approve
- Submit Application
- Save Changes

## Secondary Buttons
Used for supportive actions:
- Export Report
- Request Information
- Compare Versions

## Destructive Buttons
Used for:
- Reject
- Revoke Consent
- Delete Document
- Revoke API Key

## Tertiary Buttons
Used for:
- View Details
- Cancel
- Back
- Open Documentation

## Button Rules
- One dominant primary button per view
- Destructive actions require confirmation
- Decision buttons require a reason
- Buttons must show loading states
- Disable buttons only with visible explanation
- Never use icon-only buttons for critical actions

---

# 12. Form Design Rules

- Label every input
- Add helper text for sensitive fields
- Validate on blur and submit
- Show inline error plus error summary
- Preserve valid values after failed submission
- Use proper input types
- Use masked display for sensitive values
- Allow draft saving
- Confirm before leaving unsaved forms

---

# 13. Notifications

## Toast Notifications
Use for:
- Successful save
- Report generated
- Analyst assigned
- Connection successful

## Inline Alerts
Use for:
- Missing consent
- Poor data quality
- Model drift
- Failed document parsing
- Policy conflicts

## Modal Alerts
Use for:
- Approval
- Rejection
- Overrides
- Consent revocation
- API key deletion

---

# 14. Responsive Behaviour

## Desktop
- Persistent sidebar
- Multi-column dashboards
- Full data tables
- Sticky decision panel

## Tablet
- Collapsible sidebar
- Two-column cards
- Horizontal table scrolling

## Mobile
- Bottom or drawer navigation
- Single-column layouts
- Card-based application summaries
- Sticky bottom actions
- Avoid complex charts where a summary list is clearer

The lender dashboard should be desktop-first. The borrower portal should be mobile-first.

---

# 15. Empty, Error, and Loading States

Every major page must include:

### Empty
- Clear explanation
- Next action
- Example or onboarding hint

### Error
- Human-readable message
- Retry button
- Support reference ID

### Loading
- Skeletons for cards and tables
- Progress indicator for scoring and uploads
- Never display blank screens

---

# 16. Frontend Security Requirements

- Never store raw access tokens in localStorage
- Use secure HTTP-only cookies
- Enforce role-based route protection
- Mask personal and financial data by default
- Add automatic session timeout
- Prevent sensitive data in client logs
- Sanitize rendered AI text
- Apply CSRF protection
- Add Content Security Policy
- Restrict file previews
- Confirm privileged actions

---

# 17. Frontend Testing Plan

## Unit Tests
- Validation schemas
- Risk formatting
- Permission helpers
- Calculation display
- Status mappings

## Component Tests
- Forms
- Decision modals
- Data tables
- Risk badges
- File upload
- Filters

## Integration Tests
- Application creation
- Data upload
- Score generation
- Decision submission
- Consent flow

## End-to-End Tests
- Analyst reviews application
- Borrower submits application
- Admin creates API key
- Compliance reviewer exports audit report

## Accessibility Tests
- Keyboard navigation
- Focus order
- ARIA labels
- Contrast
- Screen-reader output

---

# 18. Recommended Frontend Folder Structure

```text
src/
├── app/
│   ├── (public)/
│   ├── (auth)/
│   ├── lender/
│   ├── borrower/
│   └── api/
├── components/
│   ├── charts/
│   ├── data-display/
│   ├── forms/
│   ├── layout/
│   ├── risk/
│   └── ui/
├── features/
│   ├── applications/
│   ├── borrowers/
│   ├── consent/
│   ├── decisions/
│   ├── explanations/
│   ├── monitoring/
│   └── portfolio/
├── hooks/
├── lib/
├── services/
├── stores/
├── types/
└── tests/
```

---

# 19. Frontend Development Phases

## Phase 1 — Foundation
- Design tokens
- Authentication
- Layout
- Role-based navigation
- Core components

## Phase 2 — Application Workflow
- Application list
- New assessment
- Data upload
- Application detail
- Decision flow

## Phase 3 — Risk and Explainability
- Risk dashboard
- SHAP visualisation
- Factor tables
- Explanation reports

## Phase 4 — Borrower Portal
- Application journey
- Document uploads
- Consent management
- Messaging

## Phase 5 — Administration
- User management
- API keys
- Policies
- Audit logs
- Monitoring

## Phase 6 — Quality
- Responsive design
- Accessibility
- Performance
- E2E testing
- Security hardening

---

# 20. Frontend Definition of Done

A frontend feature is complete only when:
- UI matches the design system
- Loading, empty, success, and error states exist
- Permissions are enforced
- Forms are validated
- Mobile and desktop behaviour are tested
- Accessibility checks pass
- Unit or integration tests exist
- Analytics events are defined
- Sensitive data is masked
- API failures are handled clearly
