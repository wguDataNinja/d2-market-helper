# /Users/buddy/Desktop/traderie/scripts/inspect_empty_prices_sample.py

import json
from pathlib import Path

# Config
RAW_FILES = {
    "pc_hc_l": "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_hc_l.json",
    "pc_hc_nl": "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_hc_nl.json",
    "pc_sc_l": "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_sc_l.json",
    "pc_sc_nl": "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_sc_nl.json"
}

SAMPLE_LIMIT = 5  # number of examples to show per segment

def inspect_file(segment, raw_path):
    print(f"\nSegment: {segment}\n" + "-" * 40)
    with open(raw_path, "r") as f:
        data = json.load(f)

    listings = data.get("Runes", {})
    total_checked = 0
    missing_price = 0
    empty_price = 0

    samples_shown = 0

    for offer_rune, offer_listings in listings.items():
        for listing in offer_listings:
            total_checked += 1

            if "price" not in listing:
                missing_price += 1
                if samples_shown < SAMPLE_LIMIT:
                    print(f"\nMISSING price | Offered: {offer_rune}")
                    print(json.dumps(listing, indent=2))
                    samples_shown += 1
                continue

            if listing["price"] == []:
                empty_price += 1
                if samples_shown < SAMPLE_LIMIT:
                    print(f"\nEMPTY price | Offered: {offer_rune}")
                    print(json.dumps(listing, indent=2))
                    samples_shown += 1

    print(f"\nChecked {total_checked} listings")
    print(f"  Missing price: {missing_price}")
    print(f"  Empty price: {empty_price}")
    if samples_shown >= SAMPLE_LIMIT:
        print(f"\nStopped after {SAMPLE_LIMIT} samples to avoid overload.")

def main():
    for segment, raw_file in RAW_FILES.items():
        inspect_file(segment, raw_file)

if __name__ == "__main__":
    main()