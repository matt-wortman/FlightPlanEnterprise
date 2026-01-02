"""read models and tenant tables

Revision ID: 002_read_models_and_tenants
Revises: 001_event_store
Create Date: 2026-01-02 13:00:00

"""
from alembic import op
import sqlalchemy as sa

from app.models.types import GUID

# revision identifiers, used by Alembic.
revision = "002_read_models_and_tenants"
down_revision = "001_event_store"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("subdomain", sa.String(length=100), unique=True, nullable=True),
        sa.Column("plan", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("features", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("enabled_specialties", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("branding", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("integrations", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_tenants_active", "tenants", ["is_active"])

    op.create_table(
        "patient_read_models",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("tenant_id", GUID(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_patient_tenant", "patient_read_models", ["tenant_id"])

    op.create_table(
        "admission_read_models",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("tenant_id", GUID(), nullable=False),
        sa.Column("patient_id", GUID(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_admission_tenant", "admission_read_models", ["tenant_id"])
    op.create_index("idx_admission_patient", "admission_read_models", ["patient_id"])

    op.create_table(
        "flightplan_read_models",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("tenant_id", GUID(), nullable=False),
        sa.Column("admission_id", GUID(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_flightplan_tenant", "flightplan_read_models", ["tenant_id"])
    op.create_index("idx_flightplan_admission", "flightplan_read_models", ["admission_id"])

    op.create_table(
        "timeline_events",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("tenant_id", GUID(), nullable=False),
        sa.Column("admission_id", GUID(), nullable=False),
        sa.Column("event_type", sa.String(length=200), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
    )
    op.create_index("idx_timeline_tenant", "timeline_events", ["tenant_id"])
    op.create_index("idx_timeline_admission", "timeline_events", ["admission_id"])
    op.create_index("idx_timeline_occurred", "timeline_events", ["occurred_at"])

    op.create_table(
        "trajectory_points",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("tenant_id", GUID(), nullable=False),
        sa.Column("admission_id", GUID(), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
    )
    op.create_index("idx_trajectory_tenant", "trajectory_points", ["tenant_id"])
    op.create_index("idx_trajectory_admission", "trajectory_points", ["admission_id"])
    op.create_index("idx_trajectory_effective", "trajectory_points", ["effective_at"])


def downgrade() -> None:
    op.drop_index("idx_trajectory_effective", table_name="trajectory_points")
    op.drop_index("idx_trajectory_admission", table_name="trajectory_points")
    op.drop_index("idx_trajectory_tenant", table_name="trajectory_points")
    op.drop_table("trajectory_points")

    op.drop_index("idx_timeline_occurred", table_name="timeline_events")
    op.drop_index("idx_timeline_admission", table_name="timeline_events")
    op.drop_index("idx_timeline_tenant", table_name="timeline_events")
    op.drop_table("timeline_events")

    op.drop_index("idx_flightplan_admission", table_name="flightplan_read_models")
    op.drop_index("idx_flightplan_tenant", table_name="flightplan_read_models")
    op.drop_table("flightplan_read_models")

    op.drop_index("idx_admission_patient", table_name="admission_read_models")
    op.drop_index("idx_admission_tenant", table_name="admission_read_models")
    op.drop_table("admission_read_models")

    op.drop_index("idx_patient_tenant", table_name="patient_read_models")
    op.drop_table("patient_read_models")

    op.drop_index("idx_tenants_active", table_name="tenants")
    op.drop_table("tenants")
