#!/usr/bin/env python3
"""build_traderie_dataset_from_history.py — Build extracted trade CSVs from
retained Traderie history JSONL, enabling price generation from the
append-only history store instead of only from current raw files.

Usage:
  python scripts/build_traderie_dataset_from_history.py
  python scripts/build_traderie_dataset_from_history.py --segment pc_sc_nl
  python scripts/build_traderie_dataset_from_history.py --write-research
"""

import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
HISTORY_DIR = ROOT_DIR / "history" / "traderie"  # will resolve from ROOT
ITEMS_PATH = ROOT_DIR / "data" / "item_ids.json"
RESEARCH_DIR = ROOT_DIR / "data" / "research"
EXTRACTED_DIR = ROOT_DIR / "data" / "extracted"

SEGMENTS_ORDERED = ["pc_sc_l", "pc_sc_nl", "pc_hc_l", "pc_hc_nl"]

SEGMENT_META = {
    "pc_hc_l": {"platform": "pc", "ladder": True, "hardcore": True},
    "pc_hc_nl": {"platform": "pc", "ladder": False, "hardcore": True},
    "pc_sc_l": {"platform": "pc", "ladder": True, "hardcore": False},
    "pc_sc_nl": {"platform": "pc", "ladder": False, "hardcore": False},
}


def load_valid_runes() -> set:
    with open(ITEMS_PATH, "r") as f:
        item_data = json.load(f)
    return set(item_data["Runes"].keys())


def content_hash(obj) -> str:
    raw = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def observation_key(obs: dict) -> str:
    """Strongest dedupe: listing_id. Fallback: item + price + captured_at hash."""
    lid = obs.get("listing_id")
    if lid:
        return f"listing_id::{lid}"
    # Stable composite key
    parts = [
        str(obs.get("source_slug", "")),
        str(obs.get("item_name", "")),
        str(obs.get("price", obs.get("price_usd", ""))),
        str(obs.get("captured_at", obs.get("updated_at", ""))),
    ]
    return f"composite::{content_hash('::'.join(parts))}"


def read_history_jsonl(segment: str) -> tuple[list[dict], int, int]:
    """Read history JSONL, return (deduped_observations, raw_count, malformed_count)."""
    # Build path: data/history/traderie/{seg}/completed_trades_{seg}.jsonl
    path = ROOT_DIR / "data" / "history" / "traderie" / segment / f"completed_trades_{segment}.jsonl"
    if not path.exists():
        return [], 0, 0

    raw_rows = 0
    malformed = 0
    all_obs = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        raw_rows += 1
        try:
            obs = json.loads(line)
            all_obs.append(obs)
        except json.JSONDecodeError:
            malformed += 1

    # Dedupe by observation_key
    seen_keys = set()
    deduped = []
    dupe_count = 0
    for obs in all_obs:
        key = observation_key(obs)
        if key in seen_keys:
            dupe_count += 1
            continue
        seen_keys.add(key)
        # Remove internal metadata fields that extractor doesn't expect
        clean = {k: v for k, v in obs.items()
                 if not k.startswith("_") and k != "observation_key"}
        deduped.append(clean)

    return deduped, raw_rows, malformed, dupe_count


def extract_fields(obs: dict, segment: str, valid_runes: set) -> dict | None:
    """Convert a history observation to extractor-compatible fields.

    Returns dict with keys matching extract_rune_trades.py CSV schema,
    or None if the observation cannot be used (non-rune, invalid).
    """
    item_name = obs.get("item_name", "")
    if item_name not in valid_runes:
        return None

    quantity = obs.get("quantity", 1)
    if quantity <= 0:
        return None

    price = obs.get("price", [])
    if not price:
        return None

    # Check all price items are valid runes
    for p in price:
        pname = p.get("name", "") if isinstance(p, dict) else ""
        if pname not in valid_runes:
            return None

    # Build Offered and Requested strings
    offered_str = f"{item_name}:{quantity}"

    requested_counts = defaultdict(int)
    for p in price:
        pname = p.get("name", "") if isinstance(p, dict) else ""
        pqty = p.get("quantity", 1) if isinstance(p, dict) else 1
        requested_counts[pname] += pqty

    requested_str = ";".join(f"{r}:{q}" for r, q in requested_counts.items())

    updated_at = obs.get("updated_at", "")
    if not updated_at:
        import uuid
        updated_at = str(uuid.uuid4())

    trade_id = f"{item_name}_{updated_at}"

    meta = SEGMENT_META[segment]
    listing_id = obs.get("listing_id", "")
    seller_rating = obs.get("seller_rating")
    seller_reviews = obs.get("seller_reviews")
    has_and = obs.get("has_and_prices", False)
    group_count = obs.get("price_group_count", 0)
    entry_count = obs.get("price_entry_count", 1)

    return {
        "TradeID": trade_id,
        "Offered": offered_str,
        "Requested": requested_str,
        "listing_id": listing_id,
        "seller_rating": seller_rating,
        "seller_reviews": seller_reviews,
        "platform": meta["platform"],
        "ladder": str(meta["ladder"]).lower(),
        "hardcore": str(meta["hardcore"]).lower(),
        "segment_slug": segment,
        "has_and_prices": str(has_and).lower(),
        "price_group_count": group_count,
        "price_entry_count": entry_count,
    }


