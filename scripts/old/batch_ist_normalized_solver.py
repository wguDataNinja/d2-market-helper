# filename: batch_ist_normalized_solver.py

import csv
import os
import numpy as np

# Base directory
BASE_DIR = "/scripts/old/extracted/"

# Dataset files
DATASETS = [
    "pc_hc_l",
    "pc_hc_nl",
    "pc_sc_l",
    "pc_sc_nl"
]

for dataset in DATASETS:
    input_file = os.path.join(BASE_DIR, f"{dataset}_symmetric_pair_ratios.csv")
    output_file = os.path.join(BASE_DIR, f"{dataset}_ist_normalized_prices.csv")

    # Build data
    pairs = []
    runes = set()

    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rune_a = row['Rune A']
            rune_b = row['Rune B']
            ratio = float(row['Estimated Ratio'])
            count = int(row['Trade Count'])
            pairs.append((rune_a, rune_b, ratio, count))
            runes.add(rune_a)
            runes.add(rune_b)

    runes = sorted(runes)
    rune_idx = {rune: i for i, rune in enumerate(runes)}

    n = len(runes)
    rows = []
    b_vals = []
    weights = []

    for rune_a, rune_b, ratio, count in pairs:
        i = rune_idx[rune_a]
        j = rune_idx[rune_b]
        row = np.zeros(n)
        row[i] = 1
        row[j] = -1
        rows.append(row)
        b_vals.append(np.log(ratio))
        weights.append(count)

        # Also add reverse direction for symmetry
        rows.append(-row)
        b_vals.append(-np.log(ratio))
        weights.append(count)

    A = np.vstack(rows)
    b = np.array(b_vals)
    W = np.diag(weights)

    # Add hard constraint: log(P_Ist) = 0
    ist_row = np.zeros(n)
    ist_row[rune_idx['Ist Rune']] = 1
    A = np.vstack([A, ist_row])
    b = np.append(b, 0)
    W = np.pad(W, ((0,1),(0,1)), 'constant')
    W[-1, -1] = 1e6  # very strong weight for hard constraint

    # Solve weighted least squares
    AtW = A.T @ W
    x = np.linalg.lstsq(AtW @ A, AtW @ b, rcond=None)[0]

    # Write output
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Rune', 'Ist Price'])
        for rune, log_price in zip(runes, x):
            price = np.exp(log_price)
            writer.writerow([rune, round(price, 6)])

    print(f"Processed: {dataset} → {output_file}")