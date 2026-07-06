#!/usr/bin/env python3
"""Dry-run readiness report for a bounded Traderie PostgreSQL pilot.

This script never writes to PostgreSQL or source files. It selects a small,
deterministic slice from the current file-backed history and reports the facts
needed to approve or block a later real-data pilot.
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.traderie_pg_adapter import PgTraderieAdapter
from scripts.traderie_storage_adapter import FileTraderieAdapter, _observation_key


DEFAULT_SEGMENT = "pc_sc_l"


def stable_digest(records):
    payload = json.dumps(records, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def select_records(segment, limit, eligible_only=False):
    adapter = FileTraderieAdapter()
    records = adapter.get_completed_trades(segment)
    records = sorted(
        records,
        key=lambda r: (
            r.get("captured_at") or "",
            str(r.get("listing_id") or ""),
            _observation_key(r),
        ),
    )
    if not eligible_only:
        return records[:limit]
    selected = []
    seen_keys = set()
    for record in records:
        classification = classify_records([record])
        key = _observation_key(record)
        if classification["required_field_rejects"]:
            continue
        if key in seen_keys:
            continue
        seen_keys.add(key)
        selected.append(record)
        if len(selected) >= limit:
            break
    return selected


def classify_records(records):
    required = {
        "segment_slug",
        "item_id",
        "item_name",
        "listing_id",
        "quantity",
        "captured_at",
        "price",
    }
    rejects = []
    keys = []
    listing_ids = []
    for record in records:
        missing = sorted(k for k in required if record.get(k) in (None, "", []))
        key = _observation_key(record)
        listing_id = record.get("listing_id")
        if key:
            keys.append(key)
        if listing_id is not None:
            listing_ids.append(str(listing_id))
        if not key:
            missing.append("observation_key")
        if missing:
            rejects.append({
                "observation_key": key,
                "listing_id": listing_id,
                "reason": "missing_required_fields",
                "fields": sorted(set(missing)),
            })
    duplicate_keys = sorted(k for k in set(keys) if keys.count(k) > 1)
    duplicate_listing_ids = sorted(k for k in set(listing_ids) if listing_ids.count(k) > 1)
    return {
        "required_field_rejects": rejects,
        "duplicate_observation_keys": duplicate_keys,
        "duplicate_listing_ids": duplicate_listing_ids,
    }


def main():
    parser = argparse.ArgumentParser(description="Traderie pilot readiness dry-run")
    parser.add_argument("--segment", default=DEFAULT_SEGMENT)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--eligible-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = select_records(args.segment, args.limit, eligible_only=args.eligible_only)
    classification = classify_records(records)
    pg_adapter = PgTraderieAdapter()
    gate_blockers = [
        "PostgreSQL adapter is an in-memory dry store, not a live database writer",
        "No approved real-data Gate packet for Traderie pilot execution in this session",
    ]
    if classification["required_field_rejects"]:
        gate_blockers.append("Selected subset has records missing required target fields")
    if classification["duplicate_observation_keys"]:
        gate_blockers.append("Selected subset has duplicate observation keys")

    report = {
        "project": "traderie",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dry_run_only": True,
        "segment": args.segment,
        "limit": args.limit,
        "eligible_only": args.eligible_only,
        "selected_count": len(records),
        "selected_observation_keys": [_observation_key(r) for r in records],
        "selected_digest_sha256": stable_digest(records),
        "mapping_target_tables": [
            "app.completed_trades",
            "app.price_entries",
            "app.snapshot_runs",
        ],
        "deduplication_keys": {
            "primary": "app.completed_trades.trade_observation_id",
            "business": "unique(segment_slug, observation_key)",
            "listing_reference": "segment_slug + listing_id index",
        },
        "rollback_model": "delete pilot rows by segment_slug and selected observation_key set, then rerun 999 validation",
        "delete_and_reimport_model": "same segment and sorted observation_key list must recreate the same digest",
        "pg_adapter_enabled": getattr(pg_adapter, "_enabled", False),
        "pg_adapter_mode": "dry_store_only",
        "classification": classification,
        "gate_status": "BLOCKED" if gate_blockers else "READY_FOR_OPERATOR_GATE",
        "gate_blockers": gate_blockers,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print("Traderie pilot readiness dry-run")
    print(f"segment: {report['segment']}")
    print(f"selected_count: {report['selected_count']}")
    print(f"digest: {report['selected_digest_sha256']}")
    print(f"gate_status: {report['gate_status']}")
    for blocker in gate_blockers:
        print(f"blocker: {blocker}")


if __name__ == "__main__":
    main()
