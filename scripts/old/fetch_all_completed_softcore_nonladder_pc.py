import csv
import json
import time
import cloudscraper

# Config
csv_path = "/data/rune_ids.csv"
output_path = "/data/PC_SC_NL/completed_softcore_nonladder_pc.json"

# Load rune name → item ID map
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rune_ids = {row["Rune Name"]: row["Item ID"] for row in reader}

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

# Results container
all_trades = {}

# Loop through each rune
for rune, item_id in rune_ids.items():
    params = {"item": item_id, **filters}
    print(f"🔍 Fetching recent trades for {rune}...")

    try:
        res = scraper.get(url, params=params)
        if res.status_code != 200:
            print(f"❌ {rune} failed ({res.status_code})")
            continue

        data = res.json()
        listings = data.get("listings", [])
        trades = []

        for l in listings:
            trades.append({
                "seller": l.get("seller", {}).get("username", "?"),
                "quantity": l.get("amount", 1),
                "updated_at": l.get("updated_at", ""),
                "price": [
                    {"name": p.get("name", "?"), "quantity": p.get("quantity", 1)}
                    for p in l.get("prices", [])
                ]
            })

        all_trades[rune] = trades
        print(f"✅ {len(trades)} trades found")

    except Exception as e:
        print(f"⚠️  Error fetching {rune}: {e}")

    time.sleep(10)  # Wait 10 seconds before next rune

# Save all results
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_trades, f, indent=2)

print(f"\n📦 All rune trades saved to {output_path}")