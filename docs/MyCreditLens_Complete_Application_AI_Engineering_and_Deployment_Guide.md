# MyCreditLens — Complete Application, AI Engineering, Dataset, Training, and Deployment Specification

**Project:** MyCreditLens  
**Product:** AI-Powered Microcredit Risk Engine for Underbanked and Thin-File Borrowers  
**Document type:** Complete MVP technical specification and implementation handbook  
**Target:** Fully functional final-year project MVP  
**Architecture:** Next.js frontend + FastAPI modular monolith + PostgreSQL + tabular machine learning  
**Primary deployment model:** Dockerised single-environment deployment with optional managed cloud services  
**Last updated:** July 2026

---

# 1. Executive Summary

MyCreditLens is a full-stack credit-assessment platform designed for borrowers who have limited formal credit history but possess alternative evidence of financial behaviour. The system collects consented financial data such as bank transactions, e-wallet activity, utility payments, gig income, point-of-sale activity, marketplace income, and remittances. It transforms these records into structured financial features, applies calibrated credit-risk models, generates explainable predictions, evaluates policy rules, and provides credit analysts with a human-controlled decision workflow.

The product must never be presented as an autonomous lending authority. The machine-learning layer estimates risk and provides supporting evidence. A human analyst retains final responsibility for approval, rejection, information requests, and manual-review decisions.

The final MVP is expected to be functionally complete. Every major frontend page should connect to a real backend capability. However, the MVP does not need enterprise banking certification, live open-banking integrations, high-availability infrastructure, Kubernetes, multi-region replication, or national-scale data.

The most important engineering distinction is:

> MyCreditLens requires a trained tabular credit-risk model, not a newly trained large language model.

Logistic Regression, XGBoost, LightGBM, and Explainable Boosting Machine are appropriate for the primary prediction task. LoRA and QLoRA apply only to an optional language-model component, such as explanation rewriting, transaction-description classification, or Bahasa Melayu generation. They must not be used to calculate probability of default.

---

# 2. Product Goals

## 2.1 Primary Goal

Provide an explainable and auditable credit-risk assessment workflow for thin-file borrowers using alternative financial data.

## 2.2 Secondary Goals

- Improve visibility into irregular-income borrowers.
- Compare interpretable and high-performance tabular models.
- Calculate calibrated probability of default.
- Present data quality and reliability separately from credit risk.
- Detect uncertainty and abstain when the model should not be trusted.
- Generate analyst-facing and borrower-facing explanations.
- Support stress testing and counterfactual scenarios.
- Provide fairness and model-monitoring reports.
- Maintain complete auditability.
- Demonstrate a production-informed but MVP-sized AI engineering workflow.

## 2.3 Non-Goals

The MVP will not:

- Disburse real loans.
- Connect directly to national credit bureaus.
- Perform legally binding lending decisions.
- Claim regulatory certification.
- Replace human underwriting.
- Train a foundation model from scratch.
- Host a large language model at production scale.
- Implement real-time continual learning.
- Guarantee fairness or legal compliance.
- Handle millions of borrowers.

---

# 3. User Roles

## 3.1 Borrower

The borrower can:

- Register and authenticate.
- Create and edit a loan application.
- Provide employment or business information.
- Grant or revoke data-processing consent.
- Upload financial data.
- Review upload and validation results.
- Respond to information requests.
- View application status.
- View a borrower-friendly explanation.
- Correct incorrect information.
- Submit a reconsideration request or appeal.
- Upload supporting appeal documents.

## 3.2 Credit Analyst

The analyst can:

- View assigned and unassigned applications.
- Review borrower profiles.
- Review financial transactions.
- Inspect data reliability.
- Generate or view risk predictions.
- Compare model outputs.
- Review SHAP explanations.
- Run stress tests.
- Run counterfactual simulations.
- Inspect integrity alerts.
- Trace evidence from a model factor to transactions.
- Approve, reject, request information, or assign manual review.
- Override recommendations with a mandatory reason.
- Add internal notes.

## 3.3 Lender Administrator

The administrator can:

- Manage users.
- Manage roles.
- Configure risk thresholds.
- Configure policy rules.
- View portfolio statistics.
- View model versions.
- View monitoring metrics.
- Manage API access.
- Export reports.
- Review system-level audit logs.

## 3.4 Compliance Reviewer

The compliance reviewer can:

- Review decision explanations.
- Inspect fairness reports.
- Review model cards.
- Review analyst overrides.
- Review consent records.
- Inspect audit trails.
- Review model drift and calibration.
- Export governance reports.

---

# 4. Existing Project Status

The repository already contains:

- A Next.js and TypeScript frontend.
- A FastAPI backend.
- Nineteen SQLAlchemy models.
- Authentication, borrower, application, scoring, data-source, decision, appeal, and reporting routers.
- Feature engineering, model training, SHAP, counterfactual, stress testing, fairness, and model-monitoring modules.
- Axios API integration.
- JWT authentication.
- React Query hooks.
- Partial replacement of frontend mock data with backend API data.

The current implementation must be treated as a scaffold until the following have been verified:

1. PostgreSQL is running.
2. Database migrations succeed.
3. API routes work against persisted data.
4. Model artifacts can be trained and loaded.
5. Scoring generates real persisted predictions.
6. SHAP generates real explanations.
7. Frontend pages load actual backend data.
8. Unit, integration, and end-to-end tests pass.

The immediate engineering priority is to make the current vertical slice work before adding infrastructure complexity.

---

# 5. High-Level Architecture

```text
Borrower / Analyst / Admin / Compliance
                  |
                  v
        Next.js Web Application
                  |
            HTTPS REST API
                  |
                  v
        FastAPI Modular Monolith
   --------------------------------
   Auth | Borrowers | Applications
   Consent | Documents | Transactions
   Features | Scoring | Explainability
   Policies | Decisions | Appeals
   Fairness | Monitoring | Audit
   --------------------------------
        |            |            |
        v            v            v
   PostgreSQL   Object Storage   ML Artifacts
        |
        v
   Optional Redis / Background Worker
```

## 5.1 Architecture Principle

Use a modular monolith.

Do not split the MVP into microservices. Microservices would introduce service discovery, distributed authentication, network failure modes, schema coordination, distributed tracing, and increased deployment burden without creating meaningful FYP value.

Modules should have clear boundaries but run inside one FastAPI application.

---

# 6. Frontend Application

## 6.1 Technology

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- React Hook Form
- Zod
- Recharts
- Axios
- JWT or secure session cookies

## 6.2 Public Pages

### Home

Explains the problem, alternative-data underwriting, explainability, human oversight, security, and consent.

### How It Works

Displays:

