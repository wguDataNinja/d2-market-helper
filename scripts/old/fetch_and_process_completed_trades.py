# fetch_and_process_trades.py
#!/usr/bin/env python3
"""
Traderie Rune Trade Processor

This script fetches completed trades from Traderie, filters and processes
valid price exchanges, and outputs a single JSON file per server environment.
"""

import json
import os
import time
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import cloudscraper

# Configuration paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEM_IDS_PATH = os.path.join(BASE_DIR, "data", "item_ids.json")
CONFIG_PATH = os.path.join(BASE_DIR, "server_configs.json")
BASE_OUTPUT_DIR = os.path.join(BASE_DIR, "data")
LOG_PATH = os.path.join(BASE_DIR, "fetch_log.txt")

# API Configuration
API_URL = "https://traderie.com/api/diablo2resurrected/listings"
MAX_RETRIES = 2
RETRY_DELAYS = [2, 5]  # seconds between retries

# Confidence and rounding constants
CONFIDENCE_MIN_TRADES = 3
CONFIDENCE_MAX_DAYS = 7
ROUNDING_STEPS = [1, 0.5, 1/3]


def log(message):
    """Write a timestamped log message to stdout and log file."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_configs(path):
    """Load server configurations from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return [cfg for cfg in json.load(f) if cfg.get("enabled", True)]


