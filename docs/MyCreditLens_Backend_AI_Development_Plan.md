# MyCreditLens — Backend, Data, AI, API, Security, and Deployment Plan

## 1. System Objective

MyCreditLens is an explainable alternative-data microcredit risk platform for thin-file borrowers, gig workers, micro-entrepreneurs, and small merchants.

The backend must:
- Ingest borrower data
- Validate consent
- Process financial records
- Engineer risk features
- Generate default probabilities
- Produce explainable outputs
- Apply lending policies
- Support analyst review
- Maintain tamper-evident audit trails
- Expose secure APIs
- Monitor model quality, fairness, and drift

The project is an academic prototype. It must not claim to be a certified banking system or legally approved automated lending platform.

---

# 2. Recommended Architecture

## 2.1 Architecture Style

Use a modular monolith for the FYP.

Do not begin with microservices. Microservices would increase deployment complexity, distributed tracing requirements, authentication overhead, and failure modes without creating meaningful academic value.

Use clear internal modules so the system can later be separated if needed.

## 2.2 Main Components

1. API Gateway / Backend API
2. Authentication and Authorisation
3. Borrower and Application Service
4. Consent Service
5. Data Ingestion Service
6. Document Processing Service
7. Feature Engineering Pipeline
8. Risk Scoring Service
9. Explainability Service
10. Policy Rules Engine
11. Decision Service
12. Audit Service
13. Notification Service
14. Model Monitoring Service
15. Reporting Service
16. Background Job Worker
17. PostgreSQL Database
18. Redis
19. Object Storage
20. MLflow

---

# 3. Recommended Technology Stack

## Backend
- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2
- Alembic
- PostgreSQL
- Redis
- Celery or Dramatiq
- Pandas
- Polars where beneficial
- NumPy
- scikit-learn
- XGBoost
- LightGBM
- InterpretML
- SHAP
- LIME
- Fairlearn
- Evidently
- MLflow
- Great Expectations
- PyJWT or Authlib
- Passlib / Argon2
- boto3 or S3-compatible SDK

## Optional AI Services
- Hugging Face Inference API
- Self-hosted Ollama
- vLLM for local or server inference
- Tesseract or PaddleOCR
- Sentence Transformers

## Infrastructure
- Docker
- Docker Compose
- Nginx
- GitHub Actions
- MinIO for local object storage
- Sentry
- Prometheus
- Grafana
- OpenTelemetry

---

# 4. Core Domain Modules

## 4.1 Identity and Access Module
Responsibilities:
- User registration
- Organisation membership
- Login
- MFA
- Password reset
- Session management
- Role-based access control
- API key management

Roles:
- SUPER_ADMIN
- LENDER_ADMIN
- CREDIT_ANALYST
- COMPLIANCE_REVIEWER
- BORROWER
- API_CLIENT

---

## 4.2 Borrower Module
Responsibilities:
- Borrower profile
- Employment profile
- Business profile
- Contact details
- Identity metadata
- Borrower segmentation
- Data retention status

Sensitive fields must be encrypted at application level where practical.

---

## 4.3 Application Module
Responsibilities:
- Loan application creation
- Requested amount
- Loan purpose
- Application status
- Assignment
- Priority
- Review lifecycle
- Final decision

Suggested status values:
- DRAFT
- SUBMITTED
- DATA_PENDING
- VALIDATION_FAILED
- READY_FOR_SCORING
- SCORING
- SCORED
- MANUAL_REVIEW
- INFORMATION_REQUESTED
- APPROVED
- REJECTED
- WITHDRAWN
- ARCHIVED

---

## 4.4 Consent Module
Responsibilities:
- Capture consent
- Scope consent by source
- Track consent version
- Record timestamps
- Support revocation
- Enforce expiry
- Store consent evidence

A score request must fail when required consent is missing or expired.

---

## 4.5 Data Ingestion Module

Supported inputs:
- CSV
- XLSX
- JSON
- PDF statements
- API payload
- Manual entry

Responsibilities:
- File upload
- File hash generation
- MIME validation
- Malware scanning
- Schema detection
- Source mapping
- Currency normalisation
- Date normalisation
- Duplicate detection
- Missing-value analysis
- Data lineage tracking

