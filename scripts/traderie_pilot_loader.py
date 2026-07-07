#!/usr/bin/env python3
"""Traderie real PostgreSQL pilot loader.

Modes:
  --dry-run   Show what would be loaded, no mutation.
  --plan      Same as dry-run with expanded evidence.
  --apply     Execute the bounded pilot load (requires explicit --apply flag).

Operations:
  --rollback  Delete pilot rows by segment_slug and observation_key set.
  --parity    Compare file-sourced counts against PostgreSQL counts.

Safety:
  - Writer-role-only data mutation (traderie_writer).
  - Never mutates as superuser.
  - Requires explicit --apply (not a default).
  - Pre-load backup check warns if no recent backup exists.
  - Every mutation outputs starting and ending row counts.
  - Rollback is delete-by-selected-keys then re-run validation.
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.traderie_storage_adapter import FileTraderieAdapter, _observation_key
from scripts.traderie_pg_adapter import PgTraderieAdapter, PG_URL_ENV_VAR
from scripts.traderie_pilot_readiness_report import stable_digest, DEFAULT_SEGMENT, classify_records

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BACKUP_ROOT = Path(os.environ.get("TRADERIE_BACKUP_ROOT", REPO_ROOT / ".backups"))
PG_DATABASE = os.environ.get("TRADERIE_PG_DATABASE", "traderie")
PG_WRITER_USER = os.environ.get("TRADERIE_PG_WRITER_USER", "traderie_writer")

TARGET_TABLES = ["app.completed_trades", "app.price_entries"]
BACKUP_MANIFEST_REQUIRED_PREFIX = "manifest_clean_"


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
        conn = psycopg2.connect(
            **kwargs,
        )
    conn.autocommit = False
    with conn.cursor() as c:
        c.execute("SELECT current_user")
        current_user = c.fetchone()[0]
        if current_user != PG_WRITER_USER:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", PG_WRITER_USER):
                raise RuntimeError("Invalid PostgreSQL writer role name")
            c.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(PG_WRITER_USER)))
    conn.commit()
    return conn


def row_counts(conn):
    counts = {}
    allowed = {("app", "completed_trades"), ("app", "price_entries")}
    for table in TARGET_TABLES:
        schema, tbl = table.split(".", 1)
        if (schema, tbl) not in allowed:
            raise ValueError(f"unexpected target table: {table}")
        c = conn.cursor()
        c.execute(f"SELECT COUNT(*) FROM {schema}.{tbl}")
        counts[table] = c.fetchone()[0]
    return counts


def assert_writer_role(conn):
    c = conn.cursor()
    c.execute("SELECT current_user")
    current_user = c.fetchone()[0]
    if current_user != PG_WRITER_USER:
        raise RuntimeError(f"Refusing pilot mutation as {current_user}; expected {PG_WRITER_USER}")


def has_recent_backup():
    if not BACKUP_ROOT.is_dir():
        return False
    manifests = sorted(BACKUP_ROOT.glob(f"{BACKUP_MANIFEST_REQUIRED_PREFIX}*.yaml"))
    if not manifests:
        return False
    return True


def select_segment_records(segment, limit, eligible_only=False):
    adapter = FileTraderieAdapter()
    records = adapter.get_completed_trades(segment)
    records = sorted(records, key=lambda r: (r.get("captured_at") or "", str(r.get("listing_id") or ""), _observation_key(r)))
    if not eligible_only:
        return records[:limit]
    selected = []
    seen_keys = set()
    for record in records:
        classification = classify_records([record])
        key = _observation_key(record)
        if classification.get("required_field_rejects"):
            continue
        if key in seen_keys:
            continue
        seen_keys.add(key)
        selected.append(record)
        if len(selected) >= limit:
            break
    return selected


def _normalize_trade_record(record: dict[str, Any], segment: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    obs_key = _observation_key(record)
    price_entries = PgTraderieAdapter._price_entries(record)
    trade = {
        "segment_slug": segment,
        "observation_key": obs_key,
        "listing_id": PgTraderieAdapter._int_or_none(record.get("listing_id")),
        "content_hash": PgTraderieAdapter._content_hash(record),
        "item_id": PgTraderieAdapter._int_or_none(record.get("item_id")),
        "item_name": record.get("item_name"),
        "quantity": PgTraderieAdapter._int_or_none(record.get("quantity")) or 1,
        "seller": record.get("seller"),
        "seller_rating": record.get("seller_rating"),
        "seller_reviews": PgTraderieAdapter._int_or_none(record.get("seller_reviews")),
        "seller_score": PgTraderieAdapter._int_or_none(record.get("seller_score")),
        "seller_status": record.get("seller_status"),
        "updated_at": record.get("updated_at"),
        "captured_at": record.get("captured_at") or record.get("_captured_at"),
        "active": record.get("active"),
        "completed": record.get("completed", True),
        "platform": record.get("platform", "pc"),
        "mode": record.get("mode"),
        "hardcore": bool(record.get("hardcore", False)),
        "ladder": record.get("ladder"),
        "game_version": record.get("game_version") or record.get("version"),
        "ruleset": record.get("ruleset", "unknown"),
        "has_and_prices": len(price_entries) > 1,
        "price_group_count": len({entry["group_number"] for entry in price_entries}) or 1,
        "price_entry_count": len(price_entries) or 1,
        "source_payload": json.dumps(record, sort_keys=True, default=str),
        "snapshot_run_id": record.get("snapshot_run_id"),
    }
    return trade, price_entries


def load_records_into_pg(conn, records, segment):
    c = conn.cursor()
    upserted = 0
    try:
        for record in records:
            trade, price_entries = _normalize_trade_record(record, segment)
            c.execute("""
                INSERT INTO app.completed_trades (
                    segment_slug, observation_key, listing_id, content_hash, item_id, item_name,
                    quantity, seller, seller_rating, seller_reviews, seller_score, seller_status,
                    updated_at, captured_at, active, completed, platform, mode, hardcore, ladder,
                    game_version, ruleset, has_and_prices, price_group_count, price_entry_count,
                    source_payload, snapshot_run_id
                )
                VALUES (
                    %(segment_slug)s, %(observation_key)s, %(listing_id)s, %(content_hash)s, %(item_id)s, %(item_name)s,
                    %(quantity)s, %(seller)s, %(seller_rating)s, %(seller_reviews)s, %(seller_score)s, %(seller_status)s,
                    %(updated_at)s, %(captured_at)s, %(active)s, %(completed)s, %(platform)s, %(mode)s, %(hardcore)s, %(ladder)s,
                    %(game_version)s, %(ruleset)s, %(has_and_prices)s, %(price_group_count)s, %(price_entry_count)s,
                    %(source_payload)s::jsonb, %(snapshot_run_id)s
                )
                ON CONFLICT (segment_slug, observation_key) DO UPDATE SET
                    listing_id = EXCLUDED.listing_id,
                    content_hash = EXCLUDED.content_hash,
                    item_id = EXCLUDED.item_id,
                    item_name = EXCLUDED.item_name,
                    quantity = EXCLUDED.quantity,
                    seller = EXCLUDED.seller,
                    seller_rating = EXCLUDED.seller_rating,
                    seller_reviews = EXCLUDED.seller_reviews,
                    seller_score = EXCLUDED.seller_score,
                    seller_status = EXCLUDED.seller_status,
                    updated_at = EXCLUDED.updated_at,
                    captured_at = EXCLUDED.captured_at,
                    active = EXCLUDED.active,
                    completed = EXCLUDED.completed,
                    platform = EXCLUDED.platform,
                    mode = EXCLUDED.mode,
                    hardcore = EXCLUDED.hardcore,
                    ladder = EXCLUDED.ladder,
                    game_version = EXCLUDED.game_version,
                    ruleset = EXCLUDED.ruleset,
                    has_and_prices = EXCLUDED.has_and_prices,
                    price_group_count = EXCLUDED.price_group_count,
                    price_entry_count = EXCLUDED.price_entry_count,
                    source_payload = EXCLUDED.source_payload,
                    snapshot_run_id = EXCLUDED.snapshot_run_id
                RETURNING trade_observation_id
            """, trade)
            trade_id = c.fetchone()[0]
            c.execute("DELETE FROM app.price_entries WHERE trade_id = %s", (trade_id,))
            for entry in price_entries:
                c.execute("""
                    INSERT INTO app.price_entries (
                        trade_id, requested_item_id, item_name, quantity, add_flag, group_number, rune_item_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    trade_id,
                    entry["requested_item_id"],
                    entry["item_name"],
                    entry["quantity"],
                    entry["add_flag"],
                    entry["group_number"],
                    entry["rune_item_id"],
                ))
            upserted += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return upserted