1. Borrower onboarding.
2. Consent.
3. Data upload.
4. Data processing.
5. Risk scoring.
6. Analyst review.
7. Decision explanation.

### Responsible AI

Explains human control, fairness evaluation, explainability, model limitations, auditability, data minimisation, and consent.

### For Lenders

Explains the lender workflow, Decision Room, API integration, monitoring, and reporting.

### Sign In

Supports email and password, role-aware redirect, token refresh, error handling, and session expiry.

---

# 7. Borrower Portal

## 7.1 Borrower Dashboard

Displays application status, current action required, uploaded documents, data-source status, consent status, messages, and appeal status.

## 7.2 New Application Workflow

### Step 1: Personal Profile

- Full name
- Date of birth
- Nationality
- Occupation
- Employment type
- Borrower segment

### Step 2: Employment or Business

Employment fields:

- Employer
- Job title
- Monthly income
- Employment start date
- Income frequency

Business fields:

- Business type
- Industry
- Start date
- Monthly revenue
- Employee count

### Step 3: Loan Request

- Requested amount
- Currency
- Purpose
- Repayment period

### Step 4: Consent

Each consent must include purpose, data source, version, granted date, expiry, retention period, and revocation option.

### Step 5: Upload

Supported MVP sources:

- CSV
- XLSX
- Manual transaction entry
- Basic PDF statement upload
- Utility-payment history
- Gig-income export
- POS export
- Remittance records

### Step 6: Review and Submit

Display application summary, data sources, missing information, consent status, and confirmation.

---

# 8. Lender Portal

## 8.1 Overview Dashboard

Metrics:

- Total applications
- New applications
- Pending review
- Approval rate
- Rejection rate
- Manual-review rate
- Average probability of default
- Risk-band distribution
- Data-quality alerts
- Recent activity

## 8.2 Applications

Functions:

- Search
- Filter
- Sort
- Pagination
- Assignment
- Status update
- Export
- Open application

Filters:

- Status
- Risk band
- Analyst
- Date range
- Borrower segment
- Data reliability
- Model version

## 8.3 Decision Room

The Decision Room is the primary analyst interface.

It should show:

- Borrower summary
- Loan request
- Probability of default
- Risk band
- Prediction confidence
- Data reliability
- Model agreement
- Manual-review reasons
- Top positive SHAP factors
- Top negative SHAP factors
- Fraud risk
- Data-integrity risk
- Stress-test summary
- Counterfactual summary
- Policy result
- Analyst notes
- Evidence checklist
- Decision controls

Decision actions:

- Approve
- Reject
- Request information
- Manual review
- Override

Every decision requires a decision reason, prediction reference, policy reference, analyst identity, timestamp, and override reason where applicable.

---

# 9. Backend Modules

## 9.1 Authentication

Responsibilities:

- Registration
- Login
- Password hashing
- JWT issuance
- Token validation
- Current-user lookup
- Role enforcement
- Organisation isolation

Recommended:

- Argon2id for passwords
- Short-lived access token
- Longer refresh token
- Secure HTTP-only cookies where possible

## 9.2 Borrower Service

- Create borrower
- Update borrower
- Retrieve borrower
- Borrower search
- Borrower history
- Employment profile
- Business profile

## 9.3 Application Service

- Create draft
- Update draft
- Submit application
- Assign analyst
- Validate status transitions
- Track application timeline
- Archive application

## 9.4 Consent Service

- Create consent
- Validate consent
- Revoke consent
- Enforce consent before processing
- Store consent version
- Record expiry

## 9.5 Data Source Service

- Accept file upload
- Validate format
- Generate file hash
- Detect duplicate files
- Parse data
- Produce validation report
- Calculate source reliability
- Store source metadata

## 9.6 Transaction Service

- Normalise transaction format
- Validate date
- Validate amount
- Determine direction
- Categorise description
- Flag anomalies
- Support analyst correction
- Support exclusion

## 9.7 Feature Engineering Service

- Aggregate transactions
- Calculate borrower features
- Version feature definitions
- Store feature lineage
- Recalculate features after corrections

## 9.8 Scoring Service

- Load active model artifacts
- Apply preprocessing
- Generate predictions
- Calibrate probability
- Assign risk band
- Calculate model agreement
- Detect uncertainty
- Store prediction
- Trigger explanation generation

## 9.9 Explainability Service

- Calculate SHAP values
- Rank contributing features
- Map feature contributions to reason codes
- Generate analyst explanation
- Generate borrower-safe explanation
- Link features to source evidence

## 9.10 Policy Service

- Evaluate rules
- Version policies
- Produce recommended action
- Produce manual-review reasons
- Store rule results

## 9.11 Decision Service

- Record analyst action
- Validate role
- Require reason
- Require override justification
- Update status
- Create audit record
- Create borrower notification

## 9.12 Appeal Service

- Create appeal
- Attach documents
- Assign reviewer
- Update status
- Record resolution
- Maintain appeal timeline

## 9.13 Fairness Service

- Calculate segment metrics
- Compare approval and error rates
- Store fairness reports
- Display sample sizes and limitations

## 9.14 Monitoring Service

- Prediction distribution
- Risk-band distribution
- Feature missingness
- Basic drift
- Calibration
- Model usage
- Data-quality trends

## 9.15 Audit Service

- Record important state changes
- Store before and after data
- Record user and timestamp
- Support filtering
- Support report export

---

# 10. Core Database Entities

The central entities are:

- User
- Borrower
- Application
- Consent
- DataSource
- Transaction
- EngineeredFeature
- MLModel
- Prediction
- Explanation
- Policy
- Decision
- Appeal
- IntegrityAlert
- AuditLog
- Report
- Fairness
- Monitoring
- Notification

## 10.1 Key Relationships

```text
Organisation 1 -> many Users
Organisation 1 -> many Borrowers
Borrower 1 -> many Applications
Application 1 -> many DataSources
DataSource 1 -> many Transactions
Application 1 -> many EngineeredFeatures
Application 1 -> many Predictions
Model 1 -> many Predictions
Prediction 1 -> many Explanations
Application 1 -> many Decisions
Application 1 -> many Appeals
Application 1 -> many AuditLogs
```

## 10.2 Data-Retention Principle

For the MVP:

- Support soft deletion.
- Mark records inactive.
- Anonymise identifying fields where required.
- Preserve decision evidence.
- Preserve audit logs.
- Document retention assumptions.

---

# 11. API Design

Base URL:

```text
/api/v1
```

## 11.1 Authentication

```text
POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET  /auth/me
```

## 11.2 Borrowers

