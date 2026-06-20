# filename: inspect_anomalies_full.py

import json
from pathlib import Path
from collections import defaultdict

# Input files (raw trade data files)
RAW_FILES = [
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_hc_l.json",
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_hc_nl.json",
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_sc_l.json",
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_sc_nl.json"
]

# Item catalog
ITEMS_PATH = Path("/data/item_data.json")

# Load item data and build Rune whitelist
with open(ITEMS_PATH, "r") as f:
    item_data = json.load(f)

valid_runes = set(item_data["Runes"].keys())

def inspect_file(raw_path):
    with open(raw_path, "r") as f:
        data = json.load(f)

    total_trades = 0
    multi_item_trades = []
    zero_quantity_trades = []
    self_trades = defaultdict(list)

    for offer_category, offer_items in data.items():
        if offer_category != "Runes":
            continue

        for offer_rune, listings in offer_items.items():
            if offer_rune not in valid_runes:
                continue

            for listing in listings:
                total_trades += 1

                offer_qty = listing.get("quantity", 1)
                price = listing.get("price", [])

                if len(price) != 1:
                    multi_item_trades.append(listing)
                    continue

                ask_item = price[0]
                ask_rune = ask_item.get("name", "")
                ask_qty = ask_item.get("quantity", 1)

                if offer_qty == 0 or ask_qty == 0:
                    zero_quantity_trades.append(listing)

                if offer_rune == ask_rune:
                    self_trades[offer_rune].append(listing)

    print(f"\n=== File: {raw_path} ===")
    print(f"Total rune trades: {total_trades}")
    print(f"Multi-item trades: {len(multi_item_trades)}")
    print(f"Zero-quantity trades: {len(zero_quantity_trades)}")
    print(f"Self-trades:")

    for rune, trades in sorted(self_trades.items()):
        print(f"  {rune}: {len(trades)}")
        for trade in trades:
            print(json.dumps(trade, indent=2))

    if multi_item_trades:
        print("\n--- Multi-item trades sample ---")
        for trade in multi_item_trades[:5]:  # limit output
            print(json.dumps(trade, indent=2))

    if zero_quantity_trades:
        print("\n--- Zero-quantity trades ---")
        for trade in zero_quantity_trades:
            print(json.dumps(trade, indent=2))

def main():
    for raw_file in RAW_FILES:
        inspect_file(raw_file)

if __name__ == "__main__":
    main()