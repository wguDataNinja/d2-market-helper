# fetch_completed_trades.py - Fetch raw completed trades by config

import json
import time
import cloudscraper
from datetime import datetime
from pathlib import Path
from tabulate import tabulate

# === Paths ===
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_OUTPUT_DIR = DATA_DIR / "raw"
ITEMS_JSON_PATH = DATA_DIR / "item_ids.json"
CONFIG_PATH = ROOT_DIR / "server_configs.json"
LOG_PATH = DATA_DIR / "fetch_log.txt"

# === Configurable Delays ===
PER_ITEM_DELAY = 5     # Time to wait between item fetches (in seconds)
RETRY_DELAY = 5        # Delay before retrying a failed fetch (in seconds)

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_configs(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [cfg for cfg in json.load(f) if cfg.get("enabled", True)]
    except Exception as e:
        log(f"Error loading configs: {e}")
        return []

def load_items(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"Error loading item IDs: {e}")
        return {}

def load_existing_data(output_path):
    if output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"Error loading existing data: {e}")
            return {}
    return {}

def fetch_listings(scraper, url, params, name):
    for attempt in range(2):
        try:
            res = scraper.get(url, params=params)
            if res.status_code != 200:
                log(f"HTTP {res.status_code} for {name} (attempt {attempt + 1})")
                time.sleep(RETRY_DELAY)
                continue
            raw = res.json()
            listings = raw.get("listings", [])
            if not isinstance(listings, list):
                log(f"Warning: 'listings' field for {name} is not a list. Treating as empty.")
                return []
            return listings
        except Exception as e:
            log(f"Fetch error for {name} (attempt {attempt + 1}): {e}")
            time.sleep(RETRY_DELAY)
    log(f"Giving up on {name} after 2 attempts.")
    return []

def sanitize_trade_entry(entry):
    seller_data = entry.get("seller", {}) or {}
    seller = seller_data.get("username", "?")
    raw_prices = entry.get("prices", []) or []
    price_list = [
        {
            "name": p.get("name", "?"),
            "quantity": p.get("quantity", 1)
        }
        for p in raw_prices if isinstance(p, dict)
    ]
    return {
        "seller": seller,
        "quantity": entry.get("amount", 1),
        "updated_at": entry.get("updated_at"),
        "price": price_list
    }

def print_summary_table(summary_data):
    headers = ["Config", "Category", "Item", "Existing", "Total Fetched", "New", "Skipped"]
    table_data = []
    for config, cat_data in summary_data.items():
        for category, items in cat_data.items():
            for name, stats in items.items():
                table_data.append([
                    config,
                    category,
                    name,
                    stats.get("existing", 0),
                    stats.get("total", 0),
                    stats.get("new", 0),
                    stats.get("dupes", 0)
                ])
    log("\nFetch Summary:\n" + tabulate(table_data, headers=headers, tablefmt="grid"))

def main():
    start_time = datetime.now()
    log("==== FETCH RUN STARTED ====")
    log(f"Started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    scraper = cloudscraper.create_scraper()
    url = "https://traderie.com/api/diablo2resurrected/listings"
    server_configs = load_configs(CONFIG_PATH)
    if not server_configs:
        log("No valid server configurations found. Exiting.")
        return

    categorized_items = load_items(ITEMS_JSON_PATH)
    if not categorized_items:
        log("No item IDs found. Exiting.")
        return

    RAW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    global_summary = {}

    for cfg in server_configs:
        slug = cfg.get("slug", "unknown")
        mode = cfg.get("mode", "normal")
        ladder = str(cfg.get("ladder", False)).lower()

        log(f"\nProcessing config: {slug} (Mode: {mode}, Ladder: {ladder})")
        output_path = RAW_OUTPUT_DIR / f"raw_trades_{slug}.json"

        existing_data = load_existing_data(output_path)
        if not isinstance(existing_data, dict):
            existing_data = {}

        existing_timestamps = {
            cat: {
                name: {
                    t.get("updated_at") for t in trades if isinstance(t, dict) and t.get("updated_at")
                }
                for name, trades in items.items() if isinstance(trades, list)
            }
            for cat, items in existing_data.items() if isinstance(items, dict)
        }

        updated_data = existing_data.copy()
        summary = {}

        for category, items in categorized_items.items():
            summary.setdefault(category, {})
            updated_data.setdefault(category, {})
            cat_existing = existing_timestamps.get(category, {})

            for name, item_id in items.items():
                existing_trades = updated_data[category].get(name, [])
                existing_count = len(existing_trades)
                log(f"Fetching {name} ({category}) - Existing trades: {existing_count}")
                params = {
                    "completed": "true",
                    "auction": "false",
                    "prop_Platform": "PC",
                    "prop_Mode": mode,
                    "prop_Ladder": ladder,
                    "item": item_id
                }
                listings = fetch_listings(scraper, url, params, name)
                total = len(listings)
                if total == 0:
                    summary[category][name] = {
                        "existing": existing_count,
                        "total": 0,
                        "new": 0,
                        "dupes": 0
                    }
                    log(f"No listings found for {name}")
                    continue

                existing = cat_existing.get(name, set())
                new_entries = []
                for entry in listings:
                    updated_at = entry.get("updated_at")
                    if not updated_at or updated_at in existing:
                        continue
                    trade = sanitize_trade_entry(entry)
                    new_entries.append(trade)
                    existing.add(updated_at)

                if new_entries:
                    updated_data[category].setdefault(name, []).extend(new_entries)

                dupes = total - len(new_entries)
                summary[category][name] = {
                    "existing": existing_count,
                    "total": total,
                    "new": len(new_entries),
                    "dupes": dupes
                }
                log(f"{name} stats: {existing_count} existing, {total} fetched, {len(new_entries)} new, {dupes} skipped")

                # Save after each item
                try:
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(updated_data, f, indent=2)
                    log(f"Partial data saved to {output_path}")
                except Exception as e:
                    log(f"Error saving partial data: {e}")

                time.sleep(PER_ITEM_DELAY)

            global_summary[slug] = summary

    print_summary_table(global_summary)
    end_time = datetime.now()
    duration = end_time - start_time
    log(f"\nCompleted at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Total duration: {duration}")
    log("==== FETCH RUN ENDED ====\n")

if __name__ == "__main__":
    main()