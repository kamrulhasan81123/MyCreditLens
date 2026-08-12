from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import validate_database_connection, init_db
from app.routers import ai, audit, auth, borrowers, applications, scoring, data_sources, decisions, appeals, reports, consents, transactions, insights
from pathlib import Path
import logging
from app.ai.runtime import CreditModelRuntime, ArtifactUnavailableError, FeatureSchemaError
from app.ai.application_adapter import ApplicationToModelAdapter
from ml.contracts import REQUIRED_ARTIFACTS

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: validate database connectivity. Migrations are managed by Alembic.
    try:
        await validate_database_connection()
        logger.info("Database connection validated")
    except Exception as exc:
        logger.error("Database connection validation failed: %s", exc)
        if settings.app_env not in {"development", "test"}:
            raise
    # Auto-create tables in development (production uses Alembic migrations)
    if settings.app_env in {"development", "test"}:
        await init_db()
        logger.info("Database tables auto-created for development")
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="MyCreditLens API",
    description="AI-Powered Credit Assessment Backend",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(borrowers.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(scoring.router, prefix="/api/v1")
app.include_router(data_sources.router, prefix="/api/v1")
app.include_router(decisions.router, prefix="/api/v1")
app.include_router(appeals.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(consents.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(insights.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "service": "MyCreditLens API",
        "environment": settings.app_env,
    }


@app.get("/health/database")
async def database_health_check():
    """Validate database connectivity with a real query."""
    try:
        await validate_database_connection()
        return {"status": "ok", "database": "reachable"}
    except Exception as exc:
        logger.exception("Database health check failed")
        return {"status": "error", "database": "unreachable", "detail": str(exc)}


@app.get("/health/model")
def model_health_check():
    """Truthful model readiness check.

    Reports ``ready`` ONLY if the artifact bundle exists, loads, the active
    feature schema can be satisfied by the application adapter, a deterministic
    dry-run input can be produced, and inference actually executes.

    States: ready | artifact_missing | load_failed | schema_incompatible |
    inference_failed.
    """
    artifact_dir = settings.resolved_model_artifact_path
    expected = [*REQUIRED_ARTIFACTS, "manifest.json"]
    present = [name for name in expected if (artifact_dir / name).exists()]
    missing = [name for name in expected if name not in present]
    detail = None
    metadata = None

    if not (artifact_dir / "manifest.json").is_file():
        status = "artifact_missing"
        return _model_health_payload(status, artifact_dir, present, missing, metadata, detail)

    # 1. Load the bundle (verifies checksums + all artifacts deserialize).
    try:
        runtime = CreditModelRuntime(artifact_dir)
    except ArtifactUnavailableError as exc:
        return _model_health_payload("load_failed", artifact_dir, present, missing, None, str(exc))

    metadata = {
        "model_name": runtime.model_name,
        "model_version": runtime.model_version,
        "feature_schema_version": runtime.feature_schema_version,
    }

    # 2. Confirm the application adapter can satisfy the active feature schema,
    #    and 3. produce a deterministic dry-run input.
    try:
        adapter = ApplicationToModelAdapter(runtime.schema)
        dry_run = adapter.dry_run_features()
    except FeatureSchemaError as exc:
        return _model_health_payload("schema_incompatible", artifact_dir, present, missing, metadata, str(exc))

    # 4. Execute real inference on the dry-run input.
    try:
        result = runtime.predict(dry_run, include_explanation=True)
    except FeatureSchemaError as exc:
        return _model_health_payload("schema_incompatible", artifact_dir, present, missing, metadata, str(exc))
    except Exception as exc:  # inference runtime failure
        logger.exception("Model dry-run inference failed")
        return _model_health_payload("inference_failed", artifact_dir, present, missing, metadata, str(exc))

    metadata["dry_run_probability"] = round(result.probability_of_default, 6)
    return _model_health_payload("ready", artifact_dir, present, missing, metadata, None)


def _model_health_payload(status, artifact_dir, present, missing, metadata, detail):
    return {
        "status": status,
        "artifact_path": str(artifact_dir),
        "present_artifacts": present,
        "missing_artifacts": missing,
        "model": metadata,
        "detail": detail,
    }


@app.get("/api/health")
def legacy_health_check():
    """Backward-compatible health check endpoint."""
    return health_check()


@app.get("/api/v1/")
def root():
    """API root endpoint."""
    return {
        "message": "Welcome to MyCreditLens API",
        "version": "1.0.0",
        "docs": "/api/docs",
    }