```text
POST   /borrowers
GET    /borrowers
GET    /borrowers/{borrower_id}
PATCH  /borrowers/{borrower_id}
DELETE /borrowers/{borrower_id}
```

## 11.3 Applications

```text
POST  /applications
GET   /applications
GET   /applications/{application_id}
PATCH /applications/{application_id}
POST  /applications/{application_id}/submit
POST  /applications/{application_id}/assign
GET   /applications/{application_id}/timeline
```

## 11.4 Consent

```text
POST /applications/{application_id}/consents
GET  /applications/{application_id}/consents
POST /consents/{consent_id}/revoke
```

## 11.5 Data Sources

```text
POST   /applications/{application_id}/data-sources
GET    /applications/{application_id}/data-sources
GET    /data-sources/{data_source_id}
DELETE /data-sources/{data_source_id}
POST   /data-sources/{data_source_id}/validate
POST   /data-sources/{data_source_id}/reprocess
```

## 11.6 Transactions

```text
GET   /applications/{application_id}/transactions
PATCH /transactions/{transaction_id}
POST  /transactions/{transaction_id}/exclude
POST  /transactions/{transaction_id}/flag
```

## 11.7 Features

```text
POST /applications/{application_id}/features/generate
GET  /applications/{application_id}/features
GET  /features/{feature_id}/evidence
```

## 11.8 Scoring

```text
POST /applications/{application_id}/score
GET  /applications/{application_id}/predictions
GET  /predictions/{prediction_id}
```

## 11.9 Explainability

```text
GET  /predictions/{prediction_id}/explanations
GET  /predictions/{prediction_id}/shap
POST /predictions/{prediction_id}/borrower-explanation
GET  /predictions/{prediction_id}/evidence
```

## 11.10 Stress Testing

```text
POST /applications/{application_id}/stress-tests
GET  /applications/{application_id}/stress-tests
```

## 11.11 Counterfactuals

```text
POST /applications/{application_id}/counterfactuals
GET  /applications/{application_id}/counterfactuals
```

## 11.12 Integrity

```text
GET  /applications/{application_id}/integrity-alerts
POST /integrity-alerts/{alert_id}/review
POST /integrity-alerts/{alert_id}/dismiss
POST /integrity-alerts/{alert_id}/escalate
```

## 11.13 Decisions

```text
POST /applications/{application_id}/decisions
GET  /applications/{application_id}/decisions
```

## 11.14 Appeals

```text
POST  /applications/{application_id}/appeals
GET   /applications/{application_id}/appeals
GET   /appeals/{appeal_id}
PATCH /appeals/{appeal_id}
POST  /appeals/{appeal_id}/documents
```

## 11.15 Fairness

```text
POST /fairness/evaluate
GET  /fairness/reports
GET  /fairness/reports/{report_id}
```

## 11.16 Monitoring

```text
GET /monitoring/overview
GET /monitoring/models
GET /monitoring/drift
GET /monitoring/calibration
```

## 11.17 Audit

```text
GET /audit-logs
GET /audit-logs/{audit_id}
```

## 11.18 Reports

```text
POST /reports/application/{application_id}
POST /reports/portfolio
GET  /reports/{report_id}
```

---

# 12. End-to-End Application Workflow

## 12.1 Borrower Onboarding

1. Borrower registers.
2. User account is created.
3. Borrower profile is created.
4. Borrower chooses employment or business path.
5. Borrower creates a draft application.
6. Borrower provides requested loan information.

## 12.2 Consent

1. System presents consent purposes.
2. Borrower selects data sources.
3. Consent records are stored.
4. Consent version and timestamp are stored.
5. Upload is blocked if required consent is missing.

## 12.3 Data Upload

1. File is uploaded.
2. File hash is generated.
3. Duplicate check runs.
4. Format is validated.
5. Parser extracts records.
6. Records are normalised.
7. Validation issues are generated.
8. Source reliability is calculated.
9. Borrower or analyst corrects invalid records.

## 12.4 Feature Engineering

1. Transactions are categorised.
2. Monthly aggregates are created.
3. Financial-behaviour features are calculated.
4. Data-quality features are calculated.
5. Feature lineage is stored.
6. Feature version is recorded.

## 12.5 Scoring

1. Active model version is loaded.
2. Features are ordered according to schema.
3. Preprocessing is applied.
4. Probability is predicted.
5. Probability is calibrated.
6. Risk band is assigned.
7. Additional models generate comparison predictions.
8. Agreement is calculated.
9. OOD detection runs.
10. Manual-review rules are evaluated.
11. Prediction is stored.

## 12.6 Explanation

1. SHAP explains the selected prediction.
2. Top factors are ranked.
3. Reason codes are generated.
4. Evidence links are created.
5. Analyst-facing text is generated.
6. Borrower-safe explanation is generated.
7. Internal-only information is excluded from borrower output.

## 12.7 Policy Evaluation

Rules evaluate consent, data reliability, probability threshold, model disagreement, OOD flag, integrity alerts, requested amount, and missing critical data.

## 12.8 Analyst Review

The analyst reviews the application, financial summary, risk score, explanation, policy result, alerts, evidence, stress tests, and counterfactuals.

The analyst chooses approve, reject, request information, or manual review.

## 12.9 Borrower Explanation and Appeal

1. Borrower receives status.
2. Borrower sees plain-language factors.
3. Borrower can correct information.
4. Borrower can request reconsideration.
5. Appeal is assigned.
6. Reviewer resolves appeal.
7. Timeline and audit logs are updated.

---

# 13. Dataset Strategy

Dataset quality is the main technical constraint in this project.

A credit-risk model requires labelled outcomes:

```text
Input features at decision time -> repayment or default outcome
```

Without repayment labels, the model cannot learn probability of default.

## 13.1 Recommended Dataset Hierarchy

### Tier 1 — Public Labelled Credit Dataset

Recommended sources:

1. Home Credit Default Risk
2. UCI Default of Credit Card Clients
3. UCI South German Credit
4. UCI Statlog German Credit
5. Other public consumer-loan datasets with documented labels

The Home Credit dataset is the strongest candidate for the main training pipeline because it contains application-level and historical credit information and a labelled target.

Limitations:

- It is not Malaysian.
- It is not primarily e-wallet or gig-worker data.
- It contains conventional lending features.
- It cannot establish Malaysian real-world validity.

### Tier 2 — Malaysian Context Data

Use Malaysian open data to calibrate synthetic feature ranges and project context.

Useful sources include:

- OpenDOSM household-income statistics.
- State-level income and expenditure data.
- District-level income summaries.
- Labour-force and self-employment statistics.
- Poverty and household-expenditure summaries.

These datasets are useful for income ranges, regional distributions, household expenditure assumptions, segment simulation, and contextual reporting.

