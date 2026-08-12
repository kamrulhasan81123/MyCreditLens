"""widen engineered_features.feature_version to VARCHAR(64)

The feature version string ``transaction_features_v1`` (23 chars) exceeds the
original VARCHAR(20). SQLite silently allowed it; PostgreSQL enforces the length.
Widen to 64.

Revision ID: 0003_widen_feature_version
Revises: 0002_application_pd_features
Create Date: 2026-08-13
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_widen_feature_version"
down_revision = "0002_application_pd_features"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("engineered_features") as batch:
        batch.alter_column("feature_version", type_=sa.String(length=64), existing_type=sa.String(length=20), existing_nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("engineered_features") as batch:
        batch.alter_column("feature_version", type_=sa.String(length=20), existing_type=sa.String(length=64), existing_nullable=False)
