#!/usr/bin/env python3
"""audit_traderie_game_version.py — Audit Game version / ruleset coverage across segments.

Reads local raw snapshots and history JSONL only. Does NOT call Traderie.

Reports:
  - Total listings by segment_slug + game_version + ruleset
  - Whether each segment's completed trades mix multiple game versions
  - Product-level impact assessment
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SNAPSHOTS_DIR = ROOT_DIR / "data" / "snapshots" / "raw" / "traderie"
HISTORY_DIR = ROOT_DIR / "data" / "history" / "traderie"
PRODUCT_PATH = ROOT_DIR / "data" / "products" / "in_game_rune_values.json"
ALL_SEGMENTS = ["pc_sc_l", "pc_sc_nl", "pc_hc_l", "pc_hc_nl"]

GV_MAP = {
    "classic": "classic",
    "lord of destruction": "lod",
    "reign of the warlock": "rotw",
}
GV_MAP_REVERSE = {v: k for k, v in GV_MAP.items()}


def ruleset_from_game_version(gv: str) -> str:
    raw = (gv or "").strip()
    if not raw:
        return "unknown"
    parts = [p.strip().lower() for p in raw.split(",")]
    resolved = set()
    for p in parts:
        if p == "classic":
            resolved.add("classic")
        elif p == "lord of destruction":
            resolved.add("lod")
        elif p == "reign of the warlock":
            resolved.add("rotw")
    if len(resolved) == 1:
        return resolved.pop()
    elif len(resolved) > 1:
        return "mixed"
    return "unknown"


def audit_from_raw_snapshots() -> dict:
    """Scan raw API response snapshots for Game version property."""
    counts = defaultdict(lambda: defaultdict(int))
    for seg in ALL_SEGMENTS:
        seg_dir = SNAPSHOTS_DIR / seg
        if not seg_dir.exists():
            continue
        run_dirs = sorted(seg_dir.iterdir())
        for run_dir in run_dirs:
            resp_path = run_dir / "response.json"
            if not resp_path.exists():
                continue
            try:
                raw = json.loads(resp_path.read_text(errors="replace"))
            except (json.JSONDecodeError, Exception):
                continue
            listings = raw.get("listings", [])
            for listing in listings:
                gv = "unknown"
                for prop in (listing.get("properties") or []):
                    if prop.get("property") == "Game version":
                        gv = prop.get("string") or "unknown"
                        break
                ruleset = ruleset_from_game_version(gv)
                counts[seg][(gv, ruleset)] += 1
    return counts


def audit_from_history_jsonl() -> dict:
    """Scan history JSONL for any game_version/ruleset fields (post-patch only)."""
    counts = defaultdict(lambda: defaultdict(int))
    for seg in ALL_SEGMENTS:
        hist_path = HISTORY_DIR / seg / f"completed_trades_{seg}.jsonl"
        if not hist_path.exists():
            continue
        for line in hist_path.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obs = json.loads(line)
            except json.JSONDecodeError:
                continue
            gv = obs.get("game_version", "unknown")
            rs = obs.get("ruleset", "unknown")
            counts[seg][(gv, rs)] += 1
    return counts


def print_audit(raw_counts: dict, hist_counts: dict):
    print("=" * 72)
    print("TRADERIE GAME VERSION / RULESET AUDIT")
    print("=" * 72)

    print("\n--- RAW SNAPSHOT ANALYSIS ---")
    print(f"{'Segment':<12} {'Game Version':<30} {'Ruleset':<10} {'Listings':>10}")
    print("-" * 64)
    total_all = 0
    seg_mixes = {}
    for seg in ALL_SEGMENTS:
        seg_counts = raw_counts.get(seg, {})
        seg_total = sum(seg_counts.values())
        total_all += seg_total
        distinct = set()
        for (gv, rs), cnt in sorted(seg_counts.items()):
            print(f"{seg:<12} {str(gv):<30} {rs:<10} {cnt:>10}")
            distinct.add(rs)
        has_mix = len(distinct) > 1
        if seg_total > 0:
            print(f"{'':12} {'':30} {'':10} {'─' * 10}")
            print(f"{'':12} {'TOTAL':<30} {'':10} {seg_total:>10}")
            if has_mix:
                print(f"{'':12} {'⚠ MIXED: ' + ', '.join(sorted(distinct)):<40}")
        seg_mixes[seg] = {
            "total_listings": seg_total,
            "distinct_rulesets": sorted(distinct),
            "mixes_rulesets": has_mix,
        }
        print()

    print(f"\n{'TOTAL ALL SEGMENTS':<42} {total_all:>10}")

    print("\n--- HISTORY JSONL GAME VERSION COVERAGE (post-patch rows) ---")
    hist_entries_with_gv = sum(
        cnt for seg in hist_counts.values() for (gv, rs), cnt in seg.items()
    )
    if hist_entries_with_gv:
        print(f"  History rows with game_version/ruleset: {hist_entries_with_gv}")
        for seg in ALL_SEGMENTS:
            seg_counts = hist_counts.get(seg, {})
            if seg_counts:
                for (gv, rs), cnt in sorted(seg_counts.items()):
                    print(f"    {seg:<12} {str(gv):<30} {rs:<10} {cnt:>10}")
    else:
        print("  No history rows have game_version/ruleset yet (pre-patch data).")

    print("\n--- PRODUCT MIX ANALYSIS ---")
    if PRODUCT_PATH.exists():
        prod = json.loads(PRODUCT_PATH.read_text())
        for seg in ALL_SEGMENTS:
            seg_data = prod.get("segments", {}).get(seg, {})
            trade_count = seg_data.get("total_modeled_trades", 0)
            sm = seg_mixes.get(seg, {})
            if sm.get("mixes_rulesets"):
                print(f"  ⚠ {seg:<12} MIXES {sm['distinct_rulesets']} — "
                      f"{trade_count} modeled trades aggregated across rulesets")
            else:
                rs_list = sm.get("distinct_rulesets", [])
                rs_str = rs_list[0] if rs_list else "no data"
                print(f"  ✓ {seg:<12} single ruleset ({rs_str}) — "
                      f"{trade_count} modeled trades")
    else:
        print("  Product file not found at", PRODUCT_PATH)

    print("\n--- KEY FINDINGS ---")
    mixing_segs = [s for s, m in seg_mixes.items() if m.get("mixes_rulesets")]
    if mixing_segs:
        print(f"  ⚠ Segments mixing multiple rulesets: {mixing_segs}")
        print(f"  → Current pricing model aggregates these together.")
        print(f"  → To split: add ruleset dimension to product schema and")
        print(f"    run separate VWAP calculations per segment+ruleset.")
    else:
        print(f"  ✓ No segment currently mixes multiple rulesets.")
    print(f"  → Region data is NOT available in completed-trades API responses.")
    print(f"  → Region appears only in the Traderie web UI (active listings).")

    return seg_mixes


def main():
    raw_counts = audit_from_raw_snapshots()
    hist_counts = audit_from_history_jsonl()

    if not any(raw_counts.values()):
        print("No raw snapshots found. Checking history only...")
        # Fallback: check raw snapshot dirs exist
        if not SNAPSHOTS_DIR.exists():
            print(f"Raw snapshot directory not found: {SNAPSHOTS_DIR}")
            print("Run snapshot_traderie.py first to collect data.")
            return 1

    seg_mixes = print_audit(raw_counts, hist_counts)

    summary_path = ROOT_DIR / "data" / "research" / "game_version_audit_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "audit_type": "game_version_ruleset_coverage",
        "generated_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "local_raw_snapshots_only",
        "segments": {s: v for s, v in seg_mixes.items()},
        "key_findings": {
            "mixing_segments": [
                s for s, v in seg_mixes.items() if v.get("mixes_rulesets")
            ],
            "region_available_in_api": False,
            "region_available_in_ui": True,
            "note": (
                "Region exists in Traderie web UI but is absent from the "
                "completed-trades API. Game version / ruleset is available "
                "in API listing properties but was dropped until this patch."
            ),
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"\n  Summary written to {summary_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
