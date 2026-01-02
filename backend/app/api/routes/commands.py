from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.tenant import get_tenant_id
from app.infrastructure.event_store import EventStore, EventToAppend

router = APIRouter(prefix="/api/v1", tags=["commands"])

class AdmissionCreate(BaseModel):
    admission_id: UUID
    patient_id: UUID
    specialty: str
    attending_id: UUID
    admit_date: datetime
    chief_complaint: str | None = None
    admission_type: str | None = None
    created_by: UUID


class LocationChange(BaseModel):
    from_location: str | None = None
    to_location: str
    from_bed: str | None = None
    to_bed: str | None = None
    effective_at: datetime
    reason: str | None = None
    created_by: UUID


class ClinicalEventCreate(BaseModel):
    event_id: UUID
    admission_id: UUID
    event_type: str
    occurred_at: datetime
    data: dict[str, Any] = Field(default_factory=dict)
    created_by: UUID


@router.post("/admissions")
async def create_admission(
    payload: AdmissionCreate,
    session: AsyncSession = Depends(get_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, Any]:
    event_store = EventStore(session=session, tenant_id=tenant_id)
    event = EventToAppend(
        event_type="admission.created",
        data={
            "admission_id": str(payload.admission_id),
            "patient_id": str(payload.patient_id),
            "specialty": payload.specialty,
            "attending_id": str(payload.attending_id),
            "admit_date": payload.admit_date.isoformat(),
            "chief_complaint": payload.chief_complaint,
            "admission_type": payload.admission_type,
        },
        metadata={},
        created_by=payload.created_by,
    )
    new_version = await event_store.append(
        stream_id=payload.admission_id,
        stream_type="Admission",
        events=[event],
        expected_version=None,
    )
    await session.commit()
    return {"new_version": new_version}


@router.post("/admissions/{admission_id}/location")
async def change_location(
    admission_id: UUID,
    payload: LocationChange,
    session: AsyncSession = Depends(get_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, Any]:
    event_store = EventStore(session=session, tenant_id=tenant_id)
    event = EventToAppend(
        event_type="admission.location_changed",
        data={
            "admission_id": str(admission_id),
            "from_location": payload.from_location,
            "to_location": payload.to_location,
            "from_bed": payload.from_bed,
            "to_bed": payload.to_bed,
            "effective_at": payload.effective_at.isoformat(),
            "reason": payload.reason,
        },
        metadata={},
        created_by=payload.created_by,
    )
    new_version = await event_store.append(
        stream_id=admission_id,
        stream_type="Admission",
        events=[event],
        expected_version=None,
    )
    await session.commit()
    return {"new_version": new_version}


@router.post("/clinical-events")
async def record_clinical_event(
    payload: ClinicalEventCreate,
    session: AsyncSession = Depends(get_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, Any]:
    event_store = EventStore(session=session, tenant_id=tenant_id)
    event = EventToAppend(
        event_type="clinical_event.recorded",
        data={
            "event_id": str(payload.event_id),
            "admission_id": str(payload.admission_id),
            "event_type": payload.event_type,
            "occurred_at": payload.occurred_at.isoformat(),
            **payload.data,
        },
        metadata={},
        created_by=payload.created_by,
    )
    new_version = await event_store.append(
        stream_id=payload.admission_id,
        stream_type="Admission",
        events=[event],
        expected_version=None,
    )
    await session.commit()
    return {"new_version": new_version}
