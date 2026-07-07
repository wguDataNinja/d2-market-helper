#!/usr/bin/env python3
"""Generate Traderie hourly/daily PostgreSQL price aggregates."""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.traderie_pg_adapter import PG_URL_ENV_VAR


PG_DATABASE = os.environ.get("TRADERIE_PG_DATABASE", "traderie")
PG_WRITER_USER = os.environ.get("TRADERIE_PG_WRITER_USER", "traderie_writer")


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
    conn.autocommit = False
    with conn.cursor() as cur:
        cur.execute("SELECT current_user")
        current_user = cur.fetchone()["current_user"]
        if current_user != PG_WRITER_USER:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", PG_WRITER_USER):
                raise RuntimeError("Invalid PostgreSQL writer role name")
            cur.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(PG_WRITER_USER)))
    conn.commit()
    return conn


def _read_keys(path: str | None) -> list[str]:
    if not path:
        return []
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def _bucket_expr(granularity: str) -> str:
    if granularity not in {"hourly", "daily"}:
        raise ValueError(f"unsupported granularity: {granularity}")
    return "hour" if granularity == "hourly" else "day"


def _params(args: argparse.Namespace, keys: list[str]) -> dict[str, Any]:
    return {
        "segment": args.segment,
        "since": args.since,
        "until": args.until,
        "keys": keys or None,
        "granularity": args.granularity,
        "source_id": args.source_id,
        "source_slug": args.source_slug,
        "run_id": args.run_id,
    }


def preview(conn, args: argparse.Namespace, keys: list[str]) -> dict[str, Any]:
    unit = _bucket_expr(args.granularity)
    sql = f"""
        WITH source_rows AS (
            SELECT
                ct.segment_slug,
                rr.rune_id,
                date_trunc('{unit}', ct.captured_at) AS bucket_start,
                (pe.quantity::numeric / GREATEST(ct.quantity, 1)) AS value_ist,
                ct.trade_observation_id
            FROM app.completed_trades ct
            JOIN app.price_entries pe ON pe.trade_id = ct.trade_observation_id
            JOIN app.rune_registry rr ON lower(rr.name) = lower(ct.item_name)
            WHERE (%(segment)s IS NULL OR ct.segment_slug = %(segment)s)
              AND (%(since)s IS NULL OR ct.captured_at >= %(since)s::timestamptz)
              AND (%(until)s IS NULL OR ct.captured_at < %(until)s::timestamptz)
              AND (%(keys)s IS NULL OR ct.observation_key = ANY(%(keys)s))
              AND pe.item_name = 'Ist Rune'
              AND COALESCE(pe.add_flag, false) = false
              AND COALESCE(ct.completed, true) = true
        )
        SELECT
            COUNT(*) AS source_observations,
            COUNT(DISTINCT (segment_slug, rune_id, bucket_start)) AS aggregate_buckets,
            MIN(bucket_start) AS oldest_bucket,
            MAX(bucket_start) AS newest_bucket
        FROM source_rows
    """
    with conn.cursor() as cur:
        cur.execute(sql, _params(args, keys))
        row = dict(cur.fetchone())
    conn.commit()
    return row


