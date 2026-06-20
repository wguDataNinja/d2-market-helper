# filename: calculate_ist_values_batch.py

import json
import csv
import math
import statistics
from pathlib import Path
import networkx as nx
from collections import deque

# Input raw data files
RAW_FILES = [
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_hc_l.json",
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_hc_nl.json",
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_sc_l.json",
    "/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_sc_nl.json"
]

# Shared item catalog
ITEMS_PATH = Path("/data/item_data.json")

# Output directory
OUTPUT_DIR = Path("/data/normalized")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def parse_trade_ratios(ratios, ratio_map):
    raw = []
    for ratio_str, info in ratios.items():
        count = info.get("count", 0)
        if count >= 1 and ratio_str in ratio_map:
            raw.append((ratio_map[ratio_str], count))
    return raw


def weighted_average(pairs):
    total_count = sum(c for _, c in pairs)
    if total_count == 0:
        return 0.0
    return sum(v * c for v, c in pairs) / total_count


def filter_outliers_logspace(pairs, log_thresh=math.log(1.5)):
    expanded = []
    for val, count in pairs:
        expanded.extend([val] * count)
    if not expanded:
        return [], []
    base = statistics.median(expanded)
    inliers, outliers = [], []
    for val, count in pairs:
        try:
            if abs(math.log(val / base)) <= log_thresh:
                inliers.append((val, count))
            else:
                outliers.append((val, count))
        except (ValueError, ZeroDivisionError):
            outliers.append((val, count))
    return inliers, outliers


def build_graph(trades):
    G = nx.DiGraph()
    G.add_node("Ist Rune")  # ensure anchor always exists

    rune_trade_counts = {}
    fallback_edges = []

    for pair, data in trades.items():
        items = pair.split(":")
        if len(items) != 2:
            continue
        a, b = items[0].strip(), items[1].strip()
        meta = data.get("metadata", {})
        ratios = data.get("ratios", {})
        total = meta.get("total_trades", 0)
        rune_trade_counts[a] = rune_trade_counts.get(a, 0) + total
        rune_trade_counts[b] = rune_trade_counts.get(b, 0) + total
        ratio_map = meta.get("numeric_ratios", {})
        last_updated = meta.get("last_updated", "")

        valid = parse_trade_ratios(ratios, ratio_map)
        if len(valid) > 2:
            inliers, _ = filter_outliers_logspace(valid)
            if inliers:
                valid = inliers
        if valid:
            weighted = weighted_average(valid)
            low_conf = meta.get("low_confidence", False) or len(valid) < 2
        else:
            rec = meta.get("recommended_ratio", "")
            if rec in ratio_map:
                weighted = ratio_map[rec]
                low_conf = True
                fallback_edges.append((a, b, weighted))
            else:
                continue
        G.add_edge(a, b, weight=weighted, count=total, low_conf=low_conf, ts=last_updated)
        G.add_edge(b, a, weight=1.0/weighted, count=total, low_conf=low_conf, ts=last_updated)

    return G, rune_trade_counts, fallback_edges


def traverse_graph(G, start="Ist Rune"):
    if start not in G:
        print(f"WARNING: Anchor node '{start}' not found in graph. Skipping traversal.")
        return {}, {}, {}, {}

    values = {start: 1.0}
    low_conf = {start: False}
    hops = {start: 0}
    last_ts = {start: "9999-12-31T23:59:59Z"}
    queue = deque([(start, 1.0, False, 0, "9999-12-31T23:59:59Z")])
    visited = {start}

    while queue:
        node, val, lc, h, ts = queue.popleft()
        for nbr in G.neighbors(node):
            if nbr in visited:
                continue
            e = G[node][nbr]
            new_val = val * e["weight"]
            new_lc = lc or e.get("low_conf", False)
            new_h = h + 1
            new_ts = min(ts, e.get("ts", ts)) if ts and e.get("ts") else (e.get("ts") or ts)
            values[nbr] = new_val
            low_conf[nbr] = new_lc
            hops[nbr] = new_h
            last_ts[nbr] = new_ts
            visited.add(nbr)
            queue.append((nbr, new_val, new_lc, new_h, new_ts))
    return values, low_conf, hops, last_ts


def write_csv(path, item_ids, values, low_conf, counts, hops, last_ts):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item_name","item_id","ist_value","low_confidence","total_trades","hops","last_updated"])
        for name, iid in item_ids.items():
            val = values.get(name, "")
            w.writerow([
                name,
                iid,
                round(val,6) if isinstance(val, float) else "",
                low_conf.get(name, ""),
                counts.get(name, 0),
                hops.get(name, ""),
                last_ts.get(name, "")
            ])


def process_file(trades_path, items_path, output_path):
    trades = load_json(trades_path)
    items = load_json(items_path)
    item_ids = {name: data["id"] for sec in items.values() for name, data in sec.items()}
    G, counts, fallback = build_graph(trades)
    vals, lc, hops, ts = traverse_graph(G)
    write_csv(output_path, item_ids, vals, lc, counts, hops, ts)


def main():
    for raw_file in RAW_FILES:
        filename = Path(raw_file).stem.replace("raw_trades_", "") + "_normalized.csv"
        output_path = OUTPUT_DIR / filename
        print(f"Processing {raw_file} -> {output_path}")
        process_file(raw_file, ITEMS_PATH, output_path)
    print("Batch processing complete.")


if __name__ == "__main__":
    main()