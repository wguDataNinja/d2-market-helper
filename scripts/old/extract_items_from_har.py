# debug_first_two_pages.py

import json
import cloudscraper
import time

scraper = cloudscraper.create_scraper()
base_url = "https://traderie.com/api/diablo2resurrected/items"
limit = 24
offsets = [0, 24]

for offset in offsets:
    url = f"{base_url}?limit={limit}&offset={offset}"
    print(f"\n🔍 Fetching: {url}")
    res = scraper.get(url)

    if res.status_code != 200:
        print(f"❌ Failed at offset {offset}: HTTP {res.status_code}")
        continue

    data = res.json()
    items = data.get("items", [])
    print(f"✅ Received {len(items)} items")

    if not items:
        continue

    print(f"\n🧾 First 5 items on page starting at offset {offset}:")
    for i, item in enumerate(items[:5]):
        name = item.get("name") or item.get("description", "").split("\n")[0]
        print(f"{i + 1}. {name}  (ID: {item.get('id')})")

    time.sleep(5)