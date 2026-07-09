#!/usr/bin/env python3
"""Traderie health export — canonical v2 JSON.

Default mode reads fixture data, applies redaction, and outputs sanitized JSON.
When --pg is supplied, reads PostgreSQL health/retention summaries using the
configured local connection without printing credentials.

Usage:
    python3 scripts/traderie_health_export.py [--output /tmp/traderie.health.json]

Produces the portfolio v2 health contract payload.
See docs/HEALTH_CONTRACT.md (ivy-control-vps).
"""

import argparse
import json
import logging
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.traderie_pg_adapter import PG_URL_ENV_VAR

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PG_DATABASE = os.environ.get("TRADERIE_PG_DATABASE", "traderie")
PG_READER_USER = os.environ.get("TRADERIE_PG_READER_USER", "traderie_reader")
PG_HEALTH_WRITER_USER = os.environ.get("TRADERIE_PG_HEALTH_WRITER_USER", "traderie_owner")

# SHARED-003 prohibited fields (exact match)
PROHIBITED_FIELDS = frozenset({
    "error_message_private", "error_message", "raw_payload", "source_url",
    "filesystem_path", "credential", "api_key", "token", "cookie",
    "session_id", "browser_profile", "private_notes", "reviewer",
    "approval_detail", "backlog_detail", "ip_address", "hostname",
    "local_path", "stack_trace", "sql_error", "chat_body", "reddit_body",
    "raw_html", "raw_response",
})

