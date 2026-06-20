# filename: batch_symmetric_pair_ratios.py

import csv
import os
from collections import defaultdict
import numpy as np

# Input/Output directory (adjust if needed)
BASE_DIR = "/scripts/old/extracted/"

# List of input files
FILES = [
    "pc_hc_l_rune_trades.csv",
    "pc_hc_nl_rune_trades.csv",
    "pc_sc_l_rune_trades.csv",
    "pc_sc_nl_rune_trades.csv"
]

for filename in FILES:
    input_path = os.path.join(BASE_DIR, filename)
    output_path = os.path.join(BASE_DIR, filename.replace("_rune_trades.csv", "_symmetric_pair_ratios.csv"))

    pair_ratios = defaultdict(list)

    with open(input_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            offer_rune = row['Offer Rune']
            offer_qty = float(row['Offer Qty'])
            ask_rune = row['Ask Rune']
            ask_qty = float(row['Ask Qty'])

            if offer_qty == 0 or ask_qty == 0:
                continue

            # Normalize pair (unordered)
            rune_a, rune_b = sorted([offer_rune, ask_rune])

            if (offer_rune, ask_rune) == (rune_a, rune_b):
                ratio = offer_qty / ask_qty
            else:
                ratio = ask_qty / offer_qty

            pair_ratios[(rune_a, rune_b)].append(ratio)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Rune A', 'Rune B', 'Estimated Ratio', 'Trade Count'])
        for (rune_a, rune_b), ratios in sorted(pair_ratios.items()):
            median_ratio = np.median(ratios)
            writer.writerow([rune_a, rune_b, round(median_ratio, 4), len(ratios)])

    print(f"Processed: {filename} → {output_path}")