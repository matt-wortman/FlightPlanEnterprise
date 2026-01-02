"""event store schema

Revision ID: 001_event_store
Revises: 
Create Date: 2026-01-02 12:10:00

"""
from alembic import op
import sqlalchemy as sa

from app.models.types import GUID

# revision identifiers, used by Alembic.
revision = "001_event_store"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("event_id", GUID(), primary_key=True),
        sa.Column("stream_id", GUID(), nullable=False),
        sa.Column("stream_type", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=200), nullable=False),
        sa.Column("event_version", sa.Integer(), nullable=False),
        sa.Column("tenant_id", GUID(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", GUID(), nullable=False),
        sa.Column("global_position", sa.BigInteger(), unique=True, nullable=False),
        sa.UniqueConstraint("stream_id", "event_version", name="uq_stream_version"),
    )
    op.create_index("idx_events_stream", "events", ["stream_id", "event_version"])
    op.create_index("idx_events_type", "events", ["event_type", "created_at"])
    op.create_index("idx_events_tenant", "events", ["tenant_id", "created_at"])
    op.create_index("idx_events_global_position", "events", ["global_position"])
    op.create_index("idx_events_created_at", "events", ["created_at"])

    op.create_table(
        "snapshots",
        sa.Column("snapshot_id", GUID(), primary_key=True),
        sa.Column("stream_id", GUID(), nullable=False),
        sa.Column("stream_type", sa.String(length=100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("stream_id", "version", name="uq_stream_snapshot"),
    )
    op.create_index("idx_snapshots_stream", "snapshots", ["stream_id", "version"])

    op.create_table(
        "subscriptions",
        sa.Column("subscription_id", sa.String(length=200), primary_key=True),
        sa.Column("last_position", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_subscriptions_updated", "subscriptions", ["updated_at"])


def downgrade() -> None:
    op.drop_index("idx_subscriptions_updated", table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_index("idx_snapshots_stream", table_name="snapshots")
    op.drop_table("snapshots")

    op.drop_index("idx_events_created_at", table_name="events")
    op.drop_index("idx_events_global_position", table_name="events")
    op.drop_index("idx_events_tenant", table_name="events")
    op.drop_index("idx_events_type", table_name="events")
    op.drop_index("idx_events_stream", table_name="events")
    op.drop_table("events")