def load_item_ids(path):
    """Load and flatten valid item IDs from JSON file, returning both forward and reverse lookups."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = {}
    for category in data.values():
        items.update(category)
    reverse_items = {v: k for k, v in items.items()}
    return items, reverse_items


def fetch_with_retries(scraper, url, params, item_name):
    """Fetch data with retries and backoff."""
    for attempt, delay in enumerate(RETRY_DELAYS + [0]):
        try:
            res = scraper.get(url, params=params)
            if res.status_code == 200:
                return res
            log(f"HTTP {res.status_code} for {item_name} (attempt {attempt+1}/{MAX_RETRIES+1})")
        except Exception as e:
            log(f"Fetch error for {item_name} (attempt {attempt+1}/{MAX_RETRIES+1}): {e}")
        if attempt < MAX_RETRIES:
            log(f"Retrying {item_name} in {delay} seconds...")
            time.sleep(delay)
        else:
            log(f"Failed to fetch data for {item_name} after {MAX_RETRIES+1} attempts.")
            return None


def sanitize_trade_entry(entry, valid_items, reverse_items):
    """Validate and sanitize a trade entry; return None if invalid."""
    raw = entry.get("prices", [])
    if not isinstance(raw, list):
        return None
    price_list = []
    for p in raw:
        if not isinstance(p, dict):
            continue
        iid = p.get("item_id")
        if isinstance(iid, str) and iid.isdigit():
            iid = int(iid)
        if iid in reverse_items:
            name_key = reverse_items[iid]
            price_list.append({"name": name_key, "quantity": p.get("quantity", 1)})
            continue
        nm = p.get("name", "")
        base = " ".join(nm.split()[:2])
        if base in valid_items:
            price_list.append({"name": base, "quantity": p.get("quantity", 1)})
    if len(price_list) != 1:
        return None
    return {
        "quantity": entry.get("amount", 1),
        "updated_at": entry.get("updated_at"),
        "price": price_list
    }


def smart_round(val):
    """Round to nearest meaningful ratio (preferring whole numbers if close)."""
    candidates = []
    base = round(val)
    for step in ROUNDING_STEPS:
        for offset in [-2, -1, 0, 1, 2]:
            r = round(base + offset * step, 1)
            if r > 0:
                candidates.append(r)
    return min(candidates, key=lambda x: abs(x - val))


def calculate_numeric_ratio(base_qty, price_qty):
    """Compute numeric ratio value or return None if invalid."""
    if price_qty <= 0:
        return None
    return base_qty / price_qty


def process_trades_to_ratios(raw_trades):
    """Aggregate raw trades into enriched ratio data per item pair."""
    pair_data = defaultdict(lambda: defaultdict(list))
    now = datetime.utcnow()
    for base_item, trades in raw_trades.items():
        for trade in trades:
            ts = trade.get("updated_at")
            if not ts:
                continue
            base_qty = trade.get("quantity", 1)
            for price in trade.get("price", []):
                price_item = price.get("name")
                price_qty = price.get("quantity", 1)
                if not price_item or base_item == price_item:
                    continue
                key = f"{base_item}:{price_item}"
                ratio_str = f"{base_qty}:{price_qty}"
                pair_data[key][ratio_str].append(ts)

    enriched = {}
    for key, ratios in pair_data.items():
        flat = []
        numeric_map = {}
        ratio_meta = {}
        last_up = None
        for ratio_str, times in ratios.items():
            try:
                b, p = map(int, ratio_str.split(':'))
            except ValueError:
                continue
            num = calculate_numeric_ratio(b, p)
            if num is None:
                continue
            numeric_map[ratio_str] = round(num, 4)
            count = len(times)
            flat.extend([num] * count)
            last = max(times)
            ratio_meta[ratio_str] = {"count": count, "last_seen": last}
            if not last_up or last > last_up:
                last_up = last
        if not flat or not last_up:
            continue
        total = len(flat)
        most_common = max(ratios.items(), key=lambda x: len(x[1]))[0]
        median_val = sorted(flat)[total // 2]
        weighted = sum(flat) / total
        rec = smart_round(weighted)
        try:
            dt = datetime.strptime(last_up, "%Y-%m-%dT%H:%M:%SZ")
            low_conf = total < CONFIDENCE_MIN_TRADES or (now - dt).days > CONFIDENCE_MAX_DAYS
        except Exception:
            low_conf = True
        enriched[key] = {
            "ratios": ratio_meta,
            "metadata": {
                "total_trades": total,
                "most_common": most_common,
                "median_ratio": round(median_val, 1),
                "weighted_avg": round(weighted, 1),
                "recommended_ratio": f"{rec}:1",
                "last_updated": last_up,
                "numeric_ratios": numeric_map,
                "low_confidence": low_conf
            }
        }
    return enriched


def load_existing_data(path):
    """Load JSON existing data or return empty dict."""
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            log(f"Error parsing {path}, starting fresh.")
    return {}


def get_existing_timestamps(data):
    """Collect all last_seen timestamps to avoid duplicates."""
    s = set()
    for item in data.values():
        for info in item.get('ratios', {}).values():
            ts = info.get('last_seen')
            if ts:
                s.add(ts)
    return s


# fetch_and_process_trades.py

def main():
    start = time.time()
    log("Starting trade data fetch and processing")
    scraper = cloudscraper.create_scraper()

    try:
        servers = load_configs(CONFIG_PATH)
    except Exception as e:
        log(f"Error loading configs: {e}")
        return

    try:
        valid_items, reverse_items = load_item_ids(ITEM_IDS_PATH)
    except Exception as e:
        log(f"Error loading item IDs: {e}")
        return

    for cfg in servers:
        platform = cfg["platform"]       # e.g. "pc"
        mode = cfg["mode"]               # "softcore" or "hardcore"
        ladder = cfg["ladder"]           # bool
        slug = cfg.get("slug", f"{platform}_{mode}_{'l' if ladder else 'nl'}")
        log(f"Processing server: {slug}")

        params_common = {
            "completed": "true",
            "auction": "false",
            "prop_Platform": platform.upper(),  # "PC"
            "prop_Mode": mode,                  # "softcore"/"hardcore"
            "prop_Ladder": str(ladder).lower() # "true"/"false"
        }

        out_path = os.path.join(BASE_OUTPUT_DIR, f"completed_trades_{slug}.json")
        existing = load_existing_data(out_path)
        seen = get_existing_timestamps(existing)
        trades_by_item = defaultdict(list)

        for name, iid in valid_items.items():
            params = {**params_common, "item": str(iid)}
            log(f"Fetching trades for {name} with params: {params}")
            res = fetch_with_retries(scraper, API_URL, params, name)
            if not res:
                continue

            try:
                listings = res.json().get("listings", [])
                log(f"Received {len(listings)} listings for {name}")
            except Exception as e:
                log(f"Error parsing JSON for {name}: {e}")
                continue

            accepted = skipped = 0
            for e in listings:
                ts = e.get("updated_at")
                if ts in seen:
                    skipped += 1
                    continue
                trade = sanitize_trade_entry(e, valid_items, reverse_items)
                if not trade:
                    skipped += 1
                    continue
                trades_by_item[name].append(trade)
                seen.add(ts)
                accepted += 1
            log(f"{name}: accepted {accepted}, skipped {skipped}")
            time.sleep(3)
        trades_by_item = {k: v for k, v in trades_by_item.items() if v}
        enriched = process_trades_to_ratios(trades_by_item)
        existing.update(enriched)

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        log(f"Wrote {len(existing)} entries to {out_path}")

    elapsed = round(time.time() - start, 2)
    log(f"Run complete in {elapsed} seconds")


if __name__ == '__main__':
    main()