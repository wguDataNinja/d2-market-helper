# /scripts/analyze_trade_consistency.py

import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

# Config paths
BASE_DIR = Path("/data")
RAW_DIR = BASE_DIR / "raw"
EXTRACTED_DIR = BASE_DIR / "extracted"
CONSISTENCY_DIR = BASE_DIR / "consistency"

# Segments to process
SEGMENTS = ["pc_hc_l", "pc_hc_nl", "pc_sc_l", "pc_sc_nl"]

for segment in SEGMENTS:
    # Load Ist prices for segment
    with open(EXTRACTED_DIR / f"{segment}_ist_avg_prices.json") as f:
        ist_prices = json.load(f)

    # Load raw trade data
    with open(RAW_DIR / f"raw_trades_{segment}.json") as f:
        trades = json.load(f)

    # Outputs for this segment
    segment_out_dir = CONSISTENCY_DIR / segment
    segment_out_dir.mkdir(parents=True, exist_ok=True)

    trade_residuals = []
    pairwise_records = defaultdict(list)

    def compute_ist_value(items):
        return sum(ist_prices.get(rune, 0) * qty for rune, qty in items.items())

    def is_pairwise_rune_trade(offered, requested):
        runes = set(offered.keys()) | set(requested.keys())
        return len(runes) == 2 and all(r in ist_prices for r in runes)

    for trade in trades:
        trade_id = trade['TradeID']
        offered = trade['Offered']
        requested = trade['Requested']

        offered_ist = compute_ist_value(offered)
        requested_ist = compute_ist_value(requested)
        if requested_ist == 0:
            continue

        residual = offered_ist / requested_ist
        trade_residuals.append({
            'TradeID': trade_id,
            'Offered Ist': offered_ist,
            'Requested Ist': requested_ist,
            'Residual': residual
        })

        if is_pairwise_rune_trade(offered, requested):
            runes = list((set(offered.keys()) | set(requested.keys())))
            rune_a, rune_b = runes[0], runes[1]
            qty_a = offered.get(rune_a, 0) - requested.get(rune_a, 0)
            qty_b = offered.get(rune_b, 0) - requested.get(rune_b, 0)

            if qty_a * qty_b < 0:
                qty_a = abs(qty_a)
                qty_b = abs(qty_b)
            elif qty_a < 0 and qty_b < 0:
                qty_a = abs(qty_a)
                qty_b = abs(qty_b)
            elif qty_a == 0 or qty_b == 0:
                continue

            observed_ratio = qty_a / qty_b
            expected_ratio = ist_prices[rune_a] / ist_prices[rune_b]
            error = (observed_ratio / expected_ratio) - 1

            key = tuple(sorted([rune_a, rune_b]))
            pairwise_records[key].append(error)

    # Export Trade Residuals
    df_residuals = pd.DataFrame(trade_residuals)
    df_residuals.to_csv(segment_out_dir / 'trade_residuals.csv', index=False)

    # Export Pairwise Consistency
    pairwise_output = []
    for (rune_a, rune_b), errors in pairwise_records.items():
        observed_ratio = sum((1 + e) for e in errors) / len(errors)
        expected_ratio = ist_prices[rune_a] / ist_prices[rune_b]
        pairwise_output.append({
            'Rune A': rune_a,
            'Rune B': rune_b,
            'Observed Ratio': observed_ratio * expected_ratio,
            'Expected Ratio': expected_ratio,
            'Error %': (observed_ratio - 1) * 100,
            'Trade Count': len(errors)
        })

    df_pairwise = pd.DataFrame(pairwise_output)
    df_pairwise.sort_values(by='Error %', key=lambda x: abs(x), ascending=False, inplace=True)
    df_pairwise.to_csv(segment_out_dir / 'pairwise_discrepancies.csv', index=False)

    print(f"{segment} consistency analysis complete.")