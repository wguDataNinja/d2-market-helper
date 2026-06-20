# /Users/buddy/Desktop/traderie/scripts/normalize_raw_trades.py

import json
import csv
import uuid
from pathlib import Path
from collections import defaultdict

# Config
RAW_FILES = {
    "pc_hc_l": "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_hc_l.json",
    "pc_hc_nl": "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_hc_nl.json",
    "pc_sc_l": "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_sc_l.json",
    "pc_sc_nl": "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_sc_nl.json"
}

ITEMS_PATH = Path("/data/item_data.json")
OUTPUT_DIR = Path("/data/normalized")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load valid runes
with open(ITEMS_PATH, "r") as f:
    item_data = json.load(f)
valid_runes = set(item_data["Runes"].keys())


def normalize_file(segment, raw_path):
    with open(raw_path, "r") as f:
        data = json.load(f)

    listings = data.get("Runes", {})
    total_raw = sum(len(listings[rune]) for rune in listings)

    normalized = []
    stats = defaultdict(int)

    for offer_rune, offer_listings in listings.items():
        if offer_rune not in valid_runes:
            continue

        for listing in offer_listings:
            offer_qty = listing.get("quantity", 1)
            updated_at = listing.get("updated_at", str(uuid.uuid4()))
            price = listing.get("price", [])

            if not price or offer_qty <= 0:
                stats["invalid"] += 1
                continue

            # Build requested dict
            requested = defaultdict(int)
            skip_non_rune = False

            for item in price:
                item_name = item.get("name", "")
                item_qty = item.get("quantity", 1)
                if item_name not in valid_runes or item_qty <= 0:
                    skip_non_rune = True
                    break
                requested[item_name] += item_qty

            if skip_non_rune:
                stats["invalid"] += 1
                continue

            # Skip self-trades
            if len(requested) == 1 and offer_rune in requested:
                stats["self_trades"] += 1
                continue

            trade_id = f"{offer_rune}_{updated_at}"
            offered_str = f"{offer_rune}:{offer_qty}"
            requested_str = ";".join(f"{r}:{q}" for r, q in requested.items())

            normalized.append((trade_id, offered_str, requested_str))

            if len(requested) == 1:
                stats["single_item"] += 1
            else:
                stats["and_trades"] += 1

    output_path = OUTPUT_DIR / f"normalized_trades_{segment}.csv"
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["TradeID", "Offered", "Requested"])
        writer.writerows(normalized)

    # Print summary
    print(f"\nSummary for {segment}:")
    print(f"  Total raw listings: {total_raw}")
    print(f"  Normalized trades extracted: {len(normalized)}")
    print(f"    Single-item trades: {stats['single_item']}")
    print(f"    AND trades: {stats['and_trades']}")
    print(f"  Skipped:")
    print(f"    Self-trades: {stats['self_trades']}")
    print(f"    Invalid: {stats['invalid']}")


def main():
    for segment, raw_file in RAW_FILES.items():
        normalize_file(segment, raw_file)


if __name__ == "__main__":
    main()