# filename: extract_rune_trades.py

import json
import csv
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

# Output folder
OUTPUT_DIR = Path("/scripts/old/extracted")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load item data and build Rune whitelist
with open(ITEMS_PATH, "r") as f:
    item_data = json.load(f)

valid_runes = set(item_data["Runes"].keys())

def process_file(raw_path, output_path):
    with open(raw_path, "r") as f:
        data = json.load(f)

    rows = []

    for offer_category, offer_items in data.items():
        if offer_category != "Runes":
            continue

        for offer_rune, listings in offer_items.items():
            if offer_rune not in valid_runes:
                continue

            for listing in listings:
                offer_qty = listing.get("quantity", 1)
                updated_at = listing.get("updated_at", "")

                price = listing.get("price", [])
                if len(price) != 1:
                    continue  # skip multi-item trades

                ask_item = price[0]
                ask_rune = ask_item.get("name", "")
                ask_qty = ask_item.get("quantity", 1)

                if ask_rune not in valid_runes:
                    continue  # skip non-rune asks

                rows.append([offer_rune, offer_qty, ask_rune, ask_qty, updated_at])

    # Write CSV
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Offer Rune", "Offer Qty", "Ask Rune", "Ask Qty", "updated_at"])
        writer.writerows(rows)


def main():
    for raw_file in RAW_FILES:
        filename = Path(raw_file).stem.replace("raw_trades_", "") + "_rune_trades.csv"
        output_path = OUTPUT_DIR / filename
        print(f"Processing {raw_file} -> {output_path}")
        process_file(raw_file, output_path)
    print("Extraction complete.")


if __name__ == "__main__":
    main()