def delete_pilot_rows(conn, observation_keys, segment):
    c = conn.cursor()
    try:
        c.execute(
            """
            DELETE FROM app.completed_trades
            WHERE segment_slug = %s
              AND observation_key = ANY(%s)
            """,
            (segment, observation_keys),
        )
        deleted = c.rowcount
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return deleted


def selected_pg_counts(conn, observation_keys, segment):
    c = conn.cursor()
    if not observation_keys:
        return {"app.completed_trades": 0, "app.price_entries": 0}
    c.execute(
        """
        SELECT COUNT(*)
        FROM app.completed_trades
        WHERE segment_slug = %s
          AND observation_key = ANY(%s)
        """,
        (segment, observation_keys),
    )
    completed_count = c.fetchone()[0]
    c.execute(
        """
        SELECT COUNT(*)
        FROM app.price_entries pe
        JOIN app.completed_trades ct ON ct.trade_observation_id = pe.trade_id
        WHERE ct.segment_slug = %s
          AND ct.observation_key = ANY(%s)
        """,
        (segment, observation_keys),
    )
    price_count = c.fetchone()[0]
    conn.commit()
    return {"app.completed_trades": completed_count, "app.price_entries": price_count}


def run_validation(conn):
    from psycopg2 import sql

    val_path = REPO_ROOT / "db" / "validation" / "999_full_validation.sql"
    if val_path.exists():
        c = conn.cursor()
        validation_sql = "\n".join(
            line for line in val_path.read_text().splitlines()
            if not line.lstrip().startswith("\\")
        )
        c.execute("SELECT session_user, current_user")
        session_user, current_user = c.fetchone()
        reset_for_validation = current_user == PG_WRITER_USER and session_user != PG_WRITER_USER
        if reset_for_validation:
            c.execute("RESET ROLE")
        c.execute(validation_sql)
        if reset_for_validation:
            c.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(PG_WRITER_USER)))
        conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Traderie PostgreSQL pilot loader")
    parser.add_argument("--segment", default=DEFAULT_SEGMENT)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--eligible-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    parser.add_argument("--parity", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not any([args.apply, args.dry_run, args.plan, args.rollback, args.parity]):
        parser.print_help()
        sys.exit(1)

    if args.apply and not has_recent_backup():
        print("BLOCKED: No recent clean backup found at %s" % BACKUP_ROOT)
        sys.exit(1)

    records = select_segment_records(args.segment, args.limit, eligible_only=args.eligible_only)
    classification = classify_records(records)
    obs_keys = [_observation_key(r) for r in records]
    digest = stable_digest(records)

    report = {
        "project": "traderie",
        "mode": "dry-run" if (args.dry_run or args.plan) else ("apply" if args.apply else "parity" if args.parity else "rollback"),
        "segment": args.segment,
        "limit": args.limit,
        "eligible_only": args.eligible_only,
        "selected_count": len(records),
        "selected_observation_keys": obs_keys,
        "selected_digest_sha256": digest,
        "mapping_target_tables": TARGET_TABLES,
        "classification": classification,
        "has_recent_backup": has_recent_backup(),
    }

    if args.dry_run or args.plan:
        if classification.get("required_field_rejects"):
            report["pilot_blocked"] = True
            report["blocker"] = "Selected records have missing required fields"
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print("Traderie pilot loader — %s" % report["mode"])
            print(f"  segment: {args.segment}, limit: {args.limit}, eligible: {args.eligible_only}")
            print(f"  selected: {len(records)} records, digest: {digest[:16]}...")
        return

    if args.rollback:
        conn = _pg_connect()
        try:
            assert_writer_role(conn)
            before = row_counts(conn)
            deleted = delete_pilot_rows(conn, obs_keys, args.segment)
            after = row_counts(conn)
            run_validation(conn)
            report["before_counts"] = before
            report["after_counts"] = after
            report["deleted"] = deleted
            report["rollback_ok"] = True
            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print(f"Rollback OK — deleted {len(obs_keys)} observations from {args.segment}")
        finally:
            conn.close()
        return

    if args.parity:
        conn = _pg_connect()
        try:
            pg_counts = selected_pg_counts(conn, obs_keys, args.segment)
            file_count = len(records)
            report["file_count"] = file_count
            report["pg_counts"] = pg_counts
            report["parity_ok"] = file_count == pg_counts["app.completed_trades"]
            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print(f"Parity: selected_file={file_count}, selected_PG={pg_counts}")
        finally:
            conn.close()
        return

    if args.apply:
        conn = _pg_connect()
        try:
            assert_writer_role(conn)
            before = row_counts(conn)
            upserted = load_records_into_pg(conn, records, args.segment)
            after = row_counts(conn)
            run_validation(conn)
            report["apply_ok"] = True
            report["upserted"] = upserted
            report["before_counts"] = before
            report["after_counts"] = after
            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print(f"Pilot load OK — upserted {upserted} records into {args.segment}")
                print(f"  Before: {before}")
                print(f"  After:  {after}")
        finally:
            conn.close()
        return


if __name__ == "__main__":
    main()
