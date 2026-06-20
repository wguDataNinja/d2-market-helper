import csv
import json
import os
import time
import cloudscraper

# Config
csv_path = "/data/rune_ids.csv"
output_dir = "/data/.old/completed_trades"
log_path = "/data/log.txt"

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Load rune name → item ID map
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rune_ids = {row["Rune Name"]: row["Item ID"] for row in reader}

# Traderie API setup
scraper = cloudscraper.create_scraper()
url = "https://traderie.com/api/diablo2resurrected/listings"

# Filters to loop through
MODES = ["softcore", "hardcore"]
LADDERS = ["true", "false"]
PLATFORM = "PC"

# Start log file
with open(log_path, "w", encoding="utf-8") as log:
    log.write("=== Traderie Fetch Log ===\n")

# Begin looping through combinations
for mode in MODES:
    for ladder in LADDERS:
        print(f"\n🌐 Platform: {PLATFORM}, Mode: {mode}, Ladder: {ladder}")

        for rune_name, item_id in rune_ids.items():
            filters = {
                "completed": "true",
                "auction": "false",
                "prop_Platform": PLATFORM,
                "prop_Mode": mode,
                "prop_Ladder": ladder,
                "item": item_id
            }

            safe_rune = rune_name.lower().replace(" ", "_")
            ladder_label = "ladder" if ladder == "true" else "nonladder"
            filename = f"{safe_rune}_pc_{mode}_{ladder_label}.json"
            filepath = os.path.join(output_dir, filename)

            print(f"🔍 Fetching {rune_name} → {filename}")

            try:
                res = scraper.get(url, params=filters)
                if res.status_code != 200:
                    print(f"❌ Error {res.status_code} for {rune_name}")
                    continue

                listings = res.json().get("listings", [])
                trades = []

                for l in listings:
                    trades.append({
                        "seller": l.get("seller", {}).get("username", "?"),
                        "quantity": l.get("amount", 1),
                        "updated_at": l.get("updated_at", ""),
                        "price": [
                            {"name": p.get("name", "?"), "quantity": p.get("quantity", 1)}
                            for p in l.get("prices") or []
                        ]
                    })

                if trades:
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(trades, f, indent=2)
                    print(f"✅ Saved {len(trades)} trades to {filename}")
                else:
                    print(f"⚠️ No trades found for {rune_name}")

                # Log to file
                with open(log_path, "a", encoding="utf-8") as log:
                    log.write(f"{filename}: {len(trades)} trades\n")

            except Exception as e:
                print(f"⚠️ Error fetching {rune_name}: {e}")

            time.sleep(10)

print("\n🏁 Done with all PC mode/ladder combinations.")