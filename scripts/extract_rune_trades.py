# extract_rune_trades.py

import json
import csv
import uuid
from pathlib import Path
from collections import defaultdict

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

# Config
RAW_FILES = {
    "pc_hc_l": str(DATA_DIR / "raw" / "raw_trades_pc_hc_l.json"),
    "pc_hc_nl": str(DATA_DIR / "raw" / "raw_trades_pc_hc_nl.json"),
    "pc_sc_l": str(DATA_DIR / "raw" / "raw_trades_pc_sc_l.json"),
    "pc_sc_nl": str(DATA_DIR / "raw" / "raw_trades_pc_sc_nl.json")
}

ITEMS_PATH = DATA_DIR / "item_ids.json"
OUTPUT_DIR = DATA_DIR / "extracted"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load valid runes
with open(ITEMS_PATH, "r") as f:
    item_data = json.load(f)
valid_runes = set(item_data["Runes"].keys())

def extract_rune_trades(segment, raw_path):
    with open(raw_path, "r") as f:
        data = json.load(f)

    listings = data.get("Runes", {})
    total_raw = sum(len(listings[rune]) for rune in listings)

    extracted = []
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

            if len(requested) == 1 and offer_rune in requested:
                stats["self_trades"] += 1
                continue

            trade_id = f"{offer_rune}_{updated_at}"
            offered_str = f"{offer_rune}:{offer_qty}"
            requested_str = ";".join(f"{r}:{q}" for r, q in requested.items())

            extracted.append((trade_id, offered_str, requested_str))

            if len(requested) == 1:
                stats["single_item"] += 1
            else:
                stats["and_trades"] += 1

    output_path = OUTPUT_DIR / f"extracted_trades_{segment}.csv"
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["TradeID", "Offered", "Requested"])
        writer.writerows(extracted)

    print(f"\nSummary for {segment}:")
    print(f"  Total raw listings: {total_raw}")
    print(f"  Extracted rune-for-rune trades: {len(extracted)}")
    print(f"    Single-item trades: {stats['single_item']}")
    print(f"    AND trades: {stats['and_trades']}")
    print(f"  Skipped:")
    print(f"    Self-trades: {stats['self_trades']}")
    print(f"    Invalid: {stats['invalid']}")

def main():
    for segment, raw_file in RAW_FILES.items():
        extract_rune_trades(segment, raw_file)

if __name__ == "__main__":
    main()