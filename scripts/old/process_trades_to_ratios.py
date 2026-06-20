# process_trades_to_ratios.py – Converts raw trades to ratio stats

import json
import os
from collections import defaultdict, Counter
from statistics import median
from datetime import datetime
from pathlib import Path

# --- Paths ---
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR
ITEM_IDS_PATH = DATA_DIR / "item_data.json"
CONFIG_PATH = ROOT_DIR / "server_configs.json"

SKIP_MULTI_ITEM_TRADES = True
SKIP_UNKNOWN_ITEMS = True

# --- Helpers ---

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def is_valid_listing(entry):
    return (
        isinstance(entry.get("quantity"), int) and entry["quantity"] > 0 and
        isinstance(entry.get("price"), list) and len(entry["price"]) > 0
    )

def get_ratio_string(sell_qty, price_qty):
    return f"{sell_qty}:{price_qty}"

def to_numeric_ratio(ratio_str):
    a, b = map(int, ratio_str.split(":"))
    return round(a / b, 5) if b != 0 else 0

def load_enabled_slugs(config_path):
    configs = load_json(config_path)
    return [cfg["slug"] for cfg in configs if cfg.get("enabled", True)]

def process_raw_data(raw_data, known_item_names):
    output = defaultdict(lambda: {"ratios": Counter(), "timestamps": []})

    for category_data in raw_data.values():
        if not isinstance(category_data, dict):
            continue
        for base_item, listings in category_data.items():
            if not isinstance(listings, list):
                continue
            for entry in listings:
                if not isinstance(entry, dict):
                    continue
                if not is_valid_listing(entry):
                    continue

                prices = entry["price"]
                if SKIP_MULTI_ITEM_TRADES and len(prices) > 1:
                    continue

                price = prices[0]
                if SKIP_UNKNOWN_ITEMS and price["name"] not in known_item_names:
                    continue

                ratio_key = f"{base_item}:{price['name']}"
                ratio_str = get_ratio_string(entry["quantity"], price.get("quantity", 1))

                output[ratio_key]["ratios"][ratio_str] += 1
                output[ratio_key]["timestamps"].append((ratio_str, entry["updated_at"]))

    return output

def build_output(raw_stats):
    result = {}
    summary = {}

    for key, data in raw_stats.items():
        ratio_counts = data["ratios"]
        timestamps = dict(data["timestamps"])

        ratios_dict = {
            ratio: {
                "count": count,
                "last_seen": timestamps.get(ratio)
            } for ratio, count in ratio_counts.items()
        }

        numeric_map = {r: to_numeric_ratio(r) for r in ratio_counts}
        trades = []
        for r, count in ratio_counts.items():
            trades.extend([numeric_map[r]] * count)

        most_common = ratio_counts.most_common(1)[0][0]
        median_val = median(trades) if trades else 0
        weighted_avg = round(sum(trades) / len(trades), 5) if trades else 0
        low_conf = len(trades) < 3

        result[key] = {
            "ratios": ratios_dict,
            "metadata": {
                "total_trades": sum(ratio_counts.values()),
                "most_common": most_common,
                "median_ratio": median_val,
                "weighted_avg": weighted_avg,
                "numeric_ratios": numeric_map,
                "recommended_ratio": most_common,
                "low_confidence": low_conf,
                "last_updated": max(timestamps.values(), default=None)
            }
        }

        summary[key] = {
            "count": sum(ratio_counts.values()),
            "low_confidence": low_conf
        }

    return result, summary

def merge_outputs(old_data, new_data):
    total_added = 0
    for key, new_entry in new_data.items():
        if key not in old_data:
            old_data[key] = new_entry
            total_added += new_entry["metadata"]["total_trades"]
            continue

        old_ratios = old_data[key]["ratios"]
        new_ratios = new_entry["ratios"]
        for ratio, stats in new_ratios.items():
            if ratio in old_ratios:
                old_ratios[ratio]["count"] += stats["count"]
                old_ts = old_ratios[ratio]["last_seen"]
                new_ts = stats["last_seen"]
                old_ratios[ratio]["last_seen"] = max(old_ts, new_ts)
            else:
                old_ratios[ratio] = stats
                total_added += stats["count"]

        total = sum(r["count"] for r in old_ratios.values())
        numeric_map = {r: to_numeric_ratio(r) for r in old_ratios}
        trades = []
        for r, stats in old_ratios.items():
            trades.extend([numeric_map[r]] * stats["count"])

        most_common = max(old_ratios.items(), key=lambda x: x[1]["count"])[0]
        median_val = median(trades)
        weighted_avg = round(sum(trades) / len(trades), 5)
        low_conf = len(trades) < 3
        last_updated = max(r["last_seen"] for r in old_ratios.values())

        old_data[key]["metadata"] = {
            "total_trades": total,
            "most_common": most_common,
            "median_ratio": median_val,
            "weighted_avg": weighted_avg,
            "numeric_ratios": numeric_map,
            "recommended_ratio": most_common,
            "low_confidence": low_conf,
            "last_updated": last_updated
        }

    return old_data, total_added

def main():
    enabled_slugs = load_enabled_slugs(CONFIG_PATH)
    item_data = load_json(ITEM_IDS_PATH)
    known_item_names = set()
    for group in item_data.values():
        known_item_names.update(group.keys())

    for slug in enabled_slugs:
        raw_path = RAW_DIR / f"raw_trades_{slug}.json"
        processed_path = PROCESSED_DIR / f"completed_trades_{slug}.json"

        if not raw_path.exists():
            print(f"⚠️ Skipping missing raw file: {raw_path}")
            continue

        raw_data = load_json(raw_path)
        processed, summary = build_output(process_raw_data(raw_data, known_item_names))

        if processed_path.exists():
            existing_result = load_json(processed_path)
        else:
            existing_result = {}

        merged_result, total_added = merge_outputs(existing_result, processed)

        with open(processed_path, "w", encoding="utf-8") as f:
            json.dump(merged_result, f, indent=2)

        print(f"✅ Processed {slug}: {len(summary)} unique ratios, {total_added} new trades added")

if __name__ == "__main__":
    main()