def get_earliest_latest(observations: list) -> tuple[str | None, str | None]:
    timestamps = []
    for obs in observations:
        t = obs.get("updated_at") or obs.get("captured_at") or obs.get("sold_at_relative")
        if t:
            timestamps.append(t)
    if not timestamps:
        return None, None
    return min(timestamps), max(timestamps)


def build_dataset(segment: str, valid_runes: set, write_research: bool) -> dict:
    hist_dir = ROOT_DIR / "data" / "history" / "traderie" / segment
    hist_path = hist_dir / f"completed_trades_{segment}.jsonl"

    obs_list, raw_count, malformed, dupe_count = read_history_jsonl(segment)
    extracted = []
    for obs in obs_list:
        row = extract_fields(obs, segment, valid_runes)
        if row:
            extracted.append(row)

    # Summary
    earliest, latest = get_earliest_latest(obs_list)
    extracted_single = sum(1 for r in extracted if ";" not in r["Requested"])
    extracted_and = sum(1 for r in extracted if ";" in r["Requested"])

    result = {
        "source": "traderie",
        "input": "retained_history_jsonl",
        "segment": segment,
        "history_file": str(hist_path.relative_to(ROOT_DIR)) if hist_path.exists() else None,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_window_label": "rolling_recent_trades_50_cap",
        "raw_rows": raw_count,
        "deduped_rows": len(obs_list),
        "malformed_rows": malformed,
        "duplicate_rows": dupe_count,
        "extracted_rows": len(extracted),
        "single_item_trades": extracted_single,
        "and_trades": extracted_and,
        "earliest_seen": earliest,
        "latest_seen": latest,
    }

    if write_research:
        RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

        # CSV output (matching extract_rune_trades.py format)
        # Uses the same filename pattern expected by calculate_rune_prices.py
        csv_path = RESEARCH_DIR / f"extracted_trades_{segment}.csv"
        fieldnames = [
            "TradeID", "Offered", "Requested",
            "listing_id", "seller_rating", "seller_reviews",
            "platform", "ladder", "hardcore", "segment_slug",
            "has_and_prices", "price_group_count", "price_entry_count",
        ]
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(extracted)
        result["csv_path"] = str(csv_path.relative_to(ROOT_DIR))

        # JSON dataset (full deduped observations with metadata)
        json_path = RESEARCH_DIR / f"traderie_history_dataset_{segment}.json"
        dataset = {
            "metadata": {k: v for k, v in result.items() if k != "csv_path"},
            "observations": obs_list,
        }
        with open(json_path, "w") as f:
            json.dump(dataset, f, indent=2)
        result["json_path"] = str(json_path.relative_to(ROOT_DIR))

        print(f"  Wrote CSV: {csv_path}")
        print(f"  Wrote JSON: {json_path}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Build Traderie extracted trade dataset from retained history JSONL")
    parser.add_argument("--segment", default=None,
                        help="Segment slug (e.g. pc_sc_nl) or all if omitted")
    parser.add_argument("--write-research", action="store_true",
                        help="Write CSV and JSON outputs to data/research/")
    parser.add_argument("--compare-current", action="store_true",
                        help="Compare history extraction against current canonical extraction (data/extracted/)")
    args = parser.parse_args()

    valid_runes = load_valid_runes()

    segments = [args.segment] if args.segment else SEGMENTS_ORDERED
    all_results = []

    print(f"{'='*60}")
    print(f"Traderie History Dataset Builder")
    print(f"Input: data/history/traderie/<seg>/completed_trades_<seg>.jsonl")
    print(f"{'='*60}")

    for seg in segments:
        print(f"\n--- {seg} ---")
        r = build_dataset(seg, valid_runes, args.write_research)
        all_results.append(r)
        print(f"  Raw rows: {r['raw_rows']}")
        print(f"  Deduped:  {r['deduped_rows']}")
        print(f"  Malformed: {r['malformed_rows']}")
        print(f"  Duplicates removed: {r['duplicate_rows']}")
        print(f"  Extracted trades: {r['extracted_rows']}")
        print(f"    Single-item: {r['single_item_trades']}")
        print(f"    AND trades:  {r['and_trades']}")
        print(f"  Window: {r['earliest_seen']} → {r['latest_seen']}")

    total_raw = sum(r["raw_rows"] for r in all_results)
    total_deduped = sum(r["deduped_rows"] for r in all_results)
    total_extracted = sum(r["extracted_rows"] for r in all_results)
    total_malformed = sum(r["malformed_rows"] for r in all_results)
    total_dupes = sum(r["duplicate_rows"] for r in all_results)

    print(f"\n{'='*60}")
    print(f"Summary ({len(all_results)} segments):")
    print(f"  Total raw history rows:  {total_raw}")
    print(f"  Total malformed:         {total_malformed}")
    print(f"  Total duplicates removed: {total_dupes}")
    print(f"  Total deduped:           {total_deduped}")
    print(f"  Total extracted trades:  {total_extracted}")
    if args.write_research:
        print(f"  Output: data/research/{{extracted_trades_{'{segment}'}.csv, traderie_history_dataset_{'{segment}'}.json}}")
    print(f"{'='*60}")

    if args.compare_current:
        print(f"\n{'='*60}")
        print(f"Comparison: History vs Canonical Extraction")
        print(f"{'='*60}")
        total_canonical = 0
        total_history = 0
        total_modeled = 0
        for seg in segments:
            # Canonical
            canonical_csv = EXTRACTED_DIR / f"extracted_trades_{seg}.csv"
            canonical_count = 0
            if canonical_csv.exists():
                with open(canonical_csv) as f:
                    canonical_count = sum(1 for _ in f) - 1  # header
                    if canonical_count < 0:
                        canonical_count = 0

            # History
            hist_csv = RESEARCH_DIR / f"extracted_trades_{seg}.csv"
            history_count = 0
            if hist_csv.exists():
                with open(hist_csv) as f:
                    history_count = sum(1 for _ in f) - 1
                    if history_count < 0:
                        history_count = 0

            # Modeled
            modeled_count = 0
            product_path = ROOT_DIR / "data" / "products" / "in_game_rune_values.json"
            if product_path.exists():
                prod = json.loads(product_path.read_text())
                seg_data = prod.get("segments", {}).get(seg)
                if seg_data:
                    modeled_count = sum(r["total_trades"] for r in seg_data.get("runes", {}).values())

            total_canonical += canonical_count
            total_history += history_count
            total_modeled += modeled_count

            pct = (history_count / canonical_count * 100) if canonical_count else 0
            print(f"\n  {seg}:")
            print(f"    Canonical extracted: {canonical_count:>8}")
            print(f"    History extracted:   {history_count:>8}  ({pct:.1f}%)")
            print(f"    Canonical modeled:   {modeled_count:>8}")

        total_pct = (total_history / total_canonical * 100) if total_canonical else 0
        model_pct = (total_modeled / total_canonical * 100) if total_canonical else 0
        print(f"\n  {'TOTAL':12}")
        print(f"    Canonical extracted: {total_canonical:>8}")
        print(f"    History extracted:   {total_history:>8}  ({total_pct:.1f}%)")
        print(f"    Canonical modeled:   {total_modeled:>8}  ({model_pct:.1f}% of canonical extracted)")
        print(f"    Delta (canonical - history): {total_canonical - total_history}")
        print(f"\n  Note: Canonical raw files accumulate ALL fetch runs without dedup.")
        print(f"  The history JSONL only started when snapshot_traderie.py was deployed.")
        print(f"  Much of the difference is data in raw files that was fetched before")
        print(f"  history collection began.")


if __name__ == "__main__":
    main()
