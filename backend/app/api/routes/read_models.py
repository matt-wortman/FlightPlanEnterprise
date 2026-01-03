from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.tenant import get_tenant_id
from app.models.read_models import (
    PatientReadModel,
    AdmissionReadModel,
    FlightPlanReadModel,
    TimelineEventModel,
    TrajectoryPointModel,
    AttachmentReadModel,
)

router = APIRouter(prefix="/api/v1", tags=["read-models"])


@router.get("/patients")
async def list_patients(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, Any]:
    result = await session.execute(
        select(PatientReadModel)
        .where(PatientReadModel.tenant_id == tenant_id)
        .offset(offset)
        .limit(limit)
    )
    rows = result.scalars().all()
    return {"items": [r.data for r in rows], "limit": limit, "offset": offset}


@router.get("/patients/{patient_id}")
async def get_patient(
    patient_id: UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, Any]:
    result = await session.execute(
        select(PatientReadModel)
        .where(PatientReadModel.tenant_id == tenant_id)
        .where(PatientReadModel.id == patient_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return {"detail": "not found"}
    return row.data


@router.get("/admissions")
async def list_admissions(
    patient_id: Optional[UUID] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, Any]:
    query = select(AdmissionReadModel).where(AdmissionReadModel.tenant_id == tenant_id)
    if patient_id:
        query = query.where(AdmissionReadModel.patient_id == patient_id)
    result = await session.execute(query.offset(offset).limit(limit))
    rows = result.scalars().all()
    return {"items": [r.data for r in rows], "limit": limit, "offset": offset}


@router.get("/flightplans/{flightplan_id}")
async def get_flightplan(
    flightplan_id: UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, Any]:
    result = await session.execute(
        select(FlightPlanReadModel)
        .where(FlightPlanReadModel.tenant_id == tenant_id)
        .where(FlightPlanReadModel.id == flightplan_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return {"detail": "not found"}
    return row.data


@router.get("/admissions/{admission_id}/timeline")
async def get_timeline(
    admission_id: UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, Any]:
    result = await session.execute(
        select(TimelineEventModel)
        .where(TimelineEventModel.tenant_id == tenant_id)
        .where(TimelineEventModel.admission_id == admission_id)
        .order_by(TimelineEventModel.occurred_at)
    )
    rows = result.scalars().all()
    return {"items": [r.data for r in rows]}


@router.get("/admissions/{admission_id}/trajectory")
async def get_trajectory(
    admission_id: UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, Any]:
    result = await session.execute(
        select(TrajectoryPointModel)
        .where(TrajectoryPointModel.tenant_id == tenant_id)
        .where(TrajectoryPointModel.admission_id == admission_id)
        .order_by(TrajectoryPointModel.effective_at)
    )
    rows = result.scalars().all()
    return {"items": [r.data for r in rows]}


@router.get("/admissions/{admission_id}/attachments")
async def get_attachments(
    admission_id: UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, Any]:
    result = await session.execute(
        select(AttachmentReadModel)
        .where(AttachmentReadModel.tenant_id == tenant_id)
        .where(AttachmentReadModel.admission_id == admission_id)
        .order_by(AttachmentReadModel.occurred_at)
    )
    rows = result.scalars().all()
    return {"items": [r.data for r in rows]}
