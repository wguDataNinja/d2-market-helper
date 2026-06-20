# filename: batch_compute_ist_prices.py

import csv
import numpy as np
import networkx as nx
import os
from collections import defaultdict

# Base path
BASE_DIR = "/scripts/old/extracted/"

# Input/output filenames (suffix only)
FILES = [
    "pc_sc_nl",
    "pc_sc_l",
    "pc_hc_nl",
    "pc_hc_l"
]

for dataset in FILES:
    INPUT_PATH = os.path.join(BASE_DIR, f"{dataset}_symmetric_pair_ratios.csv")
    OUTPUT_PATH = os.path.join(BASE_DIR, f"{dataset}_ist_normalized_prices.csv")

    G = nx.Graph()
    rune_trade_counts = defaultdict(int)

    with open(INPUT_PATH, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rune_a = row['Rune A']
            rune_b = row['Rune B']
            ratio = float(row['Estimated Ratio'])
            count = int(row['Trade Count'])

            weight = count
            G.add_edge(rune_a, rune_b, weight=weight, log_ratio=np.log(ratio))

            rune_trade_counts[rune_a] += count
            rune_trade_counts[rune_b] += count

    runes = list(G.nodes)
    runes.sort()
    rune_idx = {rune: i for i, rune in enumerate(runes)}
    n = len(runes)
    A = []
    b = []

    for u, v, data in G.edges(data=True):
        i = rune_idx[u]
        j = rune_idx[v]
        w = data['weight']
        log_r = data['log_ratio']

        row = np.zeros(n)
        row[i] = 1
        row[j] = -1

        for _ in range(w):
            A.append(row)
            b.append(log_r)

    A = np.vstack(A)
    b = np.array(b)

    anchor_idx = rune_idx.get("Ist Rune")
    anchor_row = np.zeros(n)
    anchor_row[anchor_idx] = 1
    A = np.vstack([A, anchor_row])
    b = np.append(b, 0.0)

    x, *_ = np.linalg.lstsq(A, b, rcond=None)
    prices = np.exp(x)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Rune', 'Ist Price', 'Trade Count'])
        for rune, price_val in sorted(zip(runes, prices)):
            trade_count = rune_trade_counts[rune]
            writer.writerow([rune, round(price_val, 6), trade_count])

    print(f"Processed: {dataset}")
    print(f"Output written to: {OUTPUT_PATH}")