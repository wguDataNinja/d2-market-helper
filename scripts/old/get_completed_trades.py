import cloudscraper
import csv
from datetime import datetime

# Create scraper
scraper = cloudscraper.create_scraper()

# Cham Rune item ID from your list
item_id = "3191411278"

# API URL and params for completed trades
url = "https://traderie.com/api/diablo2resurrected/listings"
params = {
    "item": item_id,
    "completed": "true",
    "auction": "false",
    "page": "0"
}

# Output file
csv_path = "cham_completed.csv"

print("🔍 Fetching completed trades for Cham Rune...")

res = scraper.get(url, params=params)
if res.status_code != 200:
    print(f"❌ HTTP {res.status_code}")
    exit()

data = res.json()
listings = data.get("listings", [])

# Parse listings
rows = []
for l in listings:
    user = l.get("seller", {}).get("username", "?")
    quantity = l.get("amount", 1)
    updated = l.get("updated_at", "")
    price_items = l.get("prices", [])

    for p in price_items:
        price_name = p.get("name", "?")
        price_qty = p.get("quantity", 1)
        rows.append([user, quantity, price_qty, price_name, updated])

# Save to CSV
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Seller", "Quantity (Cham)", "Price Qty", "Price Item", "Updated At"])
    writer.writerows(rows)

print(f"✅ Saved {len(rows)} completed trades to {csv_path}")