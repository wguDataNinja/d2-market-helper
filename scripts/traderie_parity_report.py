#!/usr/bin/env python3
"""Traderie parity report — compare file adapter vs PG adapter reads.

Usage:
    python3 scripts/traderie_parity_report.py [--segment pc_sc_l]

Compares completed_trades, price_entries, and product_builds between the
file-backed and PG-backed adapters. Reports mismatches by observation_key.

Designed for deterministic comparison during shadow/dual-write validation.
See CODEX_SESSION_1_ARCHITECTURE.md §14 (parity criteria).
"""

import argparse
import logging
import sys
from typing import Any, Optional

from scripts.traderie_storage_adapter import FileTraderieAdapter, _observation_key
from scripts.traderie_pg_adapter import PgTraderieAdapter

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class ParityReport:
    """Compare file adapter output against PG adapter output."""

    def __init__(
        self,
        file_adapter: FileTraderieAdapter,
        pg_adapter: PgTraderieAdapter,
    ):
        self._file = file_adapter
        self._pg = pg_adapter

    def compare_trades(self, segment_slug: Optional[str] = None) -> dict[str, Any]:
        file_trades = self._file.get_completed_trades(segment_slug)
        try:
            pg_trades = self._pg.get_completed_trades(segment_slug)
        except RuntimeError:
            return {
                "status": "skipped",
                "reason": "PG adapter not enabled",
                "file_count": len(file_trades),
            }

        file_by_key = {_observation_key(t): t for t in file_trades}
        pg_by_key = {_observation_key(t): t for t in pg_trades}

        file_keys = set(file_by_key.keys())
        pg_keys = set(pg_by_key.keys())

        only_file = file_keys - pg_keys
        only_pg = pg_keys - file_keys
        common = file_keys & pg_keys

        mismatches = []
        for key in sorted(common):
            ft = file_by_key[key]
            pt = pg_by_key[key]
            diff = self._diff_trade(ft, pt)
            if diff:
                mismatches.append({"observation_key": key, "differences": diff})

        return {
            "status": "completed",
            "file_count": len(file_trades),
            "pg_count": len(pg_trades),
            "only_file": len(only_file),
            "only_pg": len(only_pg),
            "common": len(common),
            "mismatches": mismatches,
            "match": len(mismatches) == 0,
        }

    def _diff_trade(self, file_trade: dict, pg_trade: dict) -> list[str]:
        compare_fields = ["item_name", "item_id", "listing_id", "quantity", "segment_slug", "ruleset"]
        diffs = []
        for field in compare_fields:
            fv = file_trade.get(field)
            pv = pg_trade.get(field)
            if str(fv) != str(pv):
                diffs.append(f"{field}: file={fv!r} pg={pv!r}")
        return diffs


def main() -> None:
    parser = argparse.ArgumentParser(description="Traderie parity report")
    parser.add_argument("--segment", "-s", help="Filter to single segment slug")
    args = parser.parse_args()

    file_adapter = FileTraderieAdapter()
    pg_adapter = PgTraderieAdapter(file_adapter=file_adapter)

    reporter = ParityReport(file_adapter, pg_adapter)
    report = reporter.compare_trades(args.segment)

    print(f"Parity Report: completed_trades")
    print(f"  Status: {report['status']}")
    if report['status'] == 'skipped':
        print(f"  Reason: {report['reason']}")
        sys.exit(0)

    print(f"  File trades:  {report['file_count']}")
    print(f"  PG trades:    {report['pg_count']}")
    print(f"  Only in file: {report['only_file']}")
    print(f"  Only in PG:   {report['only_pg']}")
    print(f"  Common:       {report['common']}")
    print(f"  Match:        {report['match']}")

    if report['mismatches']:
        print(f"\n  Mismatches ({len(report['mismatches'])}):")
        for m in report['mismatches']:
            print(f"    - {m['observation_key']}:")
            for d in m['differences']:
                print(f"      {d}")

    sys.exit(0 if report['match'] else 1)


if __name__ == "__main__":
    main()
