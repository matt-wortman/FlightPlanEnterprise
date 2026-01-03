#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, date
import random
from typing import Iterable
from uuid import UUID, uuid4

from sqlalchemy import select, func

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.infrastructure.event_store import EventStore, EventToAppend
from app.models.event_store import EventModel
from app.projections.read_model_projections import (
    AdmissionProjection,
    FlightPlanProjection,
    PatientProjection,
    TimelineProjection,
    AttachmentProjection,
)


FIRST_NAMES = [
    "Avery",
    "Jordan",
    "Morgan",
    "Cameron",
    "Riley",
    "Quinn",
    "Peyton",
    "Reese",
    "Skyler",
    "Casey",
    "Rowan",
    "Harper",
    "Sydney",
    "Emerson",
    "Sage",
]

LAST_NAMES = [
    "Patel",
    "Rivera",
    "Nguyen",
    "Kim",
    "Garcia",
    "Clark",
    "Sullivan",
    "Torres",
    "Brooks",
    "Mitchell",
    "Bennett",
    "Reed",
    "Hayes",
    "Shaw",
    "Bell",
]

CHIEF_COMPLAINTS = [
    "Chest pain",
    "Shortness of breath",
    "Post-op monitoring",
    "Arrhythmia evaluation",
    "Congenital heart defect",
    "Valve disorder",
]

LOCATIONS = ["ED", "OR", "CICU", "PICU", "Floor", "Discharge"]

PROCEDURES = [
    "CABG",
    "Valve repair",
    "Cardiac cath",
    "ECMO cannulation",
    "Atrial septal defect repair",
]

RISK_LEVELS = ["low", "moderate", "high", "critical"]


