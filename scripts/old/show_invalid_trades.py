# /Users/buddy/Desktop/traderie/scripts/show_invalid_trades.py

import json
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

# Load valid runes
with open(ITEMS_PATH, "r") as f:
    item_data = json.load(f)
valid_runes = set(item_data["Runes"].keys())

def show_invalids(segment, raw_path):
    print(f"\nSegment: {segment}\n" + "-" * 40)
    with open(raw_path, "r") as f:
        data = json.load(f)

    listings = data.get("Runes", {})

    for offer_rune, offer_listings in listings.items():
        if offer_rune not in valid_runes:
            continue

        for listing in offer_listings:
            offer_qty = listing.get("quantity", 1)
            price = listing.get("price", [])

            # Handle empty price
            if not price:
                reason = "empty_price"
                print_invalid(reason, offer_rune, offer_qty, [])
                continue

            # Handle zero offer qty
            if offer_qty <= 0:
                reason = "zero_offer_qty"
                requested_flat = flatten_price(price)
                print_invalid(reason, offer_rune, offer_qty, requested_flat)
                continue

            # Handle invalid price items
            skip = False
            requested_flat = []
            for item in price:
                item_name = item.get("name", "")
                item_qty = item.get("quantity", 1)

                if item_qty <= 0:
                    reason = "zero_price_qty"
                    skip = True
                    break

                if item_name not in valid_runes:
                    reason = f"non_rune_price ({item_name})"
                    skip = True
                    break

                requested_flat.append(f"{item_name} x {item_qty}")

            if skip:
                print_invalid(reason, offer_rune, offer_qty, requested_flat)
                continue

            # Handle self trades
            if len(price) == 1 and price[0]["name"] == offer_rune:
                reason = "self_trade"
                print_invalid(reason, offer_rune, offer_qty, requested_flat)
                continue

def flatten_price(price):
    result = []
    for item in price:
        name = item.get("name", "")
        qty = item.get("quantity", 1)
        result.append(f"{name} x {qty}")
    return result

def print_invalid(reason, offer_rune, offer_qty, requested_flat):
    requested_str = ", ".join(requested_flat) if requested_flat else "(empty)"
    print(f"INVALID: {reason} | Offered: {offer_rune} x {offer_qty} | Requested: {requested_str}")

def main():
    for segment, raw_file in RAW_FILES.items():
        show_invalids(segment, raw_file)

if __name__ == "__main__":
    main()