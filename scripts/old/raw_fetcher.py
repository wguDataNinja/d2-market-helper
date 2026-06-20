# fetch_raw_trades.py
#!/usr/bin/env python3
"""
Traderie Rune Raw Trade Fetcher

Fetches completed trades from Traderie API and saves raw listings
per server combo for future processing.
"""

import json
import os
import time
from datetime import datetime
from collections import defaultdict
import cloudscraper

# Config paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEM_IDS_PATH = os.path.join(BASE_DIR, "data", "item_data.json")
CONFIG_PATH = os.path.join(BASE_DIR, "server_configs.json")
BASE_OUTPUT_DIR = os.path.join(BASE_DIR, "data/raw")
LOG_PATH = os.path.join(BASE_DIR, "fetch_log.txt")

# API Configuration
API_URL = "https://traderie.com/api/diablo2resurrected/listings"
MAX_RETRIES = 2
RETRY_DELAYS = [2, 5]  # seconds between retries

# Debug mode
DEBUG_MODE = False
DEBUG_ITEM_LIMIT = 3

def log(message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_configs(path):
    with open(path, "r", encoding="utf-8") as f:
        return [cfg for cfg in json.load(f) if cfg.get("enabled", True)]

def load_item_ids(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = {}
    for category in data.values():
        for name, entry in category.items():
            if isinstance(entry, dict) and "id" in entry:
                items[name] = entry["id"]
            else:
                items[name] = entry
    return items

def fetch_with_retries(scraper, url, params, item_name):
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

def main():
    start = time.time()
    log("Starting raw trade fetch")
    scraper = cloudscraper.create_scraper()

    try:
        servers = load_configs(CONFIG_PATH)
    except Exception as e:
        log(f"Error loading configs: {e}")
        return

    try:
        valid_items = load_item_ids(ITEM_IDS_PATH)
    except Exception as e:
        log(f"Error loading item IDs: {e}")
        return

    for cfg in servers:
        platform = cfg["platform"]
        mode = cfg["mode"]
        ladder = cfg["ladder"]
        slug = cfg.get("slug", f"{platform}_{mode}_{'l' if ladder else 'nl'}")
        log(f"Fetching server: {slug}")

        params_common = {
            "completed": "true",
            "auction": "false",
            "prop_Platform": platform.upper(),
            "prop_Mode": mode,
            "prop_Ladder": str(ladder).lower()
        }

        raw_output = defaultdict(list)

        item_list = list(valid_items.items())
        if DEBUG_MODE:
            item_list = item_list[:DEBUG_ITEM_LIMIT]

        for name, iid in item_list:
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

            raw_output[name].extend(listings)
            time.sleep(3)

        out_path = os.path.join(BASE_OUTPUT_DIR, f"raw_trades_{slug}.json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(raw_output, f, indent=2)

        log(f"Saved raw data to {out_path}")

    elapsed = round(time.time() - start, 2)
    log(f"Raw fetch complete in {elapsed} seconds")

if __name__ == '__main__':
    main()