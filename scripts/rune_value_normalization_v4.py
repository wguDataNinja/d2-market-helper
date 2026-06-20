# filename: rune_value_normalization_v4_1.py

import pandas as pd
import re
import numpy as np
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

# === Load rune list from item_data.json ===
item_data_path = str(DATA_DIR / "item_ids.json")

with open(item_data_path, 'r') as f:
    item_data = json.load(f)

runes = list(item_data['Runes'].keys())

# === Load trade data ===
trade_data_path = str(DATA_DIR / "normalized" / "normalized_trades_pc_sc_nl.csv")
df = pd.read_csv(trade_data_path)

# === Helper ===
def parse_quantity(s, rune):
    matches = re.findall(fr'{re.escape(rune)}:(\d+)', s)
    return int(matches[0]) if matches else 0

results = []

for rune in runes:
    if rune == 'Ist Rune':
        continue  # skip Ist itself

    single_item = df[df['NumAsks'] == 1]

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

    # VWAP
    def vwap(df):
        rune_sum = df['RuneQty'].sum()
        return df['IstQty'].sum() / rune_sum if rune_sum != 0 else None

    bid_price = vwap(ist_for_rune)
    bid_count = len(ist_for_rune)
    ask_price = vwap(rune_for_ist)
    ask_count = len(rune_for_ist)

    # Blended FMV (simple average when both exist)
    if bid_price is not None and ask_price is not None:
        blended = (bid_price + ask_price) / 2
    elif bid_price is not None:
        blended = bid_price
    elif ask_price is not None:
        blended = ask_price
    else:
        blended = None

    total_trades = bid_count + ask_count

    results.append({
        'Rune': rune.replace(' Rune',''),
        'Bid_Price': bid_price,
        'Bid_Count': bid_count,
        'Ask_Price': ask_price,
        'Ask_Count': ask_count,
        'Blended_FMV': blended,
        'Total_Trades': total_trades
    })

# === Assemble final dataframe ===
results_df = pd.DataFrame(results)
results_df = results_df.sort_values(by='Total_Trades', ascending=False)

# Print output
for _, row in results_df.iterrows():
    rune = row['Rune']
    print(f"\n==== {rune} ====")

    if pd.notna(row['Bid_Price']):
        print(f"Bid: {row['Bid_Price']:.2f} Ists (count: {int(row['Bid_Count'])})")
    else:
        print("No Bid trades")

    if pd.notna(row['Ask_Price']):
        print(f"Ask: {row['Ask_Price']:.2f} Ists (count: {int(row['Ask_Count'])})")
    else:
        print("No Ask trades")

    if pd.notna(row['Blended_FMV']):
        print(f"Blended FMV: {row['Blended_FMV']:.2f} Ists")
    else:
        print("No FMV")

# Export CSV
results_df.to_csv('rune_fmv_v4_1.csv', index=False)