# MyCreditLens Supabase Integration Architecture and Phase 1 Plan

Date: 2026-07-06

## Architecture Decision

Use Supabase selectively as managed infrastructure, not as a replacement for the FastAPI backend.

Target architecture:

```text
Next.js frontend
  - Supabase Auth client
  - FastAPI API client
        |
        | Supabase access token
        v
FastAPI backend
  - verifies Supabase JWT
  - enforces business authorization
  - owns credit workflow and AI logic
        |
        +--> Supabase PostgreSQL
        +--> Supabase Storage
        +--> offline-trained ML artifacts
```

FastAPI remains the main application and AI backend for:

- consent enforcement
- data validation
- transaction processing
- feature engineering
- scoring
- SHAP/explainability
- policy evaluation
- decisions and overrides
- audit logs
- fairness and monitoring
- report generation

Do not replace FastAPI with Supabase Edge Functions. Edge Functions may be used later for small webhooks only.

## Supabase Feature Usage

| Supabase feature | Decision | Purpose |
|---|---|---|
| PostgreSQL | Use | Primary managed database |
| Auth | Use | Registration, login, refresh tokens, password reset, sessions |
| Storage | Use | Financial documents, appeal documents, consent evidence, reports |
| Row Level Security | Use | Defence-in-depth authorization |
| Realtime | Optional later | Application status and notification updates |
| Edge Functions | Limited later | Lightweight integrations and webhooks only |
| Database REST API | Avoid for lending operations | Keep sensitive workflows behind FastAPI |
| pgvector | Optional later | Policy/document RAG only, not core scoring |

Never expose the Supabase service-role key to the frontend.

## SQLAlchemy Connection Configuration

Use Supabase PostgreSQL as the database host while keeping SQLAlchemy and Alembic.

Required settings:

```env
DATABASE_URL=postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@HOST:PORT/postgres
DATABASE_URL_SYNC=postgresql://postgres.PROJECT_REF:PASSWORD@HOST:PORT/postgres
```

The exact direct, session-pooler, or transaction-pooler URL must come from the Supabase project Connect panel.

For a persistent FastAPI server, prefer:

1. Direct connection if deployment networking supports it.
2. Session pooler if direct connectivity is unsuitable.
3. Avoid transaction pooling unless SQLAlchemy behavior has been verified with it.

Recommended async engine settings:

```python
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=1800,
)
```

Important: moving to Supabase does not fix the current backend session mismatch. The backend must still be made internally consistent by using SQLAlchemy 2.0 async patterns end to end, or by intentionally switching to synchronous SQLAlchemy.

For this project, the selected direction is:

> SQLAlchemy 2.0 async sessions and Alembic migrations against Supabase PostgreSQL.

## Supabase Auth Migration Plan

Replace the custom FastAPI JWT login flow with Supabase Auth.

Frontend flow:

1. User signs up or signs in through Supabase Auth.
2. Supabase returns access and refresh tokens.
3. Frontend stores/manages session using Supabase client helpers.
4. Frontend sends the Supabase access token to FastAPI as `Authorization: Bearer <token>`.
5. FastAPI verifies the JWT.
6. FastAPI loads the application profile and role from `public.users`.

Backend flow:

1. Decode and verify Supabase JWT using the project JWKS.
2. Read `sub` from the token.
3. Load matching `public.users.id`.
4. Enforce role, organization, ownership, and assignment checks in FastAPI.

Supabase Auth handles:

- email/password registration
- login
- refresh tokens
- password reset
- email verification
- OAuth later if needed
- session management

## Profile Schema Linked to `auth.users`

Use Supabase `auth.users` for identity and `public.users` for application roles/profile data.

Initial schema:

```sql
create table public.organisations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  organisation_id uuid references public.organisations(id),
  email text not null,
  full_name text not null,
  role text not null check (
    role in (
      'borrower',
      'credit_analyst',
      'lender_admin',
      'compliance_reviewer',
      'admin'
    )
  ),
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
```

