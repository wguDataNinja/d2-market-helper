# inspect_completed_trade_files.py

import json
import os
from datetime import datetime

# === File paths ===
COMPLETED_FILES = [
    "/Users/buddy/Desktop/traderie/data/completed_trades_pc_hc_l.json",
    "/Users/buddy/Desktop/traderie/data/completed_trades_pc_hc_nl.json",
    "/Users/buddy/Desktop/traderie/data/completed_trades_pc_sc_l.json",
    "/Users/buddy/Desktop/traderie/data/completed_trades_pc_sc_nl.json",
]

def parse_timestamp(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None

def inspect_file(path):
    print(f"\n📄 Inspecting: {os.path.basename(path)}")
    if not os.path.exists(path):
        print("❌ File not found.")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_pairs = len(data)
    total_trades = 0
    all_timestamps = []

    for key, entry in data.items():
        ratios = entry.get("ratios", {})
        for r_data in ratios.values():
            count = r_data.get("count", 0)
            ts = r_data.get("last_seen")
            total_trades += count
            if ts:
                parsed = parse_timestamp(ts)
                if parsed:
                    all_timestamps.append(parsed)

    if all_timestamps:
        earliest = min(all_timestamps)
        latest = max(all_timestamps)
        duration_days = max((latest - earliest).days, 1)
        trades_per_day = round(total_trades / duration_days, 2)
    else:
        earliest = latest = None
        trades_per_day = 0

    print(f"🧮 Rune Pairs: {total_pairs}")
    print(f"📊 Total Trades: {total_trades}")
    print(f"⏱️ Earliest Timestamp: {earliest}")
    print(f"⏱️ Latest Timestamp:   {latest}")
    print(f"📈 Avg Trades/Day: {trades_per_day}")

if __name__ == "__main__":
    for file_path in COMPLETED_FILES:
        inspect_file(file_path)