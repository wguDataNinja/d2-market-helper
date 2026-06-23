# calculate_rune_prices.py

import argparse
import pandas as pd
import re
import numpy as np
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
PRICES_DIR = DATA_DIR / "prices"
PRICES_DIR.mkdir(parents=True, exist_ok=True)

SEGMENTS = ["pc_hc_l", "pc_hc_nl", "pc_sc_l", "pc_sc_nl"]
ITEMS_PATH = DATA_DIR / "item_ids.json"

parser = argparse.ArgumentParser(description="Calculate Ist-normalized VWAP rune prices from extracted CSVs")
parser.add_argument("--input-dir", default=str(DATA_DIR / "extracted"),
                    help="Directory containing extracted_trades_{segment}.csv files (default: data/extracted)")
args = parser.parse_args()
EXTRACTED_DIR = Path(args.input_dir)

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

    model_rows = []
    and_decomposed_count = 0
    and_excluded_count = 0
    for _, row in df.iterrows():
        num_asks = row['NumAsks']
        if num_asks == 1:
            row_copy = row.copy()
            row_copy['is_and_decomposed'] = False
            model_rows.append(row_copy)
        elif num_asks == 2:
            items = [part.split(':') for part in row['Requested'].split(';')]
            for item_name, item_qty in items:
                new_row = row.copy()
                new_row['Requested'] = f"{item_name}:{item_qty}"
                new_row['is_and_decomposed'] = True
                model_rows.append(new_row)
            and_decomposed_count += 1
        else:
            and_excluded_count += 1

    model_input = pd.DataFrame(model_rows)

    results = []

    for rune in runes:
        if rune == 'Ist Rune':
            continue

        ist_for_rune = model_input[
            (model_input['Offered'].str.contains('Ist Rune')) &
            (model_input['Requested'].str.contains(re.escape(rune)))
            ].copy()

        ist_for_rune['IstQty'] = ist_for_rune['Offered'].apply(lambda x: parse_quantity(x, 'Ist Rune')).astype(int)
        ist_for_rune['RuneQty'] = ist_for_rune['Requested'].apply(lambda x: parse_quantity(x, rune)).astype(int)
        ist_for_rune['IstsPerRune'] = ist_for_rune['IstQty'] / ist_for_rune['RuneQty']

        rune_for_ist = model_input[
            (model_input['Offered'].str.contains(re.escape(rune))) &
            (model_input['Requested'].str.contains('Ist Rune'))
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
    print(f"Finished segment {segment}, saved: {output_file} (decomposed {and_decomposed_count} AND trades, excluded {and_excluded_count} multi-item)")