---

## 4.6 Document Processing Module

Responsibilities:
- OCR
- Statement parsing
- Table extraction
- Transaction extraction
- Confidence scoring
- Human correction workflow

Use OCR only for extraction. Never use an LLM as the authoritative source of transaction amounts.

Recommended pipeline:
1. Upload document
2. Store original
3. Generate document hash
4. Run OCR
5. Detect tables
6. Extract transactions
7. Validate totals
8. Assign extraction confidence
9. Request manual review if confidence is low

---

## 4.7 Feature Engineering Module

### Core Feature Categories

#### Income
- Average monthly income
- Median monthly income
- Income growth
- Income volatility
- Number of income sources
- Income concentration
- Longest income gap

#### Expenses
- Average monthly expense
- Essential expense ratio
- Discretionary expense ratio
- Expense volatility
- Recurring bill burden

#### Cash Flow
- Net monthly cash flow
- Cash-in to cash-out ratio
- Minimum balance
- Median balance
- Negative-balance frequency
- Liquidity buffer
- End-of-month balance trend

#### Payment Behaviour
- Utility payment timeliness
- Missed-payment count
- Recurring bill consistency
- Late-payment ratio

#### Remittances
- Average remittance amount
- Remittance frequency
- Stability
- Dependency ratio

#### Business Activity
- POS turnover
- Sales trend
- Transaction frequency
- Customer concentration
- Revenue seasonality
- Inventory-cycle proxy

#### Gig Worker Features
- Active working days
- Weekly income consistency
- Platform concentration
- Cancellation or refund proxy
- Income seasonality

#### Data Quality
- Missing-value rate
- Source coverage
- Date coverage
- Extraction confidence
- Duplicate rate
- Consistency score

### Feature Requirements
Every feature must have:
- Name
- Description
- Formula
- Data source
- Missing-value policy
- Valid range
- Version
- Sensitivity classification

---

# 5. AI and Machine Learning Plan

## 5.1 Problem Definition

Primary task:
- Binary classification

Target:
- `default_within_90_days`
or
- `default_within_180_days`

For an academic prototype, select one target definition and keep it fixed.

Example:
```text
1 = borrower missed repayment beyond the defined threshold
0 = borrower completed repayment without default
```

The target definition must be documented precisely.

---

## 5.2 Model Strategy

Train these models:

### Baseline
- Logistic Regression

### Tree Models
- Random Forest
- XGBoost
- LightGBM

### Interpretability Model
- Explainable Boosting Machine

Do not use a large language model as the core scoring model.

---

## 5.3 Training Pipeline

1. Load labelled dataset
2. Validate schema
3. Remove duplicates
4. Split by borrower
5. Handle missing values
6. Encode categorical features
7. Scale where necessary
8. Handle imbalance
9. Train baseline
10. Train advanced models
11. Tune hyperparameters
12. Evaluate
13. Calibrate probabilities
14. Run fairness analysis
15. Generate model card
16. Register model
17. Deploy approved model

---

## 5.4 Data Splitting

Recommended:
- Train: 70%
- Validation: 15%
- Test: 15%

Where possible, use a time-based split to simulate real deployment.

Prevent leakage:
- Same borrower must not appear across train and test
- Future data must not influence historical predictions
- Features must only use information available before the decision time

---

## 5.5 Class Imbalance

Possible approaches:
- Class weights
- Threshold tuning
- SMOTE for experimentation
- Balanced Random Forest
- Focal loss only if using neural networks

Do not optimise raw accuracy.

---

## 5.6 Evaluation Metrics

Primary:
- ROC-AUC
- PR-AUC
- Recall for default class
- Precision for default class
- F1
- Brier score
- Log loss
- Calibration error
- KS statistic

Operational:
- Approval rate
- Manual review rate
- False approval rate
- False rejection rate

Always show confusion matrices at selected thresholds.

---

## 5.7 Probability Calibration

Use:
- Platt scaling
- Isotonic regression

The final model must output calibrated probabilities rather than arbitrary scores.

---

## 5.8 Risk Bands

Example only:
- Low: PD < 0.15
- Medium: 0.15 ≤ PD < 0.30
- High: PD ≥ 0.30

