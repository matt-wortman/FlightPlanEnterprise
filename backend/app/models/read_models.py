from datetime import datetime
import uuid

from sqlalchemy import DateTime, String, Index, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.types import GUID


class PatientReadModel(Base):
    __tablename__ = "patient_read_models"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_patient_tenant", "tenant_id"),
    )


class AdmissionReadModel(Base):
    __tablename__ = "admission_read_models"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_admission_tenant", "tenant_id"),
        Index("idx_admission_patient", "patient_id"),
    )


class FlightPlanReadModel(Base):
    __tablename__ = "flightplan_read_models"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    admission_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_flightplan_tenant", "tenant_id"),
        Index("idx_flightplan_admission", "admission_id"),
    )


class TimelineEventModel(Base):
    __tablename__ = "timeline_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    admission_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    event_type: Mapped[str] = mapped_column(String(200), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        Index("idx_timeline_tenant", "tenant_id"),
        Index("idx_timeline_admission", "admission_id"),
        Index("idx_timeline_occurred", "occurred_at"),
    )


class TrajectoryPointModel(Base):
    __tablename__ = "trajectory_points"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    admission_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        Index("idx_trajectory_tenant", "tenant_id"),
        Index("idx_trajectory_admission", "admission_id"),
        Index("idx_trajectory_effective", "effective_at"),
    )


class AttachmentReadModel(Base):
    __tablename__ = "attachment_read_models"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    admission_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        Index("idx_attachment_tenant", "tenant_id"),
        Index("idx_attachment_admission", "admission_id"),
        Index("idx_attachment_occurred", "occurred_at"),
    )
