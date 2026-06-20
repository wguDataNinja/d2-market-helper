# calculate_rune_prices.py

import pandas as pd
import re
import numpy as np
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

# Config
EXTRACTED_DIR = DATA_DIR / "extracted"
PRICES_DIR = DATA_DIR / "prices"
PRICES_DIR.mkdir(parents=True, exist_ok=True)

SEGMENTS = ["pc_hc_l", "pc_hc_nl", "pc_sc_l", "pc_sc_nl"]
ITEMS_PATH = DATA_DIR / "item_ids.json"

# Load valid runes
with open(ITEMS_PATH, 'r') as f:
    item_data = json.load(f)
runes = list(item_data['Runes'].keys())


# Helper
def parse_quantity(s, rune):
    matches = re.findall(fr'{re.escape(rune)}:(\d+)', s)
    return int(matches[0]) if matches else 0


# Main function
for segment in SEGMENTS:
    file_path = EXTRACTED_DIR / f"extracted_trades_{segment}.csv"
    df = pd.read_csv(file_path)

    # Count requested items for filtering
    df['NumAsks'] = df['Requested'].str.count(':')

    results = []

    for rune in runes:
        if rune == 'Ist Rune':
            continue

        single_item = df[df['NumAsks'] == 1]  # single rune requests have 0 semicolons

        # Ist for Rune (bid side)
        ist_for_rune = single_item[
            (single_item['Offered'].str.contains('Ist Rune')) &
            (single_item['Requested'].str.contains(re.escape(rune)))
            ].copy()

        ist_for_rune['IstQty'] = ist_for_rune['Offered'].apply(lambda x: parse_quantity(x, 'Ist Rune')).astype(int)
        ist_for_rune['RuneQty'] = ist_for_rune['Requested'].apply(lambda x: parse_quantity(x, rune)).astype(int)
        ist_for_rune['IstsPerRune'] = ist_for_rune['IstQty'] / ist_for_rune['RuneQty']

        # Rune for Ist (ask side)
        rune_for_ist = single_item[
            (single_item['Offered'].str.contains(re.escape(rune))) &
            (single_item['Requested'].str.contains('Ist Rune'))
            ].copy()

        rune_for_ist['IstQty'] = rune_for_ist['Requested'].apply(lambda x: parse_quantity(x, 'Ist Rune')).astype(int)
        rune_for_ist['RuneQty'] = rune_for_ist['Offered'].apply(lambda x: parse_quantity(x, rune)).astype(int)
        rune_for_ist['IstsPerRune'] = rune_for_ist['IstQty'] / rune_for_ist['RuneQty']

        # Outlier filter
        ist_for_rune = ist_for_rune[(ist_for_rune['IstsPerRune'] >= 0.5) & (ist_for_rune['IstsPerRune'] <= 50)]
        rune_for_ist = rune_for_ist[(rune_for_ist['IstsPerRune'] >= 0.5) & (rune_for_ist['IstsPerRune'] <= 50)]


        # VWAP calculation
        def vwap(df):
            rune_sum = df['RuneQty'].sum()
            return df['IstQty'].sum() / rune_sum if rune_sum != 0 else None


        bid_price = vwap(ist_for_rune)
        bid_count = len(ist_for_rune)
        ask_price = vwap(rune_for_ist)
        ask_count = len(rune_for_ist)

        blended = None
        if bid_price is not None and ask_price is not None:
            blended = (bid_price + ask_price) / 2
        elif bid_price is not None:
            blended = bid_price
        elif ask_price is not None:
            blended = ask_price

        total_trades = bid_count + ask_count

        results.append({
            'Rune': rune.replace(' Rune', ''),
            'Bid_Price': bid_price,
            'Bid_Count': bid_count,
            'Ask_Price': ask_price,
            'Ask_Count': ask_count,
            'Blended_FMV': blended,
            'Total_Trades': total_trades
        })

    # Export CSV for this segment
    results_df = pd.DataFrame(results).sort_values(by='Total_Trades', ascending=False)
    output_file = PRICES_DIR / f"rune_prices_{segment}.csv"
    results_df.to_csv(output_file, index=False)
    print(f"Finished segment {segment}, saved: {output_file}")