Thresholds must be configurable.

---

## 5.9 Explainability

### SHAP
Use SHAP for:
- Global feature importance
- Local explanation
- Waterfall chart
- Feature contribution values

### LIME
Use LIME only as a secondary comparison method.

### Reason Codes
Convert SHAP features into controlled templates.

Example:
```text
High income volatility increased assessed risk.
Consistent utility payments reduced assessed risk.
A low liquidity buffer increased assessed risk.
```

Do not allow an LLM to invent new reasons.

---

## 5.10 LLM Usage

An open-source LLM may be used for:
- Rewriting technical explanations
- Bahasa Melayu translation
- Analyst question answering
- Transaction description classification
- Document summarisation
- Synthetic test narratives

The LLM must not:
- Generate the probability of default
- Approve or reject applications
- Override policy rules
- Produce unsupported explanation factors
- Access unnecessary personal data

Recommended pattern:
1. SHAP generates factual factors
2. Rules engine validates factors
3. LLM rewrites approved factors
4. Output is stored with model and prompt version

---

# 6. Fairness and Responsible AI

## 6.1 Fairness Metrics
- Selection rate
- Demographic parity difference
- Disparate impact ratio
- Equal opportunity difference
- False-positive rate difference
- False-negative rate difference

## 6.2 Sensitive Features
Potentially sensitive features should not be used directly in scoring unless academically justified and ethically reviewed.

Examples:
- Ethnicity
- Religion
- Gender
- Disability
- Precise geolocation
- Political affiliation

Sensitive attributes may be retained separately for fairness evaluation only, with strict access controls.

## 6.3 Proxy Risk
Review features such as:
- Postcode
- Device type
- Language
- Employment platform
- Phone model
- Location frequency

These can act as proxies for socioeconomic status.

---

# 7. Policy Rules Engine

The rules engine must be independent from the model.

Example rules:
```text
IF consent_missing = true → BLOCK
IF fraud_flag = true → REJECT
IF data_quality_score < 0.60 → MANUAL_REVIEW
IF requested_amount > configured_limit → MANUAL_REVIEW
IF probability_of_default >= high_risk_threshold → HIGH_RISK
```

Each rule execution must store:
- Rule ID
- Rule version
- Input
- Result
- Timestamp

---

# 8. Decision Workflow

## Decision Types
- APPROVE
- REJECT
- MANUAL_REVIEW
- REQUEST_INFORMATION
- WITHDRAW

## Decision Requirements
Every decision must include:
- User
- Timestamp
- Reason
- Model prediction
- Policy outcome
- Optional override
- Override justification
- Model version
- Policy version

Overrides must be visible in audit logs.

---

# 9. Database Design

## Main Tables

### organisations
- id
- name
- status
- created_at

### users
- id
- organisation_id
- name
- email
- password_hash
- role
- status
- last_login_at

### borrowers
- id
- organisation_id
- external_reference
- full_name_encrypted
- date_of_birth_encrypted
- occupation_category
- borrower_segment
- created_at

### applications
- id
- borrower_id
- requested_amount
- purpose
- status
- assigned_analyst_id
- submitted_at
- decided_at

### consent_records
- id
- borrower_id
- application_id
- source_type
- consent_version
- granted_at
- expires_at
- revoked_at
- evidence_uri

### data_sources
- id
- application_id
- source_type
- file_uri
- file_hash
- status
- coverage_start
- coverage_end
- quality_score

### raw_transactions
- id
- data_source_id
- transaction_date
- description_encrypted
- amount
- direction
- currency
- category
- confidence

### engineered_features
- id
- application_id
- feature_name
- feature_value
- feature_version
- source_lineage
- created_at

### model_versions
- id
- model_name
- version
- algorithm
- metrics_json
- artifact_uri
- status
- approved_at

### model_predictions
- id
- application_id
- model_version_id
- probability_of_default
- risk_band
- threshold_version
- created_at

### explanation_reports
- id
- prediction_id
- shap_values_json
- reason_codes_json
- human_readable_text
- language
- generator_version

### policy_rules
- id
- name
- version
- condition_json
- action
- status