Recommended application model updates:

- Store borrower ownership through a Supabase Auth user id.
- Store organization id on lender-owned resources.
- Keep analyst and compliance permissions in `public.users`.
- Avoid duplicating password fields in application tables.

## RLS Policy Matrix

RLS should be enabled on sensitive application tables as defence in depth.

FastAPI must still enforce authorization because it will use a backend database connection.

| Table/resource | Borrower | Credit analyst | Lender admin | Compliance reviewer | Admin |
|---|---|---|---|---|---|
| `users` | read/update own limited profile | read users in org as needed | manage org users | read org users | manage all |
| `borrowers` | read/update own borrower profile | read assigned/org borrowers | manage org borrowers | read org borrowers | manage all |
| `applications` | create/read own applications | read/update assigned/org applications | manage org applications | read org applications | manage all |
| `consents` | create/revoke/read own consents | read for reviewed applications | read/manage org consents | read org consents | manage all |
| `data_sources` | create/read own metadata | read/reprocess assigned/org sources | manage org sources | read org sources | manage all |
| `transactions` | read own processed records where exposed | read/update reviewed records | manage org records | read org records | manage all |
| `predictions` | read borrower-safe summary | read assigned/org predictions | read org predictions | read org predictions | manage all |
| `explanations` | read borrower-safe explanation | read full analyst explanation | read org explanations | read org explanations | manage all |
| `decisions` | read own decision summary | create decisions for assigned applications | manage org decisions | read decisions/overrides | manage all |
| `appeals` | create/read own appeals | read assigned appeals | manage org appeals | review org appeals | manage all |
| `audit_logs` | no direct table access | read relevant assigned audit events | read org audit events | read org audit events | manage all |
| storage buckets | signed URLs only for owned files | signed URLs for reviewed org files | signed URLs for org files | signed URLs for org files | manage all |

Example RLS direction:

```sql
alter table public.applications enable row level security;

create policy "borrowers can view own applications"
on public.applications
for select
using (borrower_user_id = auth.uid());

create policy "org staff can view organisation applications"
on public.applications
for select
using (
  organisation_id = (
    select organisation_id
    from public.users
    where id = auth.uid()
  )
);
```

The actual table and column names should be finalized during the Alembic/schema pass.

## Storage Bucket and Path Design

Create private buckets:

- `financial-documents`
- `appeal-documents`
- `generated-reports`
- `consent-evidence`

Recommended paths:

```text
financial-documents/{organisation_id}/{application_id}/{file_id}/{original_file_name}
appeal-documents/{organisation_id}/{application_id}/{appeal_id}/{file_id}/{original_file_name}
generated-reports/{organisation_id}/{application_id}/{report_id}.pdf
consent-evidence/{organisation_id}/{application_id}/{consent_id}.json
```

Store only metadata in PostgreSQL:

- `file_name`
- `storage_bucket`
- `storage_path`
- `file_hash`
- `mime_type`
- `size_bytes`
- `uploaded_by`
- `application_id`
- `processing_status`
- `validation_status`
- `created_at`

Do not store PDF, XLSX, image, or report binaries directly in PostgreSQL.

Use signed URLs for temporary access and processing.

## Alembic Migration Strategy

Use Alembic as the schema source of truth.

Phase 1 migration sequence:

1. Add Supabase-compatible `users` profile table linked to `auth.users`.
2. Update existing models to remove custom password ownership assumptions.
3. Add organisation support if lender/admin scope remains required.
4. Add consent tables and fields required for the vertical slice.
5. Add storage metadata fields to `data_sources`, documents, reports, and appeals.
6. Add audit log fields required for auth/profile/application/scoring/decision events.
7. Add RLS SQL migrations after core tables exist.

Avoid relying on `Base.metadata.create_all` for real development and deployment.

## Frontend Authentication Migration Plan

Add dependencies:

```powershell
pnpm add @supabase/supabase-js @supabase/ssr
```

Frontend environment:

