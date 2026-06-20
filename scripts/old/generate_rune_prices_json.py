# filename: generate_rune_prices_json.py

import json
import math
import statistics
from pathlib import Path
import networkx as nx

DATA_DIR = Path("/data")
OUTPUT_PATH = DATA_DIR / "rune_prices.json"
ITEMS_PATH = DATA_DIR / "item_data.json"

TRADE_FILES = {
    "pc_sc_nl": DATA_DIR / "completed_trades_pc_sc_nl.json",
    "pc_sc_l":  DATA_DIR / "completed_trades_pc_sc_l.json",
    "pc_hc_nl": DATA_DIR / "completed_trades_pc_hc_nl.json",
    "pc_hc_l":  DATA_DIR / "completed_trades_pc_hc_l.json"
}

def load_json(path):
    with open(path) as f:
        return json.load(f)

def parse_ratios(ratios, ratio_map):
    out = []
    for ratio_str, info in ratios.items():
        count = info.get("count", 0)
        if count >= 1 and ratio_str in ratio_map:
            out.append((ratio_map[ratio_str], count))
    return out

def weighted_average(pairs):
    total = sum(c for _, c in pairs)
    if total == 0: return 0.0
    return sum(v * c for v, c in pairs) / total

def filter_outliers_log(pairs, log_thresh=math.log(1.5)):
    vals = []
    for val, count in pairs:
        vals.extend([val] * count)
    if not vals:
        return [], []
    median = statistics.median(vals)
    inliers, outliers = [], []
    for val, count in pairs:
        try:
            if abs(math.log(val / median)) <= log_thresh:
                inliers.append((val, count))
            else:
                outliers.append((val, count))
        except:
            outliers.append((val, count))
    return inliers, outliers

def build_graph(trades):
    G = nx.DiGraph()
    for pair, data in trades.items():
        items = pair.split(":")
        if len(items) != 2: continue
        a, b = items[0].strip(), items[1].strip()
        ratios = data.get("ratios", {})
        meta = data.get("metadata", {})
        ratio_map = meta.get("numeric_ratios", {})
        valid = parse_ratios(ratios, ratio_map)

        if len(valid) > 2:
            valid, _ = filter_outliers_log(valid)
        if valid:
            avg = weighted_average(valid)
            low_conf = meta.get("low_confidence", False) or len(valid) < 2
        else:
            rec = meta.get("recommended_ratio", "")
            if rec not in ratio_map:
                continue
            avg = ratio_map[rec]
            low_conf = True

        ts = meta.get("last_updated", "")
        count = sum(c for _, c in valid) if valid else 0

        G.add_edge(a, b, weight=avg, count=count, low_conf=low_conf, ts=ts)
        G.add_edge(b, a, weight=1/avg, count=count, low_conf=low_conf, ts=ts)
    return G

def edge_cost(weight, count, low_conf):
    base_cost = abs(math.log(weight))
    trade_penalty = 1 / max(count, 1)
    conf_penalty = 2.0 if low_conf else 1.0
    return base_cost * conf_penalty + trade_penalty

def build_cost_graph(G):
    CG = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        cost = edge_cost(data["weight"], data["count"], data["low_conf"])
        CG.add_edge(u, v, weight=cost)
    return CG

def is_high_conf_path(path, G):
    if len(path) > 3:
        return False
    for i in range(len(path)-1):
        edge = G[path[i]][path[i+1]]
        if edge["low_conf"] or edge["count"] < 10:
            return False
    return True

def compute_ist_values(G):
    CG = build_cost_graph(G)
    prices = {}
    if "Ist Rune" not in G:
        return prices
    for node in G.nodes:
        if "Rune" not in node:
            continue
        if node == "Ist Rune":
            prices[node] = {"ist_value": 1.0, "low_confidence": False}
            continue
        if G.has_edge(node, "Ist Rune"):
            edge = G[node]["Ist Rune"]
            val = edge["weight"]
            low_conf = edge["low_conf"] or edge["count"] < 10
            prices[node] = {"ist_value": round(1 / val, 4), "low_confidence": low_conf}
        else:
            try:
                cost, path = nx.single_source_dijkstra(CG, source="Ist Rune", target=node)
                val = 1.0
                for i in range(len(path)-1):
                    val *= G[path[i]][path[i+1]]["weight"]
                low_conf = not is_high_conf_path(path, G)
                prices[node] = {"ist_value": round(val, 4), "low_confidence": low_conf}
            except:
                continue
    return dict(sorted(prices.items(), key=lambda x: -x[1]["ist_value"]))

def main():
    all_prices = {}
    for slug, trade_path in TRADE_FILES.items():
        trades = load_json(trade_path)
        G = build_graph(trades)
        rune_prices = compute_ist_values(G)
        all_prices[slug] = rune_prices

    with open(OUTPUT_PATH, "w") as f:
        json.dump(all_prices, f, indent=2)

    print(f"✅ rune_prices.json written to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
