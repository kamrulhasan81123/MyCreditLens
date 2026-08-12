"""application PD feature contract + richer prediction persistence

Adds the inference-safe application-PD inputs that the model requires
(Borrower.home_ownership, Borrower.employment_duration_years,
Application.loan_intent) and expands Prediction to persist the full scoring
record (raw vs calibrated probability, uncertainty, scoring mode, and
denormalised model / feature-schema versions).

All changes are additive and nullable, so existing rows are preserved.

Revision ID: 0002_application_pd_features
Revises: 0001_initial_schema
Create Date: 2026-08-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_application_pd_features"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

# Columns to add per table. Because 0001 creates tables from live model
# metadata (create_all), on a fresh database these columns already exist; on a
# legacy database migrated before they existed they do not. Each operation is
# therefore guarded by a column-existence check so the migration is correct and
# idempotent in both situations.
NEW_COLUMNS = {
    "borrowers": [
        ("home_ownership", sa.String(length=20)),
        ("employment_duration_years", sa.Float()),
    ],
    "applications": [
        ("loan_intent", sa.String(length=30)),
    ],
    "predictions": [
        ("raw_probability", sa.Float()),
        ("calibrated_probability", sa.Float()),
        ("uncertainty", sa.Float()),
        ("scoring_mode", sa.String(length=30)),
        ("model_version", sa.String(length=50)),
        ("feature_schema_version", sa.String(length=50)),
    ],
}


def _existing_columns(table: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col["name"] for col in inspector.get_columns(table)}


def upgrade() -> None:
    for table, columns in NEW_COLUMNS.items():
        present = _existing_columns(table)
        to_add = [(name, type_) for name, type_ in columns if name not in present]
        if not to_add:
            continue
        with op.batch_alter_table(table) as batch:
            for name, type_ in to_add:
                batch.add_column(sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    for table, columns in NEW_COLUMNS.items():
        present = _existing_columns(table)
        to_drop = [name for name, _ in columns if name in present]
        if not to_drop:
            continue
        with op.batch_alter_table(table) as batch:
            for name in reversed(to_drop):
                batch.drop_column(name)