```env
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Frontend changes:

1. Add a Supabase browser client.
2. Replace custom `authApi.login/register` usage with Supabase Auth calls.
3. Keep FastAPI as the API for all credit workflows.
4. Attach current Supabase access token to FastAPI requests.
5. Remove frontend refresh-token calls to `/auth/refresh`.
6. Route users based on application profile role returned by FastAPI.
7. Do not use Supabase JS to write directly to sensitive credit tables.

## Backend JWT Verification Plan

Backend environment:

```env
SUPABASE_URL=
SUPABASE_PROJECT_REF=
SUPABASE_JWT_ISSUER=https://PROJECT_REF.supabase.co/auth/v1
SUPABASE_JWKS_URL=https://PROJECT_REF.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_SERVICE_ROLE_KEY=
```

Backend changes:

1. Replace custom `OAuth2PasswordBearer` user lookup with Supabase JWT verification.
2. Cache JWKS keys with expiry.
3. Validate token signature, issuer, audience if configured, expiry, and subject.
4. Load `public.users` by `auth.users.id`.
5. Return the application profile as the current user.
6. Keep service-role key server-only for admin operations and storage orchestration.

Use a dedicated auth dependency, for example:

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    claims = await verify_supabase_jwt(token)
    user = await user_service.get_by_auth_id(db, claims["sub"])
    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="Inactive or unknown user")
    return user
```

## Environment Variable Template

Frontend:

```env
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Backend:

```env
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql+asyncpg://...
DATABASE_URL_SYNC=postgresql://...

SUPABASE_URL=
SUPABASE_PROJECT_REF=
SUPABASE_JWT_ISSUER=
SUPABASE_JWKS_URL=
SUPABASE_SERVICE_ROLE_KEY=

CORS_ORIGINS=http://localhost:3000
UPLOAD_MAX_SIZE_MB=50

MODEL_ARTIFACT_PATH=./ml/artifacts
REDIS_URL=redis://localhost:6379/0
```

Do not commit real `.env` files or Supabase service-role keys.

## Local and Cloud Development Workflow

### Local Development

1. Create a Supabase project.
2. Copy database connection strings from Supabase Connect.
3. Configure backend `.env`.
4. Run Alembic migrations against Supabase PostgreSQL.
5. Configure Supabase Auth email/password.
6. Configure private storage buckets.
7. Start FastAPI locally.
8. Start Next.js locally.
9. Use Supabase Auth from the frontend and FastAPI for all credit workflows.

### Cloud/Demo Deployment

Recommended MVP deployment:

- Frontend: Vercel
- Backend: Render, Railway, Fly.io, or a single VM
- Database/Auth/Storage: Supabase
- ML artifacts: packaged with backend image initially, later object storage if needed

Deployment checks:

1. Run migrations.
2. Verify backend can connect to Supabase Postgres.
3. Verify Supabase JWT validation.
4. Verify private storage bucket access through backend.
5. Run smoke test for the vertical slice.

## Phase 1 Vertical Slice

Implement this before advanced AI, Realtime, MLflow, pgvector, or Edge Functions:

```text
Supabase Auth login
-> FastAPI verifies Supabase JWT
-> create borrower
-> create application
-> record consent
-> upload CSV/document to Supabase Storage
-> store metadata in Supabase PostgreSQL
-> process transactions in FastAPI
-> generate temporary score
-> record analyst decision
-> create audit log
```

Temporary score is acceptable in Phase 1 only. Replace it with real trained/calibrated model inference in Phase 2.

## Immediate Implementation Order

1. Fix backend SQLAlchemy async session usage.
2. Add Alembic and initial Supabase-compatible migrations.
3. Add Supabase Auth verification backend dependency.
4. Add `public.users` profile synchronization strategy.
5. Update frontend auth to Supabase.
6. Add storage service for private uploads and signed URLs.
7. Align API contracts for borrower/application/consent/upload/scoring/decision.
8. Add seed/demo workflow.
9. Add backend smoke tests for the vertical slice.