They generally do not contain individual borrower default labels.

### Tier 3 — Synthetic Alternative-Data Layer

Generate synthetic variables that represent:

- E-wallet inflows.
- Gig-income regularity.
- Utility-payment timing.
- POS sales.
- Remittance frequency.
- Liquidity buffer.
- Cash-flow volatility.
- Missing periods.
- Data-reliability signals.

Synthetic data must not be described as real borrower data.

### Tier 4 — Small Primary Research Dataset

For stronger academic value, collect a small consented survey dataset.

Possible participants:

- Gig workers.
- Small shop owners.
- Online sellers.
- Students with part-time income.
- Micro-entrepreneurs.

Collect:

- Income range.
- Income frequency.
- Expense range.
- Payment regularity.
- E-wallet usage.
- Utility-payment behaviour.
- Existing loan history.
- Self-reported missed-payment history.

Do not collect bank passwords, full account numbers, unredacted identity documents, or sensitive personal attributes without ethics approval.

A survey dataset can validate feature realism but usually cannot replace a lender dataset with verified repayment outcomes.

### Tier 5 — Industry Partnership

The ideal future source is an anonymised dataset from a microfinance institution, fintech lender, cooperative, BNPL provider, gig platform, or merchant-payment provider.

Required fields:

- Borrower identifier.
- Application date.
- Decision-time features.
- Loan amount.
- Repayment schedule.
- Default definition.
- Outcome.
- Observation window.

This is the only route to strong Malaysian predictive validity.

---

# 14. Dataset Construction Plan

## 14.1 Define the Unit of Observation

One row should represent one credit application at the moment the lending decision was made.

Do not mix future information into the row.

## 14.2 Define the Target

Example:

```text
default_90d = 1
if repayment is more than 30 days past due within 90 days after disbursement
else 0
```

Choose one definition and document it.

## 14.3 Point-in-Time Correctness

For application date \(t\), only use data available at or before \(t\).

Incorrect:

- Using repayment behaviour after approval as a training feature.
- Using future account balance.
- Using final collection outcome.

Correct:

- Transaction history before application.
- Existing obligations known at application time.
- Historical utility payments.
- Declared income at application time.

## 14.4 Synthetic Feature Generation

A practical hybrid dataset can be created by:

1. Starting with a public labelled credit dataset.
2. Mapping existing variables to borrower profiles.
3. Generating synthetic transaction histories.
4. Deriving alternative-data features.
5. Preserving the original target label.
6. Adding noise and missingness.
7. Documenting assumptions.

Example income generation:

\[
I_i \sim \text{LogNormal}(\mu_s, \sigma_s)
\]

Monthly income:

\[
I_{i,t} = I_i(1 + \epsilon_{i,t} + S_{i,t})
\]

Utility-payment timeliness:

\[
U_i \sim \text{Beta}(\alpha_s, \beta_s)
\]

Liquidity buffer:

\[
L_i = \frac{\text{median balance}}{\text{average monthly essential expense}}
\]

Synthetic default relationships may be added only if the original dataset does not contain a target. A fully synthetic target should be treated as simulation, not genuine model evidence.

---

# 15. Data Schema

## 15.1 Application-Level Data

- Borrower ID
- Application ID
- Application date
- Requested amount
- Repayment period
- Loan purpose
- Employment type
- Borrower segment

## 15.2 Transaction Data

- Transaction ID
- Source
- Timestamp
- Description
- Amount
- Currency
- Direction
- Balance
- Category
- Confidence
- Exclusion flag

## 15.3 Outcome Data

- Loan ID
- Disbursement date
- Scheduled due dates
- Payment dates
- Payment amounts
- Days past due
- Default label
- Observation window

## 15.4 Metadata

- Source system
- Extraction method
- Consent status
- Upload timestamp
- File hash
- Reliability score

---

# 16. Data Cleaning

## 16.1 Duplicate Removal

Detect duplicates using transaction ID, date, amount, description, source, and file hash.

## 16.2 Missing Values

Treat missingness as information.

Strategies:

- Median imputation for continuous variables.
- Most-frequent category for low-risk categoricals.
- Explicit `UNKNOWN` category.
- Missing-indicator feature.
- Model-native missing handling for LightGBM/XGBoost.

## 16.3 Outliers

Do not remove outliers automatically.

Use:

- Winsorisation.
- Log transforms.
- Robust scaling.
- Domain thresholds.
- Separate anomaly flags.

## 16.4 Currency

For the MVP:

- Require MYR or one selected currency.
- Store original currency.
- Store conversion rate.
- Store converted amount.

## 16.5 Dates

Normalise time zone, date format, monthly periods, and observation windows.

---

# 17. Feature Engineering

## 17.1 Income Features

### Average Monthly Income

\[
\bar{I} = \frac{1}{T}\sum_{t=1}^{T} I_t
\]

### Median Monthly Income

\[
\tilde{I} = \text{median}(I_1,\ldots,I_T)
\]

### Income Volatility

\[
V_I = \frac{\sigma(I_t)}{\bar{I} + \epsilon}
\]

### Income Consistency

\[
C_I = 1 - \min(V_I, 1)
\]

### Income Source Concentration

\[
H_I = \sum_{j=1}^{m} p_j^2
\]

## 17.2 Expense Features

### Average Monthly Expense

\[
\bar{E} = \frac{1}{T}\sum_{t=1}^{T} E_t
\]

### Expense Volatility

\[
V_E = \frac{\sigma(E_t)}{\bar{E} + \epsilon}
\]

### Essential Expense Ratio

\[
R_{\text{essential}} =
\frac{\text{essential expenses}}{\text{total expenses} + \epsilon}
\]

## 17.3 Cash-Flow Features

### Net Cash Flow

\[
NCF_t = I_t - E_t
\]

### Cash-In to Cash-Out Ratio

\[
R_{io} =
\frac{\sum \text{cash inflow}}{\sum \text{cash outflow} + \epsilon}
\]

### Liquidity Buffer

\[
L =
\frac{\text{median balance}}{\text{average essential monthly expense} + \epsilon}
\]

### Negative-Balance Frequency