def apply_aggregates(conn, args: argparse.Namespace, keys: list[str]) -> int:
    unit = _bucket_expr(args.granularity)
    interval = "1 hour" if args.granularity == "hourly" else "1 day"
    sql = f"""
        WITH source_rows AS (
            SELECT
                ct.segment_slug,
                rr.rune_id,
                date_trunc('{unit}', ct.captured_at) AS bucket_start,
                (date_trunc('{unit}', ct.captured_at) + interval '{interval}') AS bucket_end,
                (pe.quantity::numeric / GREATEST(ct.quantity, 1)) AS value_ist,
                ct.quantity::numeric AS volume,
                ct.trade_observation_id,
                ct.captured_at
            FROM app.completed_trades ct
            JOIN app.price_entries pe ON pe.trade_id = ct.trade_observation_id
            JOIN app.rune_registry rr ON lower(rr.name) = lower(ct.item_name)
            WHERE (%(segment)s IS NULL OR ct.segment_slug = %(segment)s)
              AND (%(since)s IS NULL OR ct.captured_at >= %(since)s::timestamptz)
              AND (%(until)s IS NULL OR ct.captured_at < %(until)s::timestamptz)
              AND (%(keys)s IS NULL OR ct.observation_key = ANY(%(keys)s))
              AND pe.item_name = 'Ist Rune'
              AND COALESCE(pe.add_flag, false) = false
              AND COALESCE(ct.completed, true) = true
        ),
        grouped AS (
            SELECT
                segment_slug,
                rune_id,
                bucket_start,
                bucket_end,
                COUNT(*)::integer AS observation_count,
                COUNT(DISTINCT trade_observation_id)::integer AS trade_count,
                SUM(volume)::numeric(18,6) AS volume_total,
                AVG(value_ist)::numeric(18,6) AS vwap,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY value_ist)::numeric(18,6) AS median_price,
                MIN(value_ist)::numeric(18,6) AS min_price,
                MAX(value_ist)::numeric(18,6) AS max_price,
                MIN(captured_at) AS first_seen_at,
                MAX(captured_at) AS last_seen_at
            FROM source_rows
            GROUP BY segment_slug, rune_id, bucket_start, bucket_end
        )
        INSERT INTO app.segment_aggregates (
            bucket_start, bucket_end, source_id, source_slug, segment_slug, rune_id, granularity,
            observation_count, trade_count, volume_total, vwap, median_price, min_price, max_price,
            first_seen_at, last_seen_at, run_id, generation_metadata
        )
        SELECT
            bucket_start, bucket_end, %(source_id)s, %(source_slug)s, segment_slug, rune_id, %(granularity)s,
            observation_count, trade_count, volume_total, vwap, median_price, min_price, max_price,
            first_seen_at, last_seen_at, %(run_id)s,
            jsonb_build_object('tool', 'traderie_aggregate_generation.py', 'key_limited', %(keys)s IS NOT NULL)
        FROM grouped
        ON CONFLICT (COALESCE(source_id, ''), segment_slug, rune_id, bucket_start, granularity)
        DO UPDATE SET
            bucket_end = EXCLUDED.bucket_end,
            observation_count = EXCLUDED.observation_count,
            trade_count = EXCLUDED.trade_count,
            volume_total = EXCLUDED.volume_total,
            vwap = EXCLUDED.vwap,
            median_price = EXCLUDED.median_price,
            min_price = EXCLUDED.min_price,
            max_price = EXCLUDED.max_price,
            first_seen_at = EXCLUDED.first_seen_at,
            last_seen_at = EXCLUDED.last_seen_at,
            run_id = EXCLUDED.run_id,
            generation_metadata = EXCLUDED.generation_metadata
    """
    with conn.cursor() as cur:
        cur.execute("SELECT current_user")
        current_user = cur.fetchone()["current_user"]
        if current_user != PG_WRITER_USER:
            raise RuntimeError(f"Refusing aggregate mutation as {current_user}; expected {PG_WRITER_USER}")
        cur.execute(sql, _params(args, keys))
        affected = cur.rowcount
    conn.commit()
    return affected


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Traderie segment aggregates")
    parser.add_argument("--granularity", choices=["hourly", "daily"], default="hourly")
    parser.add_argument("--segment")
    parser.add_argument("--since")
    parser.add_argument("--until")
    parser.add_argument("--observation-key-file")
    parser.add_argument("--source-id", default="traderie")
    parser.add_argument("--source-slug", default="traderie")
    parser.add_argument("--run-id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.apply and args.dry_run:
        parser.error("choose only one of --apply or --dry-run")
    if not args.apply:
        args.dry_run = True

    keys = _read_keys(args.observation_key_file)
    conn = _pg_connect()
    try:
        summary = preview(conn, args, keys)
        report = {
            "project": "traderie",
            "mode": "apply" if args.apply else "dry-run",
            "granularity": args.granularity,
            "segment": args.segment,
            "observation_key_limited": bool(keys),
            "summary": summary,
        }
        if args.apply:
            report["affected_aggregate_rows"] = apply_aggregates(conn, args, keys)
            report["apply_ok"] = True
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
