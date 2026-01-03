"""attachment read models

Revision ID: 003_attachment_read_models
Revises: 002_read_models_and_tenants
Create Date: 2026-01-03 09:00:00

"""
from alembic import op
import sqlalchemy as sa

from app.models.types import GUID

# revision identifiers, used by Alembic.
revision = "003_attachment_read_models"
down_revision = "002_read_models_and_tenants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attachment_read_models",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("tenant_id", GUID(), nullable=False),
        sa.Column("admission_id", GUID(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
    )
    op.create_index("idx_attachment_tenant", "attachment_read_models", ["tenant_id"])
    op.create_index("idx_attachment_admission", "attachment_read_models", ["admission_id"])
    op.create_index("idx_attachment_occurred", "attachment_read_models", ["occurred_at"])


def downgrade() -> None:
    op.drop_index("idx_attachment_occurred", table_name="attachment_read_models")
    op.drop_index("idx_attachment_admission", table_name="attachment_read_models")
    op.drop_index("idx_attachment_tenant", table_name="attachment_read_models")
    op.drop_table("attachment_read_models")
