#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import heapq
import logging
import os
from pathlib import Path
from typing import Callable, Iterable, Iterator
from uuid import UUID

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.infrastructure.event_store import EventStore, EventToAppend
from app.legacy_import.mapping import (
    LegacyEvent,
    LegacyIdMapper,
    normalize_datetime,
    build_admission_event,
    build_annotation_event,
    build_attachment_event,
    build_bedside_procedure_event,
    build_conference_event,
    build_continuous_therapy_event,
    build_course_correction_event,
    build_feedback_event,
    build_location_event,
    build_patient_event,
    build_risk_event,
)


LOG = logging.getLogger("legacy_import")


@dataclass
class TableConfig:
    name: str
    timestamp_column: str
    order: int
    builder: Callable[[dict], LegacyEvent | None]


class LegacyRowSource:
    def iter_rows(self, table: str, order_by: str) -> Iterator[dict]:
        raise NotImplementedError


class JsonRowSource(LegacyRowSource):
    def __init__(self, path: Path) -> None:
        self._data = _load_json(path)

    def iter_rows(self, table: str, order_by: str) -> Iterator[dict]:
        rows = list(self._data.get(table, []))
        rows.sort(key=lambda r: normalize_datetime(r.get(order_by)))
        for row in rows:
            yield row


class SqlServerRowSource(LegacyRowSource):
    def __init__(self, host: str, port: int, database: str, user: str, password: str) -> None:
        self._host = host
        self._port = port
        self._database = database
        self._user = user
        self._password = password

    def iter_rows(self, table: str, order_by: str) -> Iterator[dict]:
        try:
            import pytds
        except ImportError as exc:
            raise RuntimeError(
                "pytds is required for SQL Server imports. Install python-tds in your backend venv."
            ) from exc

        conn = pytds.connect(
            server=self._host,
            port=self._port,
            database=self._database,
            user=self._user,
            password=self._password,
            autocommit=True,
        )
        try:
            cursor = conn.cursor()
            query = f"SELECT * FROM {table} ORDER BY {order_by}"
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            for row in cursor:
                yield dict(zip(columns, row))
        finally:
            conn.close()


def build_table_configs(
    mapper: LegacyIdMapper,
    created_by: UUID,
    specialty: str,
) -> list[TableConfig]:
    return [
        TableConfig(
            name="patients",
            timestamp_column="ActivityDate",
            order=0,
            builder=lambda row: build_patient_event(row, mapper, created_by),
        ),
        TableConfig(
            name="admissions",
            timestamp_column="ADMDATE",
            order=1,
            builder=lambda row: build_admission_event(row, mapper, created_by, specialty),
        ),
        TableConfig(
            name="location_steps",
            timestamp_column="EntryDatetime",
            order=2,
            builder=lambda row: build_location_event(row, mapper, created_by),
        ),
        TableConfig(
            name="location_risks",
            timestamp_column="StartDatetime",
            order=3,
            builder=lambda row: build_risk_event(row, mapper, created_by),
        ),
        TableConfig(
            name="annotations",
            timestamp_column="EntryDatetime",
            order=4,
            builder=lambda row: build_annotation_event(row, mapper, created_by),
        ),
        TableConfig(
            name="feedbacks",
            timestamp_column="EntryDatetime",
            order=5,
            builder=lambda row: build_feedback_event(row, mapper, created_by),
        ),
        TableConfig(
            name="conferences",
            timestamp_column="EntryDatetime",
            order=6,
            builder=lambda row: build_conference_event(row, mapper, created_by),
        ),
        TableConfig(
            name="bedside_procedures",
            timestamp_column="StartDatetime",
            order=7,
            builder=lambda row: build_bedside_procedure_event(row, mapper, created_by),
        ),
        TableConfig(
            name="continuous_therapy",
            timestamp_column="EntryDatetime",
            order=8,
            builder=lambda row: build_continuous_therapy_event(row, mapper, created_by),
        ),
        TableConfig(
            name="course_corrections",
            timestamp_column="EntryDatetime",
            order=9,
            builder=lambda row: build_course_correction_event(row, mapper, created_by),
        ),
        TableConfig(
            name="attachments",
            timestamp_column="EntryDatetime",
            order=10,
            builder=lambda row: build_attachment_event(row, mapper, created_by),
        ),
    ]


