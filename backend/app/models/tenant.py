import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, JSON, func, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.types import GUID


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subdomain: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)

    plan: Mapped[str] = mapped_column(String(50), default="standard")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    features: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled_specialties: Mapped[list] = mapped_column(JSON, default=list)
    branding: Mapped[dict] = mapped_column(JSON, default=dict)
    integrations: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_tenants_active", "is_active"),
    )
