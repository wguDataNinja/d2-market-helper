# filename: extract_symmetric_rune_trades.py

import json
import csv
from pathlib import Path
from collections import defaultdict

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
OUTPUT_DIR = Path("/data/extracted_symmetric")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load item data and build Rune whitelist
with open(ITEMS_PATH, "r") as f:
    item_data = json.load(f)

valid_runes = set(item_data["Runes"].keys())

def process_file(raw_path, output_path):
    with open(raw_path, "r") as f:
        data = json.load(f)

    pair_counter = defaultdict(int)

    for offer_category, offer_items in data.items():
        if offer_category != "Runes":
            continue

        for offer_rune, listings in offer_items.items():
            if offer_rune not in valid_runes:
                continue

            for listing in listings:
                offer_qty = listing.get("quantity", 1)
                price = listing.get("price", [])
                if len(price) != 1:
                    continue  # skip multi-item trades

                ask_item = price[0]
                ask_rune = ask_item.get("name", "")
                ask_qty = ask_item.get("quantity", 1)

                if ask_rune not in valid_runes:
                    continue  # skip non-rune asks

                # Normalize to symmetric pair
                pair = tuple(sorted([offer_rune, ask_rune]))
                pair_counter[pair] += 1

    # Write CSV
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Rune A", "Rune B", "Trade Count"])
        for (rune_a, rune_b), count in sorted(pair_counter.items()):
            writer.writerow([rune_a, rune_b, count])


def main():
    for raw_file in RAW_FILES:
        filename = Path(raw_file).stem.replace("raw_trades_", "") + "_symmetric_rune_pairs.csv"
        output_path = OUTPUT_DIR / filename
        print(f"Processing {raw_file} -> {output_path}")
        process_file(raw_file, output_path)
    print("Symmetric extraction complete.")


if __name__ == "__main__":
    main()