from pathlib import Path

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


# Directory that contains the backend package (…/backend). Relative artifact
# paths are resolved against this so scoring behaves identically whether the
# process starts from the repo root, the backend dir, or a test runner.
BACKEND_DIR = Path(__file__).resolve().parents[1]

INSECURE_JWT_DEFAULT = "change-me-to-a-random-secret-key"


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./mycreditlens.db"
    database_url_sync: str = "sqlite:///./mycreditlens.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = Field(
        default=INSECURE_JWT_DEFAULT,
        validation_alias=AliasChoices("JWT_SECRET", "JWT_SECRET_KEY"),
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    auth_provider: str = "hybrid"

    # App
    app_env: str = "development"
    debug: bool = True
    cors_origins: list[str] = ["http://localhost:3000"]

    # File Storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    # Model artifacts. Points at the active application-PD bundle. Relative
    # paths are resolved against the backend package via
    # `resolved_model_artifact_path` (CWD-independent).
    model_artifact_path: str = "./ml/artifacts/application_pd"
    require_model_artifacts: bool = True
    allow_demo_scoring: bool = False

    # MLflow
    mlflow_tracking_uri: str = "http://localhost:5000"

    # Supabase (optional until configured)
    supabase_url: str | None = None
    supabase_publishable_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SUPABASE_PUBLISHABLE_KEY", "SUPABASE_ANON_KEY"),
    )
    supabase_secret_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SUPABASE_SECRET_KEY", "SUPABASE_SERVICE_ROLE_KEY"),
    )
    supabase_jwt_issuer: str | None = None
    supabase_jwt_audience: str | None = None
    supabase_jwks_url: str | None = None
    supabase_storage_bucket: str = "financial-documents"
    # Verify TLS on OUTBOUND calls to Supabase (JWKS / Auth / Storage). Default
    # True (secure, for production). Set False ONLY in environments behind a
    # TLS-inspecting proxy that presents a private CA (e.g. this sandbox), where
    # public CA verification cannot succeed.
    supabase_verify_ssl: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _enforce_secret_outside_development(self) -> "Settings":
        # Fail fast in any non-development environment if the JWT secret is
        # missing or still the shipped placeholder. Development/test keep
        # working with the insecure default so local MVP execution is not
        # blocked. The secret value itself is never logged.
        if self.app_env not in {"development", "test"}:
            if not self.jwt_secret_key or self.jwt_secret_key == INSECURE_JWT_DEFAULT:
                raise ValueError(
                    "JWT_SECRET must be set to a strong, non-default value when "
                    f"APP_ENV={self.app_env!r}. Refusing to start with an insecure secret."
                )
        return self

    @property
    def uses_insecure_jwt_secret(self) -> bool:
        return (not self.jwt_secret_key) or self.jwt_secret_key == INSECURE_JWT_DEFAULT

    @property
    def resolved_model_artifact_path(self) -> Path:
        """Absolute artifact directory, anchored to the backend package when the
        configured path is relative. Prevents CWD-dependent 503s in tests."""
        configured = Path(self.model_artifact_path)
        if configured.is_absolute():
            return configured
        return (BACKEND_DIR / configured).resolve()

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