# Redaction patterns for string values
REDACTION_PATTERNS = [
    (re.compile(r"/home/[a-zA-Z0-9_]+"), "/home/<redacted>"),
    (re.compile(r"/Users/[a-zA-Z0-9_]+"), "/Users/<redacted>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "<ip-redacted>"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "<api-key-redacted>"),
    (re.compile(r"ghp_[A-Za-z0-9]{36}"), "<token-redacted>"),
]


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        for pattern, replacement in REDACTION_PATTERNS:
            value = pattern.sub(replacement, value)
        return value
    return value


def redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key, value in data.items():
        if key in PROHIBITED_FIELDS:
            continue
        if isinstance(value, dict):
            result[key] = redact_dict(value)
        elif isinstance(value, list):
            result[key] = [redact_dict(v) if isinstance(v, dict) else redact_value(v) for v in value]
        else:
            result[key] = redact_value(value)
    return result


def transform_to_sanitized(private: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    now_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    project = private.get("project", "traderie")
    workflow = private.get("workflow", "unknown")
    workflow_id = f"{project}/{workflow}"

    freshness_seconds = 0
    if private.get("last_success_at") and private.get("last_success_at") != "unknown":
        try:
            last = datetime.fromisoformat(private["last_success_at"].replace("Z", "+00:00"))
            freshness_seconds = int((now - last).total_seconds())
        except (ValueError, TypeError):
            freshness_seconds = -1

    run_id = private.get("run_id") or str(uuid.uuid4())

    metadata = {}
    for key in ("cloudscraper_status", "snapshot_age", "product_age", "segment_status",
                "hardcore_degraded", "history_rows", "unique_listing_count",
                "largest_tables", "retention_health", "latest_collection_metrics",
                "latest_prune_audit", "row_counts", "storage_growth_bytes"):
        if key in private and private[key] is not None:
            metadata[key] = private[key]

    sanitized = {
        # Required core
        "contract_version": 2,
        "generated_at": now_str,
        "project": project,
        "workflow": workflow,
        "workflow_id": workflow_id,
        "run_id": run_id,
        "status": private.get("status", "unknown"),
        "started_at": private.get("started_at"),
        "finished_at": private.get("finished_at"),
        "last_success_at": private.get("last_success_at"),
        "expected_cadence_seconds": private.get("expected_cadence", 86400),
        "freshness_seconds": max(freshness_seconds, 0),
        "deployed_revision": private.get("deployed_revision"),
        "scheduler_state": private.get("scheduler_state", "unknown"),
        "backup_state": private.get("backup_state", "not_applicable"),
        "incident_state": private.get("incident_state", "none"),

        # Optional producer
        "records_read": private.get("records_read"),
        "records_written": private.get("records_written"),
        "records_rejected": private.get("records_rejected"),
        "backlog": private.get("backlog"),
        "retry_count": private.get("retry_count"),
        "error_class": private.get("error_class"),
        "schema_version": private.get("schema_version"),
        "migration_version": private.get("migration_version"),
        "backup_age_seconds": private.get("backup_age_seconds"),
        "storage_bytes": private.get("storage_bytes"),
        "storage_growth_bytes_24h": private.get("storage_growth_bytes_24h"),
        "database_size_bytes": private.get("database_size_bytes"),
        "data_directory_size_bytes": private.get("data_directory_size_bytes"),
        "prune_status": private.get("prune_status"),
        "disk_free_bytes": private.get("disk_free_bytes"),
        "disk_usage_pct": private.get("disk_usage_pct"),
        "producer_version": private.get("producer_version"),
        "project_environment": private.get("project_environment"),

        # Operator-only (stripped by redact_dict in public projection)
        "error_code": private.get("error_code"),
        "error_message_private": private.get("error_message_private"),

        # Traderie-specific metadata
        "metadata": metadata if metadata else None,
    }

    required_nullable = {"started_at", "finished_at", "last_success_at",
                         "deployed_revision", "error_code", "error_message_private"}
    return {k: v for k, v in sanitized.items() if v is not None or k in required_nullable}


def build_default_fixture_input() -> dict[str, Any]:
    """Build a synthetic health fixture (no real data)."""
    return {
        "project": "traderie",
        "workflow": "snapshot",
        "status": "ok",
        "started_at": "2026-07-05T05:00:00Z",
        "finished_at": "2026-07-05T05:05:00Z",
        "last_success_at": "2026-07-05T05:00:00Z",
        "expected_cadence": 21600,
        "records_read": 1250,
        "records_written": 1250,
        "records_rejected": 0,
        "backlog": 0,
        "retry_count": 0,
        "error_class": None,
        "error_code": None,
        "error_message_private": "/home/scraper/traderie/data/ error: socket.gaierror host=192.168.1.1",
        "deployed_revision": "abc123def456",
        "schema_version": 9,
        "migration_version": "20260705_009_create_health_schema",
        "scheduler_state": "active",
        "backup_state": "not_applicable",
        "storage_bytes": 2900000000,
        "storage_growth_bytes_24h": 120000000,
        "incident_state": "none",
        "storage_growth_bytes": 120000000,
        "cloudscraper_status": "ok",
        "snapshot_age": 300,
        "product_age": 3600,
        "segment_status": "ok",
        "hardcore_degraded": False,
        "history_rows": 99450,
        "unique_listing_count": 75000,
        "database_size_bytes": 9700000,
        "data_directory_size_bytes": 529000,
        "prune_status": "ok",
        "disk_free_bytes": 5800000000,
        "disk_usage_pct": 84.0,
        "producer_version": "traderie_health_export.py/2.0.0",
        "project_environment": "development",
    }


def _pg_connect():
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extras import RealDictCursor

    pg_url = os.environ.get(PG_URL_ENV_VAR, "").strip()
    if pg_url:
        conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
    else:
        login_user = os.environ.get("TRADERIE_PG_LOGIN_USER") or os.environ.get("PGUSER")
        kwargs = {
            "database": PG_DATABASE,
            "host": os.environ.get("PGHOST", ""),
            "port": os.environ.get("PGPORT", "5432"),
            "cursor_factory": RealDictCursor,
        }
        if login_user:
            kwargs["user"] = login_user
        conn = psycopg2.connect(**kwargs)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT current_user")
        current_user = cur.fetchone()["current_user"]
        if current_user != PG_READER_USER:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", PG_READER_USER):
                raise RuntimeError("Invalid PostgreSQL reader role name")
            cur.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(PG_READER_USER)))
    return conn


