import csv
import json
import os
import time
import cloudscraper

# Config
csv_path = "/data/rune_ids.csv"
output_path = "/data/completed_softcore_nonladder_pc.json"

# Load rune name → item ID map
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rune_ids = {row["Rune Name"]: row["Item ID"] for row in reader}

# Load existing trades (if any)
if os.path.exists(output_path):
    with open(output_path, "r", encoding="utf-8") as f:
        existing_data = json.load(f)
else:
    existing_data = {}

# Build timestamp sets for deduplication
existing_timestamps = {
    rune: {entry["updated_at"] for entry in trades}
    for rune, trades in existing_data.items()
}

# Traderie API setup
scraper = cloudscraper.create_scraper()
url = "https://traderie.com/api/diablo2resurrected/listings"
filters = {
    "completed": "true",
    "auction": "false",
    "prop_Platform": "PC",
    "prop_Mode": "softcore",
    "prop_Ladder": "false"
}

# Updated result container
all_trades = existing_data.copy()

# Fetch new trades per rune
for rune, item_id in rune_ids.items():
    print(f"\n🔍 Fetching recent trades for {rune}...")

    try:
        res = scraper.get(url, params={**filters, "item": item_id})
        if res.status_code != 200:
            print(f"❌ {rune} failed ({res.status_code})")
            continue

        listings = res.json().get("listings", [])
        new_trades = []

        seen = existing_timestamps.get(rune, set())

        for l in listings:
            updated_at = l.get("updated_at", "")
            if updated_at in seen:
                continue  # Skip duplicate

            trade = {
                "seller": l.get("seller", {}).get("username", "?"),
                "quantity": l.get("amount", 1),
                "updated_at": updated_at,
                "price": [
                    {"name": p.get("name", "?"), "quantity": p.get("quantity", 1)}
                    for p in l.get("prices", [])
                ]
            }

            new_trades.append(trade)
            seen.add(updated_at)

        if new_trades:
            all_trades.setdefault(rune, []).extend(new_trades)
            print(f"✅ {len(new_trades)} new trades added")
        else:
            print(f"⏭️  No new trades")

    except Exception as e:
        print(f"⚠️  Error fetching {rune}: {e}")

    time.sleep(10)

# Save updated result
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_trades, f, indent=2)

print(f"\n📦 Appended results saved to {output_path}")