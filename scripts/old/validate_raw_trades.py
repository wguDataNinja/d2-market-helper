# filename: validate_raw_trades.py

import json
from pathlib import Path

# Input files (raw trade data files)
RAW_FILES = [
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_hc_l.json",
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_hc_nl.json",
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_sc_l.json",
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_sc_nl.json"
]

# Item catalog (contains full item list)
ITEMS_PATH = Path("/data/item_data.json")

# Load valid rune whitelist
with open(ITEMS_PATH, "r") as f:
    item_data = json.load(f)

valid_runes = set(item_data["Runes"].keys())

def validate_file(raw_path):
    with open(raw_path, "r") as f:
        data = json.load(f)

    errors = []
    total = 0
    valid = 0

    for offer_category, offer_items in data.items():
        for offer_rune, listings in offer_items.items():
            for listing in listings:
                total += 1

                offer_qty = listing.get("quantity", 1)
                price = listing.get("price", [])

                # Check for multi-item trades
                if len(price) != 1:
                    errors.append((listing, "Multi-item trade"))
                    continue

                ask_item = price[0]
                ask_rune = ask_item.get("name", "")
                ask_qty = ask_item.get("quantity", 1)

                # Check for non-rune items
                if offer_rune not in valid_runes or ask_rune not in valid_runes:
                    errors.append((listing, "Non-rune trade"))
                    continue

                # Check for zero or negative quantities
                if offer_qty <= 0 or ask_qty <= 0:
                    errors.append((listing, "Invalid quantity"))
                    continue

                # Check for self-trades (rune traded for itself)
                if offer_rune == ask_rune:
                    errors.append((listing, "Self-trade detected"))
                    continue

                valid += 1

    print(f"Validation complete: {raw_path}")
    print(f"  Total trades: {total}")
    print(f"  Valid trades: {valid}")
    print(f"  Invalid trades: {len(errors)}")

    for listing, reason in errors:
        print(f"    {reason}: {listing}")

def main():
    for raw_file in RAW_FILES:
        validate_file(raw_file)

if __name__ == "__main__":
    main()