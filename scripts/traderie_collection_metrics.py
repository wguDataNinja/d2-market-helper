#!/usr/bin/env python3
"""Persist Traderie collection-run metrics without changing collector logic."""

import argparse
import json
import os
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.traderie_pg_adapter import PG_URL_ENV_VAR


PG_DATABASE = os.environ.get("TRADERIE_PG_DATABASE", "traderie")
PG_WRITER_USER = os.environ.get("TRADERIE_PG_WRITER_USER", "traderie_writer")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _pg_connect():
    import psycopg2
    from psycopg2 import sql

    pg_url = os.environ.get(PG_URL_ENV_VAR, "").strip()
    if pg_url:
        conn = psycopg2.connect(pg_url)
    else:
        login_user = os.environ.get("TRADERIE_PG_LOGIN_USER") or os.environ.get("PGUSER")
        kwargs = {
            "database": PG_DATABASE,
            "host": os.environ.get("PGHOST", ""),
            "port": os.environ.get("PGPORT", "5432"),
        }
        if login_user:
            kwargs["user"] = login_user
        conn = psycopg2.connect(**kwargs)
    conn.autocommit = False
    with conn.cursor() as cur:
        cur.execute("SELECT current_user")
        current_user = cur.fetchone()[0]
        if current_user != PG_WRITER_USER:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", PG_WRITER_USER):
                raise RuntimeError("Invalid PostgreSQL writer role name")
            cur.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(PG_WRITER_USER)))
    conn.commit()
    return conn


def _load_input(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_metrics(args: argparse.Namespace, payload: dict[str, Any]) -> dict[str, Any]:
    started_at = args.started_at or payload.get("started_at") or _utc_now()
    completed_at = args.completed_at or payload.get("completed_at") or payload.get("finished_at")
    records_returned = int(args.records_returned if args.records_returned is not None else payload.get("records_returned", payload.get("records_read", 0)))
    records_new = int(args.records_new if args.records_new is not None else payload.get("records_new", payload.get("records_written", 0)))
    records_skipped = int(args.records_skipped_duplicate if args.records_skipped_duplicate is not None else payload.get("records_skipped_duplicate", max(records_returned - records_new, 0)))
    denominator = records_new + records_skipped
    duplicate_ratio = (records_skipped / denominator) if denominator else None
    segment_breakdown = payload.get("segment_breakdown") or {}

    return {
        "workflow": args.workflow or payload.get("workflow", "traderie_collection"),
        "source_id": args.source_id or payload.get("source_id", "traderie"),
        "source_slug": args.source_slug or payload.get("source_slug", "traderie"),
        "segment_slug": args.segment or payload.get("segment_slug"),
        "trigger_type": args.trigger_type or payload.get("trigger_type", "manual"),
        "started_at": started_at,
        "completed_at": completed_at,
        "elapsed_ms": args.elapsed_ms if args.elapsed_ms is not None else payload.get("elapsed_ms"),
        "requests_made": int(args.requests_made if args.requests_made is not None else payload.get("requests_made", 0)),
        "response_bytes": int(args.response_bytes if args.response_bytes is not None else payload.get("response_bytes", 0)),
        "records_returned": records_returned,
        "records_new": records_new,
        "records_skipped_duplicate": records_skipped,
        "duplicate_ratio": duplicate_ratio,
        "retries": int(args.retries if args.retries is not None else payload.get("retries", payload.get("retry_count", 0))),
        "failures": int(args.failures if args.failures is not None else payload.get("failures", 0)),
        "stop_reason": args.stop_reason or payload.get("stop_reason", "completed"),
        "collector_version": args.collector_version or payload.get("collector_version") or f"python-{platform.python_version()}",
        "error_summary": payload.get("error_summary") or {},
        "source_diagnostics": payload.get("source_diagnostics") or {},
        "segment_breakdown": segment_breakdown,
    }


def insert_metrics(metrics: dict[str, Any]) -> str:
    with _pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_user")
            current_user = cur.fetchone()[0]
            if current_user != PG_WRITER_USER:
                raise RuntimeError(f"Refusing metrics mutation as {current_user}; expected {PG_WRITER_USER}")
            cur.execute(
                """
                INSERT INTO app.collection_run_metrics (
                    workflow, source_id, source_slug, segment_slug, trigger_type,
                    started_at, completed_at, elapsed_ms, requests_made, response_bytes,
                    records_returned, records_new, records_skipped_duplicate, duplicate_ratio,
                    retries, failures, stop_reason, collector_version,
                    error_summary, source_diagnostics, segment_breakdown
                )
                VALUES (
                    %(workflow)s, %(source_id)s, %(source_slug)s, %(segment_slug)s, %(trigger_type)s,
                    %(started_at)s, %(completed_at)s, %(elapsed_ms)s, %(requests_made)s, %(response_bytes)s,
                    %(records_returned)s, %(records_new)s, %(records_skipped_duplicate)s, %(duplicate_ratio)s,
                    %(retries)s, %(failures)s, %(stop_reason)s, %(collector_version)s,
                    %(error_summary)s::jsonb, %(source_diagnostics)s::jsonb, %(segment_breakdown)s::jsonb
                )
                RETURNING run_id
                """,
                {
                    **metrics,
                    "error_summary": json.dumps(metrics["error_summary"], sort_keys=True),
                    "source_diagnostics": json.dumps(metrics["source_diagnostics"], sort_keys=True),
                    "segment_breakdown": json.dumps(metrics["segment_breakdown"], sort_keys=True),
                },
            )
            run_id = cur.fetchone()[0]
        conn.commit()
    return str(run_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Persist Traderie collection metrics to PostgreSQL")
    parser.add_argument("--input-json", help="Metrics JSON file, or '-' for stdin")
    parser.add_argument("--apply", action="store_true", help="Insert into app.collection_run_metrics")
    parser.add_argument("--dry-run", action="store_true", help="Print metrics only")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument("--workflow")
    parser.add_argument("--source-id")
    parser.add_argument("--source-slug")
    parser.add_argument("--segment")
    parser.add_argument("--trigger-type", choices=["scheduled", "manual", "backfill", "retry", "pilot"])
    parser.add_argument("--started-at")
    parser.add_argument("--completed-at")
    parser.add_argument("--elapsed-ms", type=int)
    parser.add_argument("--requests-made", type=int)
    parser.add_argument("--response-bytes", type=int)
    parser.add_argument("--records-returned", type=int)
    parser.add_argument("--records-new", type=int)
    parser.add_argument("--records-skipped-duplicate", type=int)
    parser.add_argument("--retries", type=int)
    parser.add_argument("--failures", type=int)
    parser.add_argument("--stop-reason")
    parser.add_argument("--collector-version")
    args = parser.parse_args()

    if args.apply and args.dry_run:
        parser.error("choose only one of --apply or --dry-run")
    if not args.apply:
        args.dry_run = True

    metrics = build_metrics(args, _load_input(args.input_json))
    report = {"project": "traderie", "mode": "apply" if args.apply else "dry-run", "metrics": metrics}
    if args.apply:
        report["run_id"] = insert_metrics(metrics)
        report["insert_ok"] = True

    if args.json or args.dry_run:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(f"Inserted collection metrics row {report['run_id']}")


if __name__ == "__main__":
    main()
