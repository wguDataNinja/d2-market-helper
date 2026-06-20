# check_raw_trade_files_v3.py

import json
import os
from datetime import datetime, timezone

# File paths
file_paths = [
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_hc_l.json",
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_hc_nl.json",
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_sc_l.json",
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_sc_nl.json"
]

def read_file(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)
    return data

def analyze_trades(data):
    timestamps = []
    total_trades = 0

    for category in data:
        for item in data[category]:
            trades = data[category][item]
            total_trades += len(trades)
            for trade in trades:
                updated_at = trade.get('updated_at')
                if updated_at:
                    try:
                        dt = datetime.fromisoformat(updated_at.rstrip("Z")).replace(tzinfo=timezone.utc)
                        timestamps.append(dt)
                    except Exception:
                        continue

    if not timestamps:
        return total_trades, None, None

    oldest = min(timestamps)
    newest = max(timestamps)
    return total_trades, oldest, newest

def days_ago(ts):
    now = datetime.now(timezone.utc)
    delta = now - ts
    return f"{delta.days} days ago"

def print_report(file_path, count, oldest, newest):
    print(f"\nFile: {os.path.basename(file_path)}")
    print(f"Total trades: {count}")
    if oldest and newest:
        print(f"Oldest trade: {oldest.isoformat()} UTC ({days_ago(oldest)})")
        print(f"Newest trade: {newest.isoformat()} UTC ({days_ago(newest)})")
    else:
        print("No valid updated_at timestamps found.")

def main():
    for file_path in file_paths:
        try:
            data = read_file(file_path)
            count, oldest, newest = analyze_trades(data)
            print_report(file_path, count, oldest, newest)
        except Exception as e:
            print(f"\nError processing {file_path}: {e}")

if __name__ == "__main__":
    main()