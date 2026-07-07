#!/usr/bin/env python3
"""Dry-run/apply Traderie PostgreSQL retention pruning with audit rows."""

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


def _where(args: argparse.Namespace, keys: list[str]) -> tuple[str, dict[str, Any]]:
    clauses = []
    params: dict[str, Any] = {"segment": args.segment, "keys": keys or None, "retention_days": args.retention_days}
    if args.segment:
        clauses.append("ct.segment_slug = %(segment)s")
    if keys:
        clauses.append("ct.observation_key = ANY(%(keys)s)")
    else:
        clauses.append("ct.captured_at < now() - (%(retention_days)s::text || ' days')::interval")
    return " AND ".join(clauses) if clauses else "true", params


def preview_completed_trades(conn, args: argparse.Namespace, keys: list[str]) -> dict[str, Any]:
    where_sql, params = _where(args, keys)
    sql = f"""
        SELECT
            COUNT(*) AS eligible_completed_trades,
            COALESCE(SUM(price_entry_count), 0) AS expected_price_entries_from_trade_rows,
            MIN(captured_at) AS oldest_captured_at,
            MAX(captured_at) AS newest_captured_at
        FROM app.completed_trades ct
        WHERE {where_sql}
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = dict(cur.fetchone())
    conn.commit()
    return row


def _assert_writer(cur) -> None:
    cur.execute("SELECT current_user")
    current_user = cur.fetchone()["current_user"]
    if current_user != PG_WRITER_USER:
        raise RuntimeError(f"Refusing prune mutation as {current_user}; expected {PG_WRITER_USER}")


def apply_completed_trade_prune(conn, args: argparse.Namespace, keys: list[str]) -> dict[str, Any]:
    if not args.i_understand_this_deletes_rows:
        raise RuntimeError("Refusing apply without --i-understand-this-deletes-rows")
    if not keys and not args.allow_retention_window_apply:
        raise RuntimeError("Refusing broad retention apply without --allow-retention-window-apply")

    where_sql, params = _where(args, keys)
    with conn.cursor() as cur:
        _assert_writer(cur)
        cur.execute(
            f"""
            SELECT ct.trade_observation_id, ct.segment_slug, ct.observation_key, to_jsonb(ct) AS payload
            FROM app.completed_trades ct
            WHERE {where_sql}
            ORDER BY ct.captured_at, ct.trade_observation_id
            LIMIT %(batch_size)s
            """,
            {**params, "batch_size": args.batch_size},
        )
        rows = cur.fetchall()
        if not rows:
            conn.commit()
            return {"archived_rows": 0, "deleted_completed_trades": 0}

        for row in rows:
            cur.execute(
                """
                INSERT INTO archive.prune_archive_audit (
                    segment_slug, observation_key, source_table, archived_payload, metadata
                )
                VALUES (%s, %s, 'app.completed_trades', %s::jsonb, %s::jsonb)
                """,
                (
                    row["segment_slug"],
                    row["observation_key"],
                    json.dumps(row["payload"], sort_keys=True, default=str),
                    json.dumps({"tool": "traderie_prune.py", "retention_days": args.retention_days, "key_limited": bool(keys)}, sort_keys=True),
                ),
            )
            cur.execute(
                """
                INSERT INTO app.prune_audit (
                    segment_slug, observation_key, trade_observation_id, action, reason_code, source_table, archive_table, metadata
                )
                VALUES (%s, %s, %s, 'archived', %s, 'app.completed_trades', 'archive.prune_archive_audit', %s::jsonb)
                """,
                (
                    row["segment_slug"],
                    row["observation_key"],
                    row["trade_observation_id"],
                    "pilot_key_prune" if keys else "retention_window",
                    json.dumps({"tool": "traderie_prune.py"}, sort_keys=True),
                ),
            )

        trade_ids = [row["trade_observation_id"] for row in rows]
        cur.execute(
            "DELETE FROM app.completed_trades WHERE trade_observation_id = ANY(%s::uuid[])",
            (trade_ids,),
        )
        deleted = cur.rowcount
        for row in rows:
            cur.execute(
                """
                INSERT INTO app.prune_audit (
                    segment_slug, observation_key, action, reason_code, source_table, archive_table, metadata
                )
                VALUES (%s, %s, 'pruned', %s, 'app.completed_trades', 'archive.prune_archive_audit', %s::jsonb)
                """,
                (
                    row["segment_slug"],
                    row["observation_key"],
                    "pilot_key_prune" if keys else "retention_window",
                    json.dumps({"tool": "traderie_prune.py", "deleted_in_batch": True}, sort_keys=True),
                ),
            )
        cur.execute("ANALYZE app.completed_trades")
        cur.execute("ANALYZE app.price_entries")
    conn.commit()
    return {"archived_rows": len(rows), "deleted_completed_trades": deleted}


def prune_aggregates(conn, args: argparse.Namespace) -> dict[str, int]:
    if not args.i_understand_this_deletes_rows:
        raise RuntimeError("Refusing aggregate apply without --i-understand-this-deletes-rows")
    if args.aggregate_granularity == "hourly":
        cutoff = "30 days"
    elif args.aggregate_granularity == "daily":
        cutoff = "365 days"
    else:
        raise ValueError("aggregate granularity must be hourly or daily")
    with conn.cursor() as cur:
        _assert_writer(cur)
        cur.execute(
            """
            DELETE FROM app.segment_aggregates
            WHERE granularity = %s
              AND bucket_start < now() - %s::interval
            """,
            (args.aggregate_granularity, cutoff),
        )
        deleted = cur.rowcount
        cur.execute(
            """
            INSERT INTO app.prune_audit (segment_slug, action, reason_code, source_table, metadata)
            VALUES ('pc_sc_l', 'pruned', 'aggregate_retention_window', 'app.segment_aggregates', %s::jsonb)
            """,
            (json.dumps({"tool": "traderie_prune.py", "granularity": args.aggregate_granularity, "rows_deleted": deleted}, sort_keys=True),),
        )
    conn.commit()
    return {"deleted_segment_aggregates": deleted}


def main() -> None:
    parser = argparse.ArgumentParser(description="Traderie retention prune")
    parser.add_argument("--table", choices=["completed_trades", "aggregates"], default="completed_trades")
    parser.add_argument("--segment")
    parser.add_argument("--retention-days", type=int, default=7)
    parser.add_argument("--observation-key-file")
    parser.add_argument("--aggregate-granularity", choices=["hourly", "daily"], default="hourly")
    parser.add_argument("--batch-size", type=int, default=10000)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-retention-window-apply", action="store_true")
    parser.add_argument("--i-understand-this-deletes-rows", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.apply and args.dry_run:
        parser.error("choose only one of --apply or --dry-run")
    if not args.apply:
        args.dry_run = True

    keys = _read_keys(args.observation_key_file)
    conn = _pg_connect()
    try:
        if args.table == "completed_trades":
            summary = preview_completed_trades(conn, args, keys)
        else:
            summary = {"table": "app.segment_aggregates", "granularity": args.aggregate_granularity}
        report = {
            "project": "traderie",
            "mode": "apply" if args.apply else "dry-run",
            "table": args.table,
            "segment": args.segment,
            "observation_key_limited": bool(keys),
            "summary": summary,
        }
        if args.apply and args.table == "completed_trades":
            report["apply_result"] = apply_completed_trade_prune(conn, args, keys)
            report["apply_ok"] = True
        elif args.apply:
            report["apply_result"] = prune_aggregates(conn, args)
            report["apply_ok"] = True
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
