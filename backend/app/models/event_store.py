from datetime import datetime
import uuid

from sqlalchemy import BigInteger, DateTime, Integer, String, Index, UniqueConstraint, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.types import GUID


class EventModel(Base):
    __tablename__ = "events"

    event_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    stream_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    stream_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(200), nullable=False)
    event_version: Mapped[int] = mapped_column(Integer, nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)

    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)

    global_position: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("stream_id", "event_version", name="uq_stream_version"),
        Index("idx_events_stream", "stream_id", "event_version"),
        Index("idx_events_type", "event_type", "created_at"),
        Index("idx_events_tenant", "tenant_id", "created_at"),
        Index("idx_events_global_position", "global_position"),
        Index("idx_events_created_at", "created_at"),
    )


class SnapshotModel(Base):
    __tablename__ = "snapshots"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    stream_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    stream_type: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("stream_id", "version", name="uq_stream_snapshot"),
        Index("idx_snapshots_stream", "stream_id", "version"),
    )


class SubscriptionModel(Base):
    __tablename__ = "subscriptions"

    subscription_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    last_position: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_subscriptions_updated", "updated_at"),
    )
