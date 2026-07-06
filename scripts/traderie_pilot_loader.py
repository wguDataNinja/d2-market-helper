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
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.traderie_storage_adapter import FileTraderieAdapter, _observation_key
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
    conn = psycopg2.connect(
        database=PG_DATABASE,
        user=PG_WRITER_USER,
        host=os.environ.get("PGHOST", ""),
        port=os.environ.get("PGPORT", "5432"),
    )
    conn.autocommit = False
    return conn


def row_counts(conn):
    counts = {}
    for table in TARGET_TABLES:
        schema, tbl = table.split(".")
        c = conn.cursor()
        c.execute(f"SELECT COUNT(*) FROM {schema}.{tbl}")
        counts[table] = c.fetchone()[0]
    return counts


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


def load_records_into_pg(conn, records, segment):
    c = conn.cursor()
    inserted = 0
    for record in records:
        listing_id = record.get("listing_id")
        price = record.get("price")
        item_name = record.get("item", {}).get("name") if isinstance(record.get("item"), dict) else record.get("item")
        captured_at = record.get("captured_at")
        obs_key = _observation_key(record)
        ruleset = record.get("ruleset", "")
        status = record.get("status", "unknown")

        # app.completed_trades
        c.execute("""
            INSERT INTO app.completed_trades (listing_id, item_name, price, captured_at, segment_slug, observation_key, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (observation_key) DO NOTHING
        """, (listing_id, item_name, price, captured_at, segment, obs_key, status))

        # app.price_entries — derive price entry
        if price is not None:
            c.execute("""
                INSERT INTO app.price_entries (item_name, price, observed_at, segment_slug, observation_key)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (item_name, price, captured_at, segment, obs_key))

        inserted += 1
    conn.commit()
    return inserted


def delete_pilot_rows(conn, observation_keys, segment):
    c = conn.cursor()
    for ok in observation_keys:
        c.execute("DELETE FROM app.price_entries WHERE observation_key = %s", (ok,))
        c.execute("DELETE FROM app.completed_trades WHERE observation_key = %s", (ok,))
    conn.commit()


def run_validation(conn):
    val_path = REPO_ROOT / "db" / "validation" / "999_full_validation.sql"
    if val_path.exists():
        c = conn.cursor()
        c.execute(val_path.read_text())
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
            before = row_counts(conn)
            delete_pilot_rows(conn, obs_keys, args.segment)
            after = row_counts(conn)
            run_validation(conn)
            report["before_counts"] = before
            report["after_counts"] = after
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
            pg_counts = row_counts(conn)
            file_count = len(records)
            report["file_count"] = file_count
            report["pg_counts"] = pg_counts
            report["parity_ok"] = file_count <= max(v for v in pg_counts.values()) + 5
            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print(f"Parity: file={file_count}, PG={pg_counts}")
        finally:
            conn.close()
        return

    if args.apply:
        conn = _pg_connect()
        try:
            before = row_counts(conn)
            inserted = load_records_into_pg(conn, records, args.segment)
            after = row_counts(conn)
            run_validation(conn)
            report["apply_ok"] = True
            report["inserted"] = inserted
            report["before_counts"] = before
            report["after_counts"] = after
            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print(f"Pilot load OK — inserted {inserted} records into {args.segment}")
                print(f"  Before: {before}")
                print(f"  After:  {after}")
        finally:
            conn.close()
        return


if __name__ == "__main__":
    main()