### policy_results
- id
- application_id
- rule_id
- result
- detail_json

### decisions
- id
- application_id
- decision
- reason
- analyst_id
- override
- override_reason
- created_at

### audit_logs
- id
- organisation_id
- user_id
- action
- entity_type
- entity_id
- before_json
- after_json
- ip_address
- created_at

---

# 10. API Design

Base path:
```text
/api/v1
```

## Authentication
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/mfa/verify`
- `POST /auth/password/forgot`
- `POST /auth/password/reset`

## Borrowers
- `POST /borrowers`
- `GET /borrowers`
- `GET /borrowers/{id}`
- `PATCH /borrowers/{id}`
- `DELETE /borrowers/{id}`

## Applications
- `POST /applications`
- `GET /applications`
- `GET /applications/{id}`
- `PATCH /applications/{id}`
- `POST /applications/{id}/submit`
- `POST /applications/{id}/assign`

## Consent
- `POST /applications/{id}/consents`
- `GET /applications/{id}/consents`
- `POST /consents/{id}/revoke`

## Data Sources
- `POST /applications/{id}/data-sources`
- `GET /applications/{id}/data-sources`
- `DELETE /data-sources/{id}`
- `POST /data-sources/{id}/validate`
- `POST /data-sources/{id}/reprocess`

## Scoring
- `POST /applications/{id}/score`
- `GET /applications/{id}/score`
- `POST /applications/{id}/rescore`

## Explainability
- `GET /predictions/{id}/explanation`
- `POST /predictions/{id}/explanation/language`
- `GET /predictions/{id}/shap`

## Decisions
- `POST /applications/{id}/decisions`
- `GET /applications/{id}/decisions`

## Monitoring
- `GET /monitoring/models`
- `GET /monitoring/drift`
- `GET /monitoring/fairness`
- `GET /monitoring/calibration`

## Audit
- `GET /audit-logs`
- `GET /audit-logs/{id}`

## Reports
- `POST /reports/application/{id}`
- `POST /reports/portfolio`
- `GET /reports/{id}`

---

# 11. Example Score API

## Request
```json
{
  "application_id": "app_123",
  "force_recompute": false
}
```

## Response
```json
{
  "prediction_id": "pred_456",
  "probability_of_default": 0.184,
  "risk_band": "MEDIUM",
  "confidence": 0.87,
  "recommended_action": "MANUAL_REVIEW",
  "model": {
    "name": "lightgbm_credit_risk",
    "version": "1.2.0"
  },
  "top_factors": [
    {
      "feature": "income_volatility",
      "direction": "increases_risk",
      "impact": 0.091
    },
    {
      "feature": "utility_payment_timeliness",
      "direction": "reduces_risk",
      "impact": -0.063
    }
  ]
}
```

---

# 12. Background Jobs

Use Celery or Dramatiq for:
- OCR
- Data validation
- Feature generation
- Model scoring
- Explanation generation
- Report generation
- Email notifications
- Drift calculations

Job states:
- QUEUED
- RUNNING
- SUCCEEDED
- FAILED
- RETRYING
- CANCELLED

---

# 13. Data Quality Framework

Checks:
- Required columns
- Data type validity
- Date range
- Currency consistency
- Duplicate records
- Missing values
- Invalid amounts
- Outliers
- Transaction balance consistency
- OCR confidence
- Source completeness

Generate:
- Overall quality score
- Issue list
- Blocking issues
- Warnings
- Suggested corrections

---

# 14. Security Plan

## Authentication
- Argon2id password hashing
- MFA for privileged users
- Short-lived access tokens
- Rotating refresh tokens
- Secure HTTP-only cookies
- Device/session revocation

## Authorisation
- RBAC
- Organisation-level tenancy isolation
- Object-level permissions
- Admin approval for privileged actions

## Data Protection
- TLS
- Encryption at rest
- Field-level encryption for sensitive data
- Key rotation
- Secrets manager
- Masked logs
- Data minimisation

## File Security
- MIME validation
- Extension validation
- File-size limits
- Malware scanning
- Quarantine before processing
- Signed URLs
- Private object storage

## API Security
- Rate limiting
- Idempotency keys
- Request validation
- Replay protection
- API key scopes
- Webhook signatures
- Audit logging

---

# 15. Auditability

Audit these events:
- Login
- Failed login
- Borrower creation
- Consent grant and revocation
- File upload
- Data correction
- Score generation
- Model version used
- Policy rule result
- Decision
- Override
- API key creation
- Export
- User and role changes

Audit records must be append-only from the application perspective.

Optional academic enhancement:
- Chain audit hashes to detect tampering

---

# 16. Model Registry and MLOps

Use MLflow for:
- Experiment tracking
- Parameters
- Metrics
- Artifacts
- Model registration
- Stage promotion

Model stages:
- EXPERIMENTAL
- VALIDATED
- APPROVED
- ACTIVE
- RETIRED

A model cannot become ACTIVE without:
- Test metrics
- Calibration report
- Fairness report
- Explainability check
- Model card
- Approval record

---

# 17. Model Monitoring

Monitor:
- Prediction distribution
- Feature distribution
- Missing-value rates
- Drift
- Calibration
- Segment performance
- Approval rate
- Manual review rate
- Data quality

Alerts:
- PSI above threshold
- AUC degradation
- Calibration degradation
- Approval-rate shift
- Segment disparity increase
- Missing feature increase

---

# 18. Logging and Observability

## Logs
- Structured JSON logs
- Correlation ID
- User ID
- Organisation ID
- Request ID
- Application ID
- Job ID

## Metrics
- Request latency
- Error rate
- Scoring latency
- Job queue depth
- OCR failure rate
- Model inference count
- Database connection usage

## Tracing
Use OpenTelemetry across:
- API request
- Job queue
- Feature generation
- Model inference
- Report generation

---

# 19. Error Handling

Standard error shape:
```json
{
  "error": {
    "code": "CONSENT_REQUIRED",
    "message": "Required consent is missing.",
    "details": {
      "source_type": "EWALLET"
    },
    "request_id": "req_123"
  }
}
```

Categories:
- Validation error
- Authentication error
- Authorisation error
- Consent error
- Data quality error
- Scoring error
- Model unavailable
- Policy conflict
- Internal error

Never expose stack traces to clients.

---

# 20. Testing Strategy

## Unit Tests
- Feature formulas
- Policy rules
- Risk band mapping
- Consent validation
- Permission checks
- Reason-code generation

## Integration Tests
- Database
- Redis
- Object storage
- Model loading
- Scoring pipeline
- Audit generation

## ML Tests
- Schema
- Leakage
- Performance threshold
- Calibration threshold
- Fairness threshold
- Feature drift
- Deterministic inference

## API Tests
- Authentication
- CRUD
- Upload
- Scoring
- Explanation
- Decisions
- Audit

## Security Tests
- Broken access control
- IDOR
- Injection
- File upload
- Token misuse
- Rate limiting
- Tenant isolation

## Performance Tests
- Concurrent score requests
- Large CSV uploads
- Report generation
- Application list queries

---

# 21. Deployment Architecture

## Local Development
Docker Compose:
- frontend
- backend
- worker
- PostgreSQL
- Redis
- MinIO
- MLflow
- Nginx

## FYP Demo Deployment
Recommended:
- Frontend: Vercel
- Backend: Render, Railway, Fly.io, or cloud VM
- PostgreSQL: Managed PostgreSQL
- Redis: Managed Redis
- Object storage: S3-compatible
- MLflow: Same VM or separate container

## Production-Like Deployment
- Managed Kubernetes or ECS
- Managed PostgreSQL
- Managed Redis
- Private object storage
- WAF
- Secret manager
- Monitoring stack

---

# 22. CI/CD Pipeline

On pull request:
1. Lint
2. Type check
3. Unit tests
4. API tests
5. Security scan
6. Dependency scan
7. Docker build

On merge to main:
1. Build image
2. Run migrations
3. Deploy staging
4. Run smoke tests
5. Manual approval
6. Deploy production/demo
7. Health check
8. Rollback if failed

---

# 23. Recommended Backend Folder Structure

```text
app/
├── api/
│   ├── dependencies/
│   └── v1/
├── core/
│   ├── config.py
│   ├── security.py
│   └── logging.py
├── modules/
│   ├── auth/
│   ├── borrowers/
│   ├── applications/
│   ├── consent/
│   ├── ingestion/
│   ├── documents/
│   ├── features/
│   ├── scoring/
│   ├── explainability/
│   ├── policies/
│   ├── decisions/
│   ├── monitoring/
│   ├── reports/
│   └── audit/
├── models/
├── schemas/
├── repositories/
├── services/
├── workers/
├── ml/
│   ├── datasets/
│   ├── features/
│   ├── training/
│   ├── evaluation/
│   ├── inference/
│   └── monitoring/
├── tests/
└── main.py
```

---

# 24. Development Phases

## Phase 1 — Foundation
- Repository setup
- Docker
- FastAPI
- PostgreSQL
- Authentication
- RBAC
- Organisation tenancy

## Phase 2 — Borrower and Application Workflow
- Borrowers
- Applications
- Status lifecycle
- Assignment
- Notes

## Phase 3 — Consent and Data Ingestion
- Consent records
- Uploads
- Validation
- Data source metadata
- Data quality report

## Phase 4 — Feature Engineering
- Transaction normalisation
- Feature definitions
- Feature versioning
- Data lineage
- Feature test suite

## Phase 5 — Model Development
- Baseline model
- Advanced models
- Evaluation
- Calibration
- Fairness
- Model selection

## Phase 6 — Scoring and Explainability
- Model service
- SHAP
- Reason codes
- Policy rules
- Decision workflow

## Phase 7 — Monitoring and Governance
- MLflow
- Drift
- Fairness dashboard APIs
- Audit logs
- Model cards

## Phase 8 — Reporting and Deployment
- PDF/CSV reports
- CI/CD
- Monitoring
- Security hardening
- Demo environment

---

# 25. Suggested 14-Week FYP Schedule

## Weeks 1–2
- Requirements
- Literature review
- Dataset strategy
- Architecture
- UI wireframes

## Weeks 3–4
- Authentication
- Borrower/application modules
- Database

## Weeks 5–6
- Data upload
- Validation
- Feature engineering

## Weeks 7–8
- Model training
- Evaluation
- Calibration
- Fairness

## Weeks 9–10
- Scoring API
- SHAP
- Policy engine
- Decision workflow

## Weeks 11–12
- Monitoring
- Reports
- Audit logs
- Frontend integration

## Week 13
- Testing
- Security
- Performance
- User evaluation

## Week 14
- Final report
- Presentation
- Demo video
- Deployment

---

# 26. Dataset Strategy

Best options:
1. Public credit-risk dataset
2. Synthetic alternative-data dataset
3. Hybrid dataset
4. Partner-provided anonymised dataset

Recommended FYP approach:
- Use a public labelled loan outcome dataset
- Add synthetic alternative-data fields
- Clearly document which fields are real and which are simulated
- Avoid claiming Malaysian predictive validity unless Malaysian data is used

Synthetic generation must preserve:
- Realistic distributions
- Correlations
- Missingness
- Income seasonality
- Class imbalance

---

# 27. Research Questions

1. Do alternative-data features improve default prediction over a traditional baseline?
2. Which model provides the best balance between discrimination and calibration?
3. How much performance is lost when sensitive or proxy features are removed?
4. Are SHAP explanations understandable to analysts?
5. Does performance vary materially across borrower segments?
6. Does an explainable model provide sufficient performance compared with boosting models?

---

# 28. FYP Evaluation Deliverables

- Architecture diagram
- ER diagram
- API documentation
- Dataset documentation
- Feature dictionary
- Model comparison table
- Calibration curve
- Confusion matrices
- Fairness report
- SHAP examples
- Model card
- Security design
- User acceptance test
- Deployment guide
- Demo video

---

# 29. Definition of Done

The backend and AI system are complete only when:
- Consent is enforced
- Data quality is measured
- Feature lineage exists
- At least three models are compared
- Probabilities are calibrated
- SHAP explanations are generated
- Policy rules are independent
- Analyst decisions are audited
- Sensitive data is protected
- API documentation exists
- Tests pass
- Model versioning exists
- Fairness analysis is documented
- The system is deployed and demonstrable