def iter_events(
    row_source: LegacyRowSource,
    table_configs: list[TableConfig],
    max_events: int | None,
) -> Iterator[LegacyEvent]:
    streams: list[tuple[TableConfig, Iterator[LegacyEvent]]] = []
    for config in table_configs:
        stream = _iter_table_events(row_source, config)
        streams.append((config, stream))

    heap: list[tuple[datetime, int, int, LegacyEvent, Iterator[LegacyEvent]]] = []
    for idx, (config, stream) in enumerate(streams):
        try:
            event = next(stream)
        except StopIteration:
            continue
        heapq.heappush(
            heap,
            (event.occurred_at, config.order, idx, event, stream),
        )

    emitted = 0
    while heap:
        _, _, idx, event, stream = heapq.heappop(heap)
        yield event
        emitted += 1
        if max_events is not None and emitted >= max_events:
            return
        try:
            next_event = next(stream)
            heapq.heappush(
                heap,
                (next_event.occurred_at, table_configs[idx].order, idx, next_event, stream),
            )
        except StopIteration:
            continue


def _iter_table_events(row_source: LegacyRowSource, config: TableConfig) -> Iterator[LegacyEvent]:
    for row in row_source.iter_rows(config.name, config.timestamp_column):
        event = config.builder(row)
        if event:
            yield event


async def import_events(
    events: Iterable[LegacyEvent],
    tenant_id: UUID,
    batch_size: int,
    dry_run: bool,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    processed = 0
    async with async_session_factory() as session:
        store = EventStore(session=session, tenant_id=tenant_id)
        for event in events:
            counts[event.event_type] = counts.get(event.event_type, 0) + 1
            processed += 1
            if dry_run:
                continue
            payload = EventToAppend(
                event_type=event.event_type,
                data=event.data,
                metadata={
                    **event.metadata,
                    "imported_at": datetime.now(timezone.utc).isoformat(),
                },
                created_by=event.created_by,
            )
            await store.append(
                stream_id=event.stream_id,
                stream_type=event.stream_type,
                events=[payload],
                expected_version=None,
            )
            if processed % batch_size == 0:
                await session.commit()
        if not dry_run:
            await session.commit()
    return {"total": processed, **counts}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import legacy v2 SQL Server data into the enterprise event store.",
    )
    parser.add_argument("--legacy-json", help="Path to JSON export of legacy tables.")
    parser.add_argument("--legacy-host", default=os.getenv("LEGACY_DB_HOST", "localhost"))
    parser.add_argument("--legacy-port", type=int, default=int(os.getenv("LEGACY_DB_PORT", "11433")))
    parser.add_argument("--legacy-db", default=os.getenv("LEGACY_DB_NAME", "FlightPlan"))
    parser.add_argument("--legacy-user", default=os.getenv("LEGACY_DB_USER", "sa"))
    parser.add_argument("--legacy-password", default=os.getenv("LEGACY_DB_PASSWORD"))
    parser.add_argument("--tenant-id", default=os.getenv("DEFAULT_TENANT_ID"))
    parser.add_argument("--created-by", default=os.getenv("LEGACY_IMPORT_USER_ID"))
    parser.add_argument("--mapping-file", default=os.getenv("LEGACY_MAPPING_FILE"))
    parser.add_argument("--specialty", default=os.getenv("LEGACY_SPECIALTY", "cardiac"))
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--max-events", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=args.log_level.upper(), format="%(levelname)s %(message)s")

    if not args.tenant_id:
        settings = get_settings()
        args.tenant_id = str(settings.default_tenant_id)

    if not args.created_by:
        raise SystemExit("created-by is required (LEGACY_IMPORT_USER_ID or --created-by).")

    mapper = LegacyIdMapper.from_env(mapping_file=args.mapping_file)

    tenant_id = UUID(args.tenant_id)
    created_by = UUID(args.created_by)

    if args.legacy_json:
        row_source: LegacyRowSource = JsonRowSource(Path(args.legacy_json))
    else:
        if not args.legacy_password:
            raise SystemExit("legacy-password is required (LEGACY_DB_PASSWORD or --legacy-password).")
        row_source = SqlServerRowSource(
            host=args.legacy_host,
            port=args.legacy_port,
            database=args.legacy_db,
            user=args.legacy_user,
            password=args.legacy_password,
        )

    table_configs = build_table_configs(mapper, created_by, args.specialty)
    event_stream = iter_events(row_source, table_configs, args.max_events)

    LOG.info("Starting legacy import (dry_run=%s)", args.dry_run)
    counts = asyncio.run(
        import_events(
            events=event_stream,
            tenant_id=tenant_id,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
        )
    )
    mapper.save()
    LOG.info("Import complete. Total events: %s", counts.get("total", 0))
    for key, value in sorted(counts.items()):
        if key == "total":
            continue
        LOG.info("  %s: %s", key, value)


def _load_json(path: Path) -> dict:
    import json

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


if __name__ == "__main__":
    main()