@dataclass
class SeedEvent:
    stream_id: UUID
    stream_type: str
    event_type: str
    data: dict
    created_by: UUID
    occurred_at: datetime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed the event store with synthetic data.")
    parser.add_argument("--patients", type=int, default=25)
    parser.add_argument("--admissions-per-patient", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--tenant-id", default=None)
    parser.add_argument("--created-by", default="00000000-0000-0000-0000-000000000001")
    parser.add_argument("--specialty", default="cardiac")
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def random_date_of_birth(rng: random.Random) -> date:
    today = date.today()
    years = rng.randint(1, 75)
    days = rng.randint(0, 364)
    return today - timedelta(days=years * 365 + days)


def build_seed_events(
    rng: random.Random,
    patient_count: int,
    created_by: UUID,
    specialty: str,
    admissions_per_patient: int,
) -> list[SeedEvent]:
    events: list[SeedEvent] = []
    now = datetime.now(timezone.utc)

    admissions_per_patient = max(1, admissions_per_patient)
    for _ in range(patient_count):
        patient_id = uuid4()

        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        dob = random_date_of_birth(rng)
        mrn_token = f"TOK-{uuid4().hex[:12]}"

        admission_dates = [
            now
            - timedelta(
                days=rng.randint(1, 200) + admission_index * rng.randint(30, 120),
                hours=rng.randint(0, 23),
            )
            for admission_index in range(admissions_per_patient)
        ]
        admission_dates.sort()
        earliest_admit = min(admission_dates)

        patient_event = SeedEvent(
            stream_id=patient_id,
            stream_type="Patient",
            event_type="patient.created",
            data={
                "patient_id": str(patient_id),
                "name": f"{first} {last}",
                "mrn": mrn_token,
                "date_of_birth": dob.isoformat(),
                "gender": rng.choice(["male", "female", "other", "unknown"]),
                "legacy_fields": {"seeded": True},
            },
            created_by=created_by,
            occurred_at=earliest_admit - timedelta(days=rng.randint(1, 7)),
        )
        events.append(patient_event)

        for admission_index, admit_date in enumerate(admission_dates):
            admission_id = uuid4()
            flightplan_id = uuid4()

            admission_event = SeedEvent(
                stream_id=admission_id,
                stream_type="Admission",
                event_type="admission.created",
                data={
                    "admission_id": str(admission_id),
                    "patient_id": str(patient_id),
                    "specialty": specialty,
                    "attending_id": str(uuid4()),
                    "admit_date": admit_date.isoformat(),
                    "chief_complaint": rng.choice(CHIEF_COMPLAINTS),
                    "admission_type": rng.choice(["emergency", "elective", "transfer"]),
                },
                created_by=created_by,
                occurred_at=admit_date,
            )
            events.append(admission_event)

            flightplan_event = SeedEvent(
                stream_id=flightplan_id,
                stream_type="FlightPlan",
                event_type="flightplan.created",
                data={
                    "flightplan_id": str(flightplan_id),
                    "admission_id": str(admission_id),
                    "status": rng.choice(["draft", "active", "completed"]),
                },
                created_by=created_by,
                occurred_at=admit_date + timedelta(hours=2),
            )
            events.append(flightplan_event)

            location_path = _build_location_path(rng)
            loc_time = admit_date
            prev_location = None
            for location in location_path:
                loc_time += timedelta(hours=rng.randint(6, 36))
                events.append(
                    SeedEvent(
                        stream_id=admission_id,
                        stream_type="Admission",
                        event_type="admission.location_changed",
                        data={
                            "admission_id": str(admission_id),
                            "from_location": prev_location,
                            "to_location": location,
                            "from_bed": None,
                            "to_bed": None,
                            "effective_at": loc_time.isoformat(),
                            "reason": None,
                        },
                        created_by=created_by,
                        occurred_at=loc_time,
                    )
                )
                prev_location = location

            for _ in range(rng.randint(2, 5)):
                event_time = admit_date + timedelta(hours=rng.randint(4, 120))
                events.append(
                    SeedEvent(
                        stream_id=admission_id,
                        stream_type="Admission",
                        event_type="clinical_event.recorded",
                        data={
                            "event_id": str(uuid4()),
                            "admission_id": str(admission_id),
                            "event_type": rng.choice(["procedure", "consultation", "annotation"]),
                            "occurred_at": event_time.isoformat(),
                            "details": {"label": rng.choice(PROCEDURES)},
                            "notes": "Synthetic clinical note.",
                        },
                        created_by=created_by,
                        occurred_at=event_time,
                    )
                )

            for _ in range(rng.randint(1, 3)):
                event_time = admit_date + timedelta(hours=rng.randint(6, 96))
                events.append(
                    SeedEvent(
                        stream_id=admission_id,
                        stream_type="Admission",
                        event_type="clinical_event.recorded",
                        data={
                            "event_id": str(uuid4()),
                            "admission_id": str(admission_id),
                            "event_type": "risk_status",
                            "occurred_at": event_time.isoformat(),
                            "risk_level": rng.choice(RISK_LEVELS),
                            "risk_score": rng.randint(1, 5),
                            "location": rng.choice(LOCATIONS[:-1]),
                            "notes": "Synthetic risk note.",
                        },
                        created_by=created_by,
                        occurred_at=event_time,
                    )
                )

            if rng.random() > 0.6:
                attachment_time = admit_date + timedelta(hours=rng.randint(8, 140))
                events.append(
                    SeedEvent(
                        stream_id=admission_id,
                        stream_type="Admission",
                        event_type="attachment.added",
                        data={
                            "attachment_id": str(uuid4()),
                            "admission_id": str(admission_id),
                            "occurred_at": attachment_time.isoformat(),
                            "storage_key": f"synthetic/{uuid4().hex}.pdf",
                            "filename": "Synthetic Note.pdf",
                            "description": "Synthetic attachment",
                            "attachment_type": "note",
                            "content_type": "application/pdf",
                            "thumbnail_key": None,
                            "linked_event_id": None,
                        },
                        created_by=created_by,
                        occurred_at=attachment_time,
                    )
                )

    return events


def _build_location_path(rng: random.Random) -> list[str]:
    base = ["ED", "OR", "CICU", "Floor", "Discharge"]
    if rng.random() > 0.6:
        base.insert(2, "PICU")
    return base


async def _current_global_position(session) -> int:
    result = await session.execute(select(func.max(EventModel.global_position)))
    value = result.scalar_one_or_none()
    return int(value or 0)


async def _project_from_position(
    store: EventStore,
    session,
    start_position: int,
) -> int:
    position = start_position
    projections = [
        PatientProjection(session, store.tenant_id),
        AdmissionProjection(session, store.tenant_id),
        FlightPlanProjection(session, store.tenant_id),
        TimelineProjection(session, store.tenant_id),
        AttachmentProjection(session, store.tenant_id),
    ]
    while True:
        events = await store.get_all_events_since(position=position, limit=200)
        if not events:
            break
        for event in events:
            for projection in projections:
                await projection.handle(event)
            position = event["global_position"]
        await session.flush()
    return position


async def seed_database(
    events: list[SeedEvent],
    tenant_id: UUID,
    batch_size: int,
    dry_run: bool,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    async with async_session_factory() as session:
        store = EventStore(session=session, tenant_id=tenant_id)
        start_position = await _current_global_position(session)

        for idx, event in enumerate(sorted(events, key=lambda e: (e.stream_id, e.occurred_at))):
            counts[event.event_type] = counts.get(event.event_type, 0) + 1
            if dry_run:
                continue
            payload = EventToAppend(
                event_type=event.event_type,
                data=event.data,
                metadata={"source": "synthetic_seed"},
                created_by=event.created_by,
            )
            await store.append(
                stream_id=event.stream_id,
                stream_type=event.stream_type,
                events=[payload],
                expected_version=None,
            )
            if (idx + 1) % batch_size == 0:
                await session.commit()

        if not dry_run:
            await session.commit()
            await _project_from_position(store, session, start_position)
            await session.commit()

    return {"total": len(events), **counts}


def main() -> None:
    args = parse_args()
    settings = get_settings()
    tenant_id = UUID(args.tenant_id or str(settings.default_tenant_id))
    created_by = UUID(args.created_by)

    rng = random.Random(args.seed)
    events = build_seed_events(
        rng,
        args.patients,
        created_by,
        args.specialty,
        args.admissions_per_patient,
    )
    counts = asyncio.run(seed_database(events, tenant_id, args.batch_size, args.dry_run))

    print("Seed complete.")
    print(f"Total events: {counts.get('total', 0)}")
    for key, value in sorted(counts.items()):
        if key == "total":
            continue
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
