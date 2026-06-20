# preview_raw_trades.py — corrected nested structure

import json

RAW_PATH = "/data/raw/raw_trades_pc_hc_nl.json"

with open(RAW_PATH, "r", encoding="utf-8") as f:
    raw = json.load(f)

print("\n📦 Top-level categories:", list(raw.keys()))

count = 0
for category, items in raw.items():
    print(f"\n📁 Category: {category}")
    for item_name, listings in items.items():
        print(f"🔍 {item_name} — {len(listings)} entries")
        for entry in listings[:2]:  # Preview first 2 entries per item
            print("—", entry)
            count += 1
            if count >= 10:
                break
        if count >= 10:
            break
    if count >= 10:
        break