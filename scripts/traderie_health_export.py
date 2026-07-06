#!/usr/bin/env python3
"""Traderie health export — sanitized JSON matching SHARED-003 schema.

INERT / DRY-RUN ONLY. Reads fixture data, applies redaction filter,
and outputs sanitized JSON. Does NOT read production snapshots or
connect to any database.

Usage:
    python3 scripts/traderie_health_export.py [--output /tmp/traderie.health.json]

See CODEX_SESSION_1_ARCHITECTURE.md §8 and SHARED-003_HEALTH_CONTRACT.md.
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

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
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    freshness = 0
    if private.get("last_success_at") and private.get("last_success_at") != "unknown":
        try:
            last = datetime.fromisoformat(private["last_success_at"].replace("Z", "+00:00"))
            freshness = int((datetime.now(timezone.utc) - last).total_seconds())
        except (ValueError, TypeError):
            freshness = -1

    sanitized = {
        "schema_version": 1,
        "generated_at": now,
        "project": private.get("project", "traderie"),
        "workflow": private.get("workflow", "unknown"),
        "status": private.get("status", "unknown"),
        "last_success": private.get("last_success_at"),
        "freshness": max(freshness, 0),
        "expected_cadence": private.get("expected_cadence", 86400),
        "volume_24h": private.get("records_written", 0),
        "incident": private.get("incident_state", "none") == "active",
        "degraded_reason_code": private.get("error_code") or private.get("error_class"),
        "backup_state": private.get("backup_state", "not_applicable"),
        "migration_version": private.get("migration_version"),
        "storage_growth_bytes": private.get("storage_growth_bytes"),
        "cloudscraper_status": private.get("cloudscraper_status"),
        "snapshot_age": private.get("snapshot_age"),
        "product_age": private.get("product_age"),
        "segment_status": private.get("segment_status"),
        "hardcore_degraded": private.get("hardcore_degraded"),
        "history_rows": private.get("history_rows"),
        "unique_listing_count": private.get("unique_listing_count"),
    }
    return {k: v for k, v in sanitized.items() if v is not None or k in ("schema_version", "generated_at", "project", "workflow", "freshness", "expected_cadence", "incident")}


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
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Traderie sanitized health export")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--input", "-i", help="Input JSON file with private health data")
    args = parser.parse_args()

    if args.input:
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

    logger.info("Dry-run health export written to %s", output_path)


if __name__ == "__main__":
    main()
