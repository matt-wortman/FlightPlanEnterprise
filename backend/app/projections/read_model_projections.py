from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.read_models import (
    PatientReadModel,
    AdmissionReadModel,
    FlightPlanReadModel,
    TimelineEventModel,
    TrajectoryPointModel,
)


class PatientProjection:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id

    async def handle(self, event: dict) -> None:
        if event["event_type"] != "patient.created":
            return

        data = event["data"]
        patient_id = UUID(data["patient_id"])

        existing = await self.session.get(PatientReadModel, patient_id)
        if existing:
            existing.data = data
            existing.updated_at = datetime.now(timezone.utc)
        else:
            self.session.add(
                PatientReadModel(
                    id=patient_id,
                    tenant_id=self.tenant_id,
                    data=data,
                )
            )


class AdmissionProjection:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id

    async def handle(self, event: dict) -> None:
        if event["event_type"] == "admission.created":
            data = event["data"]
            admission_id = UUID(data["admission_id"])
            patient_id = UUID(data["patient_id"])

            existing = await self.session.get(AdmissionReadModel, admission_id)
            if existing:
                existing.data = data
                existing.patient_id = patient_id
                existing.updated_at = datetime.now(timezone.utc)
            else:
                self.session.add(
                    AdmissionReadModel(
                        id=admission_id,
                        tenant_id=self.tenant_id,
                        patient_id=patient_id,
                        data=data,
                    )
                )

        if event["event_type"] == "admission.location_changed":
            data = event["data"]
            admission_id = UUID(data["admission_id"])
            location = data.get("to_location", "")
            effective_at = _parse_datetime(data.get("effective_at"))

            self.session.add(
                TrajectoryPointModel(
                    id=UUID(data.get("trajectory_id") or event["event_id"]),
                    tenant_id=self.tenant_id,
                    admission_id=admission_id,
                    location=location,
                    effective_at=effective_at,
                    data=data,
                )
            )


class FlightPlanProjection:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id

    async def handle(self, event: dict) -> None:
        if event["event_type"] != "flightplan.created":
            return

        data = event["data"]
        flightplan_id = UUID(data["flightplan_id"])
        admission_id = UUID(data["admission_id"])

        existing = await self.session.get(FlightPlanReadModel, flightplan_id)
        if existing:
            existing.data = data
            existing.admission_id = admission_id
            existing.updated_at = datetime.now(timezone.utc)
        else:
            self.session.add(
                FlightPlanReadModel(
                    id=flightplan_id,
                    tenant_id=self.tenant_id,
                    admission_id=admission_id,
                    data=data,
                )
            )


class TimelineProjection:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id

    async def handle(self, event: dict) -> None:
        if event["event_type"] != "clinical_event.recorded":
            return

        data = event["data"]
        admission_id = UUID(data["admission_id"])
        occurred_at = _parse_datetime(data.get("occurred_at"))

        self.session.add(
            TimelineEventModel(
                id=UUID(data.get("event_id") or event["event_id"]),
                tenant_id=self.tenant_id,
                admission_id=admission_id,
                event_type=data.get("event_type", event["event_type"]),
                occurred_at=occurred_at,
                data=data,
            )
        )


def _parse_datetime(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return datetime.now(timezone.utc)
