# Filename: rune_trade_report_v2.py

import os
import json
from collections import defaultdict, Counter
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
base_dir = str(ROOT_DIR / "data")
report_path = str(ROOT_DIR / "reports" / "rune_trade_report_v2.txt")
item_list_path = str(ROOT_DIR / "data" / "item_ids.json")

input_files = {
    "SC_L": os.path.join(base_dir, "pc_sc_l", "completed_pc_sc_l.json"),
    "SC_NL": os.path.join(base_dir, "pc_sc_nl", "completed_pc_sc_nl.json"),
    "HC_L": os.path.join(base_dir, "pc_hc_l", "completed_pc_hc_l.json"),
    "HC_NL": os.path.join(base_dir, "pc_hc_nl", "completed_pc_hc_nl.json"),
}

# Load item name list
with open(item_list_path, "r") as f:
    item_ids = json.load(f)

tracked_items = set()
for category in item_ids.values():
    tracked_items.update(category.keys())

# Load all trade data
server_data = {}
for name, path in input_files.items():
    with open(path, "r") as f:
        server_data[name] = json.load(f)

# Section 1: Total trades per server
server_trade_counts = {s: sum(len(trades) for trades in data.values()) for s, data in server_data.items()}

# Section 2: Top 5 trades by volume (item A : item B)
pair_counter = Counter()
for data in server_data.values():
    for sell_item, trades in data.items():
        for t in trades:
            for price_item in t.get("price", []):
                pair = f"{sell_item} : {price_item['name']}"
                pair_counter[pair] += 1
top_5_pairs = pair_counter.most_common(5)

# Section 3: Top 5 traded items overall (aggregated)
item_counter = Counter()
for data in server_data.values():
    for item, trades in data.items():
        item_counter[item] += len(trades)
        for t in trades:
            for p in t.get("price", []):
                item_counter[p["name"]] += 1
top_5_items = item_counter.most_common(5)

# Section 4: Per-item summary from item_ids.json
tracked_item_summaries = {}
for item in tracked_items:
    total = 0
    sample = []
    for data in server_data.values():
        trades = data.get(item, [])
        total += len(trades)
        sample.extend(trades)
    tracked_item_summaries[item] = {
        "count": total,
        "sample": sample[:3]  # Truncate for brevity
    }

# Generate report
lines = []

lines.append("=== TOTAL TRADES PER SERVER ===")
for server, count in server_trade_counts.items():
    lines.append(f"{server}: {count}")
lines.append("")

lines.append("=== TOP 5 TRADES BY VOLUME ===")
for i, (pair, count) in enumerate(top_5_pairs, 1):
    lines.append(f"{i}. {pair} — {count} trades")
lines.append("")

lines.append("=== TOP 5 TRADED ITEMS (BUY OR SELL) ===")
for i, (item, count) in enumerate(top_5_items, 1):
    lines.append(f"{i}. {item} — {count} appearances")
lines.append("")

lines.append("=== TRACKED ITEM SUMMARY ===")
for item, summary in tracked_item_summaries.items():
    lines.append(f"\n{item}: {summary['count']} trades")
    for trade in summary["sample"]:
        buyer = ", ".join([f"{p['quantity']}x {p['name']}" for p in trade.get("price", [])])
        lines.append(f"  - Seller: {trade['seller']}, Qty: {trade['quantity']}, For: {buyer}")

# Write to file
os.makedirs(os.path.dirname(report_path), exist_ok=True)
with open(report_path, "w") as f:
    f.write("\n".join(lines))

print(f"✅ Report written to: {report_path}")