\[
F_{neg} =
\frac{\#\{\text{days balance}<0\}}{\#\{\text{observed days}\}}
\]

## 17.4 Payment Features

### Utility Timeliness

\[
U =
\frac{\text{on-time utility payments}}{\text{total utility payments}}
\]

### Missed-Payment Ratio

\[
M =
\frac{\text{missed or late payments}}{\text{scheduled payments}}
\]

## 17.5 Remittance Features

- Mean remittance
- Standard deviation
- Frequency
- Longest gap
- Dependency ratio

\[
R_{dep} =
\frac{\text{remittance inflow}}{\text{total inflow} + \epsilon}
\]

## 17.6 Business Features

- Monthly POS turnover
- Sales trend
- Revenue seasonality
- Active sales days
- Customer concentration
- Refund ratio

Sales trend:

\[
Sales_t = \beta_0 + \beta_1 t + \epsilon_t
\]

## 17.7 Gig Worker Features

- Active working days
- Weekly income variance
- Platform concentration
- Weekend dependency
- Longest inactivity period
- Earnings trend

## 17.8 Data Reliability Features

A simple weighted score:

\[
R = 0.30C + 0.25M + 0.20E + 0.15D + 0.10V
\]

where:

- \(C\): date coverage
- \(M\): completeness
- \(E\): extraction confidence
- \(D\): duplicate-free rate
- \(V\): validation pass rate

This is a project-designed reliability measure, not a universal financial standard.

---

# 18. Train, Validation, and Test Splits

## 18.1 Preferred Time Split

Use:

- Training: oldest 70%
- Validation: next 15%
- Test: latest 15%

## 18.2 Borrower-Level Grouping

The same borrower must not appear in more than one split.

## 18.3 Cross-Validation

- Stratified K-fold for static public datasets.
- GroupKFold if borrowers repeat.
- TimeSeriesSplit for time-ordered data.

## 18.4 Leakage Checks

Check future transaction data, outcome-derived fields, collection activity, post-decision repayment, IDs that encode outcome, and application status after decision.

---

# 19. Mathematical Model Foundations

## 19.1 Logistic Regression

\[
P(y=1|x) = \sigma(z)
\]

where:

\[
z = \beta_0 + \sum_{j=1}^{p}\beta_j x_j
\]

and:

\[
\sigma(z) = \frac{1}{1+e^{-z}}
\]

Binary cross-entropy:

\[
\mathcal{L} =
-\frac{1}{N}
\sum_{i=1}^{N}
\left[
y_i\log(\hat{p}_i)
+
(1-y_i)\log(1-\hat{p}_i)
\right]
\]

Regularised objective:

\[
\mathcal{L}_{reg}
=
\mathcal{L}
+
\lambda\|\beta\|_2^2
\]

Why use it:

- Strong baseline.
- Interpretable coefficients.
- Stable.
- Easy to calibrate.
- Useful for governance comparison.

## 19.2 Decision Trees

Gini impurity:

\[
G = 1 - \sum_{k=1}^{K}p_k^2
\]

## 19.3 Random Forest

\[
\hat{p}(x)
=
\frac{1}{B}
\sum_{b=1}^{B}
\hat{p}_b(x)
\]

## 19.4 Gradient Boosting

\[
F_M(x) = F_0(x) + \sum_{m=1}^{M}\eta h_m(x)
\]

XGBoost objective:

\[
\mathcal{L}^{(t)}
=
\sum_i l(y_i,\hat{y}_i^{(t-1)} + f_t(x_i))
+
\Omega(f_t)
\]

with:

\[
\Omega(f)
=
\gamma T
+
\frac{1}{2}\lambda\|w\|^2
\]

## 19.5 Explainable Boosting Machine

\[
g(E[y]) =
\beta_0
+
\sum_j f_j(x_j)
+
\sum_{i<j}f_{ij}(x_i,x_j)
\]

---

# 20. Class Imbalance

## 20.1 Class Weighting

\[
\mathcal{L}
=
-\sum_i w_{y_i}
\left[
y_i\log(\hat p_i)
+
(1-y_i)\log(1-\hat p_i)
\right]
\]

## 20.2 Resampling

- Random undersampling
- Random oversampling
- SMOTE

SMOTE must be used only inside training folds.

## 20.3 Threshold Tuning

Default threshold 0.5 is rarely optimal.

Select threshold based on recall, precision, expected cost, and manual-review capacity.

---

# 21. Evaluation Metrics

## 21.1 Precision

\[
Precision =
\frac{TP}{TP+FP}
\]

## 21.2 Recall

\[
Recall =
\frac{TP}{TP+FN}
\]

## 21.3 F1

\[
F1 =
2\frac{Precision \cdot Recall}{Precision + Recall}
\]

## 21.4 Brier Score

\[
BS =
\frac{1}{N}
\sum_{i=1}^{N}
(\hat p_i-y_i)^2
\]

## 21.5 Log Loss

\[
-\frac{1}{N}
\sum_i
[y_i\log(\hat p_i)+(1-y_i)\log(1-\hat p_i)]
\]

## 21.6 KS Statistic

\[
KS =
\max_t
|F_0(t)-F_1(t)|
\]

Also evaluate ROC-AUC, PR-AUC, calibration curves, confusion matrices, and segment-level metrics.

---

# 22. Probability Calibration

## 22.1 Platt Scaling

\[
P(y=1|s)
=
\frac{1}{1+\exp(As+B)}
\]

## 22.2 Isotonic Regression

Fits a non-decreasing function.

Calibration must be fit only on validation data.

---

# 23. Model Selection Framework

Do not select a model by ROC-AUC alone.

Recommended score:

```text
35% discrimination
25% calibration
20% fairness
20% explainability and operational stability
```

Recommended final design:

- Logistic Regression as governance baseline.
- XGBoost or LightGBM as performance model.
- EBM as interpretability challenger.

---

# 24. SHAP Explainability

For a prediction:

\[
f(x) =
\phi_0 + \sum_{j=1}^{p}\phi_j
\]

Store:

- Feature name
- Feature value
- SHAP value
- Direction
- Rank
- Reason code

Example:

```text
income_volatility
value: 0.34
SHAP: +0.092
reason: HIGH_INCOME_VOLATILITY
```

The LLM must not invent explanation factors. It may only rewrite approved deterministic reason codes.

---

# 25. Counterfactual Explanations

A counterfactual seeks a nearby input \(x'\) such that:

\[
f(x') \neq f(x)
\]

while minimising:

\[
\min_{x'}
\lambda_1 d(x,x')
+
\lambda_2 \mathcal{L}(f(x'),y_{target})
+
\lambda_3 C(x')
\]

Mutable features:

- Requested amount
- Income volatility
- Liquidity buffer
- Expense ratio
- Utility timeliness

Immutable features must not be recommended for change.

For the MVP, constrained search is sufficient.

---

# 26. Stress Testing

Examples:

\[
I'_t = 0.8I_t
\]

for a 20% income reduction.

\[
E'_t = 1.15E_t
\]

for a 15% expense increase.

The system recalculates features, probability, risk band, and manual-review status.

Stress testing is not retraining.

---

# 27. Model Agreement and Uncertainty

Given model probabilities:

\[
p_1,p_2,\ldots,p_M
\]

Prediction spread:

\[
S = \max(p_m)-\min(p_m)
\]

Standard deviation:

\[
\sigma_p =
\sqrt{
\frac{1}{M}
\sum_m(p_m-\bar p)^2
}
\]

Example rules:

- High agreement: \(S \leq 0.05\)
- Moderate: \(0.05 < S \leq 0.12\)
- Low: \(S > 0.12\)

Low agreement triggers manual review.

---

# 28. Out-of-Distribution Detection

## 28.1 Range Checks

Flag features outside training percentiles.

## 28.2 Isolation Forest

Use anomaly score to identify unusual points.

## 28.3 Mahalanobis Distance

\[
D_M(x)
=
\sqrt{
(x-\mu)^T
\Sigma^{-1}
(x-\mu)
}
\]

Output:

- In distribution
- Moderately unfamiliar
- Outside model coverage

---

# 29. Fraud and Data Integrity

Fraud risk must remain separate from credit risk.

Rules:

- Duplicate file hash
- Duplicate transaction IDs
- Repeated identical transactions
- Declared income mismatch
- Missing periods
- Large unexplained deposit
- Conflicting employer information
- Modified document metadata

Outputs:

```text
Credit Risk: Medium
Fraud Risk: Low
Data Integrity Risk: Elevated
Data Reliability: 72%
```

---

# 30. Fairness Engineering

## 30.1 Selection Rate

\[
SR_g =
\frac{\#\text{approved in group }g}
{\#\text{applications in group }g}
\]

## 30.2 Demographic Parity Difference

\[
DPD = SR_a-SR_b
\]

## 30.3 Disparate Impact Ratio

\[
DIR =
\frac{SR_{protected}}{SR_{reference}}
\]

Also calculate equal-opportunity difference and false-positive-rate difference.

Rules:

- Always show sample size.
- Do not claim fairness based on one metric.
- Separate model fairness from analyst-decision fairness.
- Sensitive attributes should be used for auditing, not necessarily scoring.
- Synthetic groups must be labelled as synthetic.

---

# 31. LLM, Fine-Tuning, LoRA, and QLoRA

## 31.1 Core Decision

LoRA and QLoRA are not required for the core credit-risk engine.

Using QLoRA for probability of default would be the wrong architecture because transaction features are structured, tabular boosting models are more efficient, calibration is easier, explainability is stronger, data volume is insufficient, and LLM outputs are not deterministic enough for underwriting.

## 31.2 Appropriate LLM Tasks

- Explanation rewriting
- Bahasa Melayu translation
- Transaction-description classification
- Document summarisation
- Analyst question answering

## 31.3 Prompt-Only Baseline

Before fine-tuning:

1. Select an instruction-tuned open model.
2. Use structured prompts.
3. Provide approved reason codes.
4. Validate JSON output.
5. Measure hallucination rate.

## 31.4 Retrieval-Augmented Generation

Use RAG for policy manuals, feature dictionary, model card, explanation templates, and product documentation.

Do not use RAG to calculate risk.

## 31.5 LoRA Mathematics

A pretrained weight matrix:

\[
W_0 \in \mathbb{R}^{d \times k}
\]

is frozen.

The update is:

\[
\Delta W = BA
\]

where:

\[
B \in \mathbb{R}^{d \times r},
\quad
A \in \mathbb{R}^{r \times k}
\]

and:

\[
r \ll \min(d,k)
\]

The adapted output:

\[
h = W_0x + \frac{\alpha}{r}BAx
\]

Only \(A\) and \(B\) are trained.

## 31.6 QLoRA

QLoRA:

- Quantises frozen base-model weights to 4-bit.
- Trains LoRA adapters.
- Reduces memory usage.
- Preserves a larger model on limited hardware.

## 31.7 When to Use LoRA

Use LoRA when the base model fits in memory, you have high-quality supervised examples, and prompting is insufficient.

## 31.8 When to Use QLoRA

Use QLoRA when the base model does not fit in full precision, you want to tune a 3B–8B model on a consumer GPU, and you can validate quantised inference.

## 31.9 Optional Fine-Tuning Dataset

Example:

```json
{
  "instruction": "Rewrite the approved credit explanation in plain Bahasa Melayu.",
  "input": {
    "decision": "MANUAL_REVIEW",
    "reason_codes": [
      "HIGH_INCOME_VOLATILITY",
      "LOW_LIQUIDITY_BUFFER"
    ]
  },
  "output": "Permohonan ini memerlukan semakan lanjut kerana pendapatan bulanan berubah dengan ketara dan simpanan tunai semasa adalah terhad."
}
```

Dataset requirements:

- 1,000–5,000 high-quality examples for an FYP experiment.
- Human review.
- No raw personal data.
- Balanced reason-code coverage.
- Train, validation, and test split.
- English and Bahasa Melayu evaluation.

## 31.10 Suggested LoRA Configuration

For a 3B–8B model:

```text
rank r: 8 or 16
alpha: 16 or 32
dropout: 0.05
learning rate: 1e-4 to 2e-4
epochs: 2 to 4
batch size: based on VRAM
gradient accumulation: 4 to 16
target modules: attention projection layers
```

These are starting values, not guaranteed optimal settings.

## 31.11 LLM Evaluation

Measure:

- Exact reason-code preservation
- Unsupported-claim rate
- Bahasa Melayu quality
- Readability
- JSON validity
- Latency
- Human preference
- Sensitive-data leakage

A fine-tuned LLM should not be deployed unless it performs better than templates and prompt-only baselines.

---

# 32. Model Training Pipeline

## 32.1 Repository Structure

```text
backend/
├── app/
│   ├── ai/
│   ├── services/
│   ├── routers/
│   └── models/
├── ml/
│   ├── data/
│   │   ├── raw/
│   │   ├── interim/
│   │   └── processed/
│   ├── features/
│   ├── training/
│   │   ├── train_logistic.py
│   │   ├── train_xgboost.py
│   │   ├── train_ebm.py
│   │   ├── calibrate.py
│   │   ├── evaluate.py
│   │   └── select_model.py
│   ├── inference/
│   ├── explainability/
│   ├── monitoring/
│   └── artifacts/
│       ├── preprocessor.joblib
│       ├── model.joblib
│       ├── calibrator.joblib
│       ├── explainer.joblib
│       ├── feature_schema.json
│       └── model_card.md
```

## 32.2 Reproducibility

Store random seed, dataset hash, Git commit, feature version, model parameters, package versions, split definition, metrics, and artifact checksum.

## 32.3 Training Steps

1. Download dataset.
2. Verify licence.
3. Create data dictionary.
4. Define target.
5. Remove leakage.
6. Split dataset.
7. Fit preprocessing on training data only.
8. Train Logistic Regression.
9. Train XGBoost.
10. Train EBM.
11. Tune hyperparameters.
12. Calibrate probabilities.
13. Evaluate test data once.
14. Run SHAP.
15. Run fairness analysis.
16. Generate model card.
17. Save artifacts.
18. Register active model.
19. Load artifacts in FastAPI.
20. Run inference tests.

---

# 33. Hyperparameter Tuning

## 33.1 Logistic Regression

Tune:

- `C`
- penalty
- class weight

## 33.2 XGBoost

Tune:

- `n_estimators`
- `max_depth`
- `learning_rate`
- `min_child_weight`
- `subsample`
- `colsample_bytree`
- `reg_alpha`
- `reg_lambda`
- `scale_pos_weight`

## 33.3 Tuning Strategy

Use random search for baseline, Optuna for advanced tuning, cross-validation, early stopping, and a fixed evaluation metric.

Do not tune on test data.

---

# 34. Model Artifact Contract

The FastAPI scoring service should load:

- Preprocessor
- Model
- Calibrator
- Feature schema
- Risk thresholds
- Model metadata
- SHAP explainer

Example metadata:

```json
{
  "model_name": "xgboost_credit_risk",
  "version": "1.0.0",
  "target": "default_90d",
  "training_dataset": "home_credit_hybrid_v1",
  "feature_version": "1.0.0",
  "created_at": "2026-07-06",
  "roc_auc": 0.78,
  "pr_auc": 0.31,
  "brier_score": 0.14
}
```

---

# 35. Inference Design

Training and inference must be separate.

Correct:

```text
Offline training
-> saved artifacts
-> FastAPI loads artifacts at startup
-> requests perform inference
```

Incorrect:

```text
FastAPI startup
-> retrain model
```

Inference must validate feature names, feature order, data types, missing-value handling, and model version.

---

# 36. MLOps

## 36.1 MVP MLOps

Required:

- Artifact versioning
- Model metadata
- Dataset hash
- Feature version
- Evaluation report
- Model card
- Repeatable training script

Optional:

- MLflow
- DVC
- Evidently
- Scheduled monitoring

## 36.2 MLflow

Use for experiment parameters, metrics, artifacts, model registry, and model stage.

Stages:

- Experimental
- Validated
- Approved
- Active
- Retired

## 36.3 Model Card

Include intended use, target definition, dataset, features, performance, calibration, fairness, limitations, prohibited uses, deployment date, and version.

---

# 37. Testing Strategy

## 37.1 Unit Tests

Test feature formulas, consent rules, risk bands, policy rules, reason codes, data reliability, stress transformations, and counterfactual constraints.

## 37.2 API Tests

Test authentication, permissions, CRUD, upload, scoring, explanation, decision, appeal, and audit.

## 37.3 ML Tests

Test schema, null rates, feature range, leakage, determinism, minimum ROC-AUC, maximum Brier score, calibration, fairness reports, and artifact loading.

## 37.4 Integration Tests

Test:

```text
application
-> consent
-> upload
-> features
-> score
-> explanation
-> decision
-> audit
```

## 37.5 End-to-End Tests

Use Playwright.

Scenarios:

- Borrower submits application.
- Analyst reviews and decides.
- Borrower appeals.
- Compliance reviewer exports audit report.

## 37.6 Security Tests

Test broken access control, IDOR, SQL injection, file upload abuse, token expiry, tenant isolation, sensitive-data exposure, and rate limiting.

---

# 38. Security

## 38.1 Authentication

- Strong password hash
- Token expiry
- Refresh-token rotation
- Role enforcement
- Session revocation

## 38.2 Sensitive Data

- Encrypt sensitive fields
- Mask values in UI
- Avoid sensitive data in logs
- Store uploads privately
- Use signed download URLs

## 38.3 File Upload

- MIME check
- Extension check
- Size limit
- Malware scan
- File hash
- Quarantine before parsing

## 38.4 API

- Pydantic validation
- CORS restrictions
- Rate limiting
- Error sanitisation
- Request IDs
- Audit middleware

## 38.5 LLM Privacy

Do not send full name, national ID, account number, raw bank statement, phone number, or address.

Send approved reason codes, aggregated values, redacted text, and structured non-identifying context.

---

# 39. Deployment Plan

## 39.1 Local Development

Services:

- Next.js frontend
- FastAPI backend
- PostgreSQL
- Optional Redis
- Optional worker
- Optional MLflow
- MinIO or local uploads

Use Docker Compose.

```text
docker-compose.yml
├── frontend
├── backend
├── postgres
├── redis
├── worker
├── minio
└── mlflow
```

## 39.2 MVP Cloud Deployment

### Frontend

- Vercel

### Backend

- Render, Railway, Fly.io, or one cloud VM

### Database

- Managed PostgreSQL

### Object Storage

- S3-compatible bucket

### Redis

- Managed Redis only if background tasks are enabled

### Model Artifacts

- Backend image for small artifacts
- Object storage or MLflow for versioned artifacts

## 39.3 Containerisation

Backend Dockerfile:

- Python slim image
- Install dependencies
- Copy source
- Non-root user
- Health check
- Uvicorn or Gunicorn worker

Frontend Dockerfile:

- Multi-stage build
- Production Next.js output

## 39.4 Database Migration

Deployment sequence:

1. Build image.
2. Back up database.
3. Run Alembic migrations.
4. Start backend.
5. Check health.
6. Start frontend.
7. Run smoke tests.

## 39.5 Environment Variables

Backend:

```text
DATABASE_URL
JWT_SECRET
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS
CORS_ORIGINS
UPLOAD_DIR
MODEL_ARTIFACT_PATH
REDIS_URL
MLFLOW_TRACKING_URI
OBJECT_STORAGE_ENDPOINT
OBJECT_STORAGE_ACCESS_KEY
OBJECT_STORAGE_SECRET_KEY
```

Frontend:

```text
NEXT_PUBLIC_API_URL
```

## 39.6 CI/CD

Pull request:

1. Lint.
2. Type check.
3. Unit tests.
4. API tests.
5. ML tests.
6. Security scan.
7. Docker build.

Main branch:

1. Build.
2. Deploy staging.
3. Run migrations.
4. Smoke test.
5. Manual approval.
6. Deploy MVP.
7. Verify health.

## 39.7 Observability

MVP:

- Structured logs
- Request IDs
- Sentry
- Basic health endpoint
- Model-version logging
- Prediction latency
- Error counts

Optional:

- Prometheus
- Grafana
- OpenTelemetry

---

# 40. Deployment Environments

## 40.1 Development

- Local database
- Mock email
- Debug logs
- Local model artifacts
- Synthetic data

## 40.2 Staging

- Managed test database
- Production-like configuration
- Seeded demo users
- Seeded applications
- Test model

## 40.3 Demo / MVP Production

- Managed PostgreSQL
- Private object storage
- HTTPS
- Restricted CORS
- Secrets manager
- Scheduled backups
- Error monitoring

---

# 41. Performance Targets

Reasonable MVP targets:

- Standard API p95: under 500 ms
- Application list p95: under 1 second
- Scoring: under 3 seconds
- SHAP explanation: under 5 seconds
- Report generation: under 15 seconds

These are MVP targets, not guarantees.

---

# 42. Implementation Milestones

## Milestone 1 — Database and Authentication

- PostgreSQL
- Alembic
- User registration
- Login
- Roles
- Seed users

## Milestone 2 — Borrower and Application

- Borrower CRUD
- Application CRUD
- Status workflow
- Assignment
- Timeline

## Milestone 3 — Consent and Data Upload

- Consent
- CSV/XLSX upload
- Parsing
- Validation
- Reliability

## Milestone 4 — Transactions and Features

- Normalisation
- Categorisation
- Feature generation
- Lineage
- Data corrections

## Milestone 5 — Model Training

- Dataset
- Logistic Regression
- XGBoost
- EBM
- Calibration
- Metrics
- Artifacts

## Milestone 6 — Scoring and SHAP

- Scoring API
- Prediction storage
- SHAP
- Reason codes
- Evidence drawer

## Milestone 7 — Policy and Decisions

- Policy engine
- Manual-review reasons
- Analyst decision
- Overrides
- Audit

## Milestone 8 — Advanced AI Features

- Model agreement
- OOD
- Counterfactuals
- Stress testing
- Integrity alerts

## Milestone 9 — Borrower Features

- Explanation
- Information request
- Appeal
- Notifications

## Milestone 10 — Governance

- Fairness
- Monitoring
- Reports
- Model card

## Milestone 11 — Frontend Completion

- Remove remaining mock data
- Loading states
- Error states
- Pagination
- Validation
- Empty states

## Milestone 12 — Deployment

- Docker
- CI/CD
- Staging
- Demo deployment
- Documentation
- Demo video

---

# 43. Final Definition of Done

The MVP is complete when:

- PostgreSQL migrations work.
- Users can authenticate.
- Roles are enforced.
- Borrowers can create applications.
- Consent is recorded and enforced.
- Financial data can be uploaded.
- Transactions are validated and stored.
- Data reliability is calculated.
- Features are generated and versioned.
- A trained model produces real probability of default.
- Probability is calibrated.
- Model version is stored.
- SHAP explanations are generated.
- Evidence is traceable.
- Policy rules execute.
- Model disagreement is calculated.
- OOD detection works.
- Stress tests work.
- Counterfactual simulation works.
- Integrity alerts work.
- Analysts can make decisions.
- Overrides require reasons.
- Borrowers receive explanations.
- Appeals work.
- Fairness reports are generated.
- Monitoring data is displayed.
- Reports are downloadable.
- Audit logs are complete.
- Frontend pages use real APIs.
- Automated tests pass.
- The application is deployed.
- A complete end-to-end demo works.

---

# 44. Critical Engineering Recommendations

1. Do not train a foundation model for this project.
2. Do not use LoRA or QLoRA for the credit score.
3. Train tabular models locally or in Colab.
4. Use public labelled credit data for the core model.
5. Use Malaysian open data only for context and synthetic ranges unless labels exist.
6. Treat synthetic alternative data honestly.
7. Separate training from inference.
8. Use a time-based split where possible.
9. Prevent borrower leakage.
10. Calibrate probabilities.
11. Evaluate PR-AUC and Brier score, not only accuracy.
12. Store model and feature versions.
13. Treat SHAP as evidence support, not causal proof.
14. Require human review for uncertain cases.
15. Keep credit risk, fraud risk, and data reliability separate.
16. Implement one complete vertical slice before adding Redis or MLflow.
17. Build every frontend feature with a simplified real backend implementation.
18. Do not call the MVP production-ready for real lending.
19. Document limitations clearly.
20. Make reproducibility part of the final academic contribution.

---

# 45. Recommended Research Contribution

Frame the contribution as:

> Design and evaluation of an explainable, uncertainty-aware, fairness-evaluated alternative-data credit-risk platform for thin-file borrowers, implemented as a fully functional end-to-end MVP.

Recommended experiments:

1. Traditional features versus alternative features.
2. Logistic Regression versus XGBoost versus EBM.
3. Calibrated versus uncalibrated probabilities.
4. Performance before and after removing sensitive proxies.
5. SHAP explanation evaluation.
6. Model disagreement as a manual-review trigger.
7. OOD detection.
8. Data reliability impact.
9. Cost-sensitive threshold selection.
10. Template explanations versus optional fine-tuned LLM explanations.

---

# 46. References and Dataset Sources

Use these authoritative starting points:

1. UCI Machine Learning Repository — Statlog German Credit Data.
2. UCI Machine Learning Repository — South German Credit.
3. UCI Machine Learning Repository — Default of Credit Card Clients.
4. Kaggle — Home Credit Default Risk.
5. OpenDOSM — Household Income and Expenditure.
6. OpenDOSM — Household Income by State and Percentile.
7. Hu et al. — LoRA: Low-Rank Adaptation of Large Language Models.
8. Dettmers et al. — QLoRA: Efficient Finetuning of Quantized LLMs.
9. SHAP documentation and TreeExplainer.
10. Scikit-learn documentation.
11. XGBoost documentation.
12. LightGBM documentation.
13. InterpretML documentation.
14. Fairlearn documentation.
15. MLflow documentation.

---

# 47. Final Position

MyCreditLens should be built as a full-featured MVP with a real end-to-end workflow, but its primary AI should remain a calibrated, explainable tabular machine-learning system.

The correct AI stack is:

```text
Public labelled credit dataset
+ synthetic alternative-data features
+ rigorous feature engineering
+ Logistic Regression baseline
+ XGBoost or LightGBM performance model
+ EBM interpretability challenger
+ calibration
+ SHAP
+ fairness evaluation
+ OOD and abstention
+ analyst-controlled decision
```

The optional language-model stack is:

```text
Approved reason codes
+ structured non-sensitive context
+ prompt-only baseline
+ optional RAG
+ optional LoRA or QLoRA fine-tuning
+ output validation
+ human review
```

This separation creates a technically defensible, academically strong, and operationally credible final-year project.
