# /scripts/aggregate_ist_prices.py

import csv
import json
from pathlib import Path
from collections import defaultdict

# Segments to process
SEGMENTS = ["pc_hc_l", "pc_hc_nl", "pc_sc_l", "pc_sc_nl"]

# Base path
BASE_DIR = Path("/data/extracted")

for segment in SEGMENTS:
    input_file = BASE_DIR / f"{segment}_ist_normalized_prices.csv"
    output_file = BASE_DIR / f"{segment}_ist_avg_prices.json"

    price_data = defaultdict(list)

    with open(input_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rune = row["Rune"]
            price = float(row["Ist Price"])
            count = int(row["Trade Count"])

            if count == 0:
                continue  # skip zero count

            price_data[rune].extend([price] * count)

    final_prices = {}
    for rune, prices in price_data.items():
        avg_price = round(sum(prices) / len(prices), 4)
        final_prices[rune] = avg_price

    final_prices["Ist Rune"] = 1.0

    with open(output_file, "w") as f:
        json.dump(final_prices, f, indent=2)

    print(f"{segment} aggregated -> {output_file}")