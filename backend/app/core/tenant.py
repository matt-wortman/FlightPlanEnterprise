from contextvars import ContextVar
from uuid import UUID

from fastapi import Request

from app.core.config import get_settings

current_tenant: ContextVar[UUID | None] = ContextVar("current_tenant", default=None)


def get_tenant_id(request: Request) -> UUID:
    settings = get_settings()
    header_value = request.headers.get("X-Tenant-ID")
    tenant_id = UUID(header_value) if header_value else UUID(settings.default_tenant_id)
    current_tenant.set(tenant_id)
    return tenant_id