def _pg_connect_as_role(role: str, pg_url: str = ""):
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extras import RealDictCursor

    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", role):
        raise RuntimeError("Invalid PostgreSQL role name")

    if pg_url:
        conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
    else:
        login_user = os.environ.get("TRADERIE_PG_LOGIN_USER") or os.environ.get("PGUSER")
        kwargs = {
            "database": PG_DATABASE,
            "host": os.environ.get("PGHOST", ""),
            "port": os.environ.get("PGPORT", "5432"),
            "cursor_factory": RealDictCursor,
        }
        if login_user:
            kwargs["user"] = login_user
        conn = psycopg2.connect(**kwargs)
    conn.autocommit = True

    with conn.cursor() as cur:
        cur.execute("SELECT current_user")
        current_user = cur.fetchone()["current_user"]
        if current_user != role:
            cur.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(role)))
    return conn


def _fetch_one(cur, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any]:
    cur.execute(sql, params)
    row = cur.fetchone()
    return dict(row) if row else {}


def _fetch_all(cur, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cur.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


def build_pg_health_input() -> dict[str, Any]:
    """Read sanitized PostgreSQL health facts only."""
    import os
    import shutil

    with _pg_connect() as conn:
        with conn.cursor() as cur:
            latest_health = _fetch_one(
                cur,
                """
                SELECT workflow, status, last_success_at, expected_cadence, records_written,
                       error_class, backup_state, migration_version, schema_version,
                       deployed_revision, scheduler_state, incident_state,
                       records_read, records_rejected, backlog, retry_count, error_code
                FROM health.health_runs
                ORDER BY started_at DESC
                LIMIT 1
                """,
            )
            migration = _fetch_one(
                cur,
                "SELECT name, version FROM app.traderie_migrations ORDER BY version DESC LIMIT 1",
            )
            db_size = _fetch_one(cur, "SELECT pg_database_size(current_database()) AS database_size_bytes")
            largest_tables = _fetch_all(
                cur,
                """
                SELECT schemaname || '.' || relname AS table_name,
                       pg_total_relation_size(relid) AS total_bytes,
                       n_live_tup AS estimated_rows
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(relid) DESC
                LIMIT 3
                """,
            )
            row_counts = _fetch_one(
                cur,
                """
                SELECT
                  (SELECT COUNT(*) FROM app.completed_trades) AS completed_trades,
                  (SELECT COUNT(*) FROM app.price_entries) AS price_entries,
                  (SELECT COUNT(*) FROM app.collection_run_metrics) AS collection_run_metrics,
                  (SELECT COUNT(*) FROM app.segment_aggregates) AS segment_aggregates,
                  (SELECT COUNT(*) FROM app.prune_audit) AS prune_audit
                """,
            )
            retention = _fetch_one(
                cur,
                """
                SELECT
                  (SELECT COUNT(*) FROM app.completed_trades WHERE captured_at < now() - interval '7 days') AS completed_trades_eligible_7d,
                  (SELECT COUNT(*) FROM app.segment_aggregates WHERE granularity = 'hourly' AND bucket_start < now() - interval '30 days') AS hourly_aggregates_eligible_30d,
                  (SELECT COUNT(*) FROM app.segment_aggregates WHERE granularity = 'daily' AND bucket_start < now() - interval '365 days') AS daily_aggregates_eligible_365d,
                  (SELECT MAX(acted_at) FROM app.prune_audit) AS last_prune_at
                """,
            )
            latest_metrics = _fetch_one(
                cur,
                """
                SELECT workflow, trigger_type, started_at, completed_at, requests_made,
                       response_bytes, records_returned, records_new,
                       records_skipped_duplicate, duplicate_ratio, failures, stop_reason
                FROM app.collection_run_metrics
                ORDER BY started_at DESC
                LIMIT 1
                """,
            )
            latest_prune = _fetch_one(
                cur,
                """
                SELECT segment_slug, action, reason_code, source_table, archive_table, acted_at
                FROM app.prune_audit
                ORDER BY acted_at DESC
                LIMIT 1
                """,
            )
            backup_state_row = _fetch_one(
                cur,
                """
                SELECT backup_state, backup_age_seconds
                FROM health.health_runs
                WHERE backup_state IS NOT NULL AND backup_state != 'not_applicable'
                ORDER BY started_at DESC
                LIMIT 1
                """,
            )

    last_success = latest_health.get("last_success_at")

    # Derive prune_status from latest prune audit
    latest_prune_acted_at = latest_prune.get("acted_at") if latest_prune else None
    prune_status = "ok"
    if latest_prune_acted_at:
        try:
            prune_age = (datetime.now(timezone.utc) - latest_prune_acted_at).total_seconds()
            if prune_age > 35 * 86400:
                prune_status = "stale"
        except TypeError:
            prune_status = "unknown"

    # Filesystem disk stats from REPO_ROOT
    disk_free_bytes = None
    disk_usage_pct = None
    try:
        usage = shutil.disk_usage(REPO_ROOT)
        disk_free_bytes = usage.free
        disk_usage_pct = round((usage.used / usage.total) * 100, 2)
    except OSError:
        pass

    # Data directory size via env var or default
    data_directory_size_bytes = None
    data_root = os.environ.get("TRADERIE_DATA_ROOT", "")
    if data_root:
        try:
            data_dir = Path(data_root)
            if data_dir.is_dir():
                data_directory_size_bytes = sum(
                    f.stat().st_size for f in data_dir.rglob("*") if f.is_file()
                )
        except OSError:
            pass

    return {
        "project": "traderie",
        "workflow": latest_health.get("workflow", "postgres_health"),
        "status": latest_health.get("status", "ok"),
        "last_success_at": last_success.isoformat().replace("+00:00", "Z") if hasattr(last_success, "isoformat") else last_success,
        "expected_cadence": latest_health.get("expected_cadence", 21600) if isinstance(latest_health.get("expected_cadence"), (int, float)) else 21600,
        "records_read": latest_health.get("records_read"),
        "records_written": latest_health.get("records_written", 0),
        "records_rejected": latest_health.get("records_rejected"),
        "backlog": latest_health.get("backlog"),
        "retry_count": latest_health.get("retry_count"),
        "error_class": latest_health.get("error_class"),
        "error_code": latest_health.get("error_code"),
        "deployed_revision": latest_health.get("deployed_revision") or os.environ.get("TRADERIE_DEPLOYED_REVISION"),
        "schema_version": latest_health.get("schema_version") or migration.get("version"),
        "migration_version": latest_health.get("migration_version") or migration.get("name"),
        "scheduler_state": latest_health.get("scheduler_state", "unknown"),
        "backup_state": latest_health.get("backup_state", "unknown"),
        "backup_age_seconds": backup_state_row.get("backup_age_seconds") if backup_state_row else None,
        "incident_state": latest_health.get("incident_state", "none"),
        "database_size_bytes": db_size.get("database_size_bytes"),
        "storage_bytes": db_size.get("database_size_bytes"),
        "data_directory_size_bytes": data_directory_size_bytes,
        "prune_status": prune_status,
        "disk_free_bytes": disk_free_bytes,
        "disk_usage_pct": disk_usage_pct,
        "producer_version": "traderie_health_export.py/2.0.0",
        "project_environment": os.environ.get("TRADERIE_ENVIRONMENT", "development"),
        "largest_tables": largest_tables,
        "row_counts": row_counts,
        "retention_health": retention,
        "latest_collection_metrics": latest_metrics,
        "latest_prune_audit": latest_prune,
    }


def _migration_version_number(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    match = re.search(r"_(\d{3})(?:_|$)", str(value))
    if match:
        return int(match.group(1))
    try:
        return int(str(value))
    except ValueError:
        return None


def _count_records_read(private_data: dict[str, Any]) -> int:
    row_counts = private_data.get("row_counts")
    if not isinstance(row_counts, dict):
        return 0
    return sum(value for value in row_counts.values() if isinstance(value, int))


def _backup_state(value: Any) -> str:
    state = str(value or "").strip().lower()
    return state if state in {"ok", "stale", "fail"} else "ok"


def record_health_run(private_data: dict[str, Any]) -> str:
    """Insert one bounded health.health_runs row and return its run_id."""
    from psycopg2.extras import Json

    writer_url = os.environ.get("TRADERIE_PG_HEALTH_WRITER_URL", "").strip()
    now = datetime.now(timezone.utc)
    migration_version = _migration_version_number(private_data.get("migration_version")) or 17
    schema_version = _migration_version_number(private_data.get("schema_version")) or 17
    metadata = {
        "exporter": "scripts/traderie_health_export.py",
        "row_counts": private_data.get("row_counts", {}),
        "retention_health": private_data.get("retention_health", {}),
        "latest_collection_metrics": private_data.get("latest_collection_metrics", {}),
        "latest_prune_audit": private_data.get("latest_prune_audit", {}),
        "largest_tables": private_data.get("largest_tables", []),
    }

    with _pg_connect_as_role(PG_HEALTH_WRITER_USER, writer_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO health.health_runs
                    (workflow, status, started_at, finished_at, last_success_at,
                     expected_cadence, records_read, records_written,
                     records_rejected, backlog, retry_count, error_class,
                     error_code, deployed_revision, schema_version,
                     migration_version, scheduler_state, backup_state,
                     storage_bytes, storage_growth_bytes_24h, incident_state,
                     metadata)
                VALUES
                    (%s, %s, %s, %s, %s,
                     %s::interval, %s, %s,
                     %s, %s, %s, %s,
                     %s, %s, %s,
                     %s, %s, %s,
                     %s, %s, %s,
                     %s)
                RETURNING run_id
                """,
                (
                    "health_export",
                    private_data.get("status", "ok"),
                    now,
                    now,
                    now if private_data.get("status", "ok") == "ok" else None,
                    "6 hours",
                    _count_records_read(private_data),
                    1,
                    0,
                    0,
                    0,
                    private_data.get("error_class"),
                    private_data.get("error_code"),
                    os.environ.get("TRADERIE_DEPLOYED_REVISION", private_data.get("deployed_revision", "")),
                    schema_version,
                    migration_version,
                    os.environ.get("TRADERIE_SCHEDULER_STATE", "inert"),
                    _backup_state(private_data.get("backup_state")),
                    private_data.get("storage_bytes") or private_data.get("database_size_bytes"),
                    private_data.get("storage_growth_bytes_24h") or private_data.get("storage_growth_bytes"),
                    private_data.get("incident_state", "none"),
                    Json(metadata, dumps=lambda obj: json.dumps(obj, default=str)),
                ),
            )
            row = cur.fetchone()
    return str(row["run_id"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Traderie sanitized health export")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--input", "-i", help="Input JSON file with private health data")
    parser.add_argument("--pg", action="store_true", help="Read health and retention facts from PostgreSQL")
    args = parser.parse_args()

    if args.pg:
        private_data = build_pg_health_input()
        private_data["workflow"] = "health_export"
        private_data["health_run_id"] = record_health_run(private_data)
    elif args.input:
        with open(args.input) as f:
            private_data = json.load(f)
    else:
        private_data = build_default_fixture_input()

    sanitized = transform_to_sanitized(private_data)
    redacted = redact_dict(sanitized)

    output_path = args.output or "/dev/stdout"
    with open(output_path, "w") if output_path != "/dev/stdout" else sys.stdout as f:
        json.dump(redacted, f, indent=2, default=str)
        f.write("\n")

    logger.info("Health export written to %s", output_path)


if __name__ == "__main__":
    main()
