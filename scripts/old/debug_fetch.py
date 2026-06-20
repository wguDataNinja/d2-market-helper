import cloudscraper

scraper = cloudscraper.create_scraper()

url = "https://traderie.com/api/diablo2resurrected/listings"
params = {
    "itemTags": "true",
    "item": "4149485449",  # Ber Rune
    "selling": "true",
    "auction": "false",
    "page": "0"  # just like initial page load
}

print(f"🔍 Fetching Traderie page 0 (50 listings)...")

res = scraper.get(url, params=params)
if res.status_code != 200:
    print(f"❌ HTTP {res.status_code}")
    exit()

data = res.json()
listings = data.get("listings", [])
print(f"✅ {len(listings)} listings found")

for l in listings[:10]:  # preview up to 10
    user = l.get("seller", {}).get("username", "?")
    amount = l.get("amount", 1)
    wants = [f'{p.get("quantity", 1)} x {p.get("name", "?")}' for p in l.get("prices", [])]
    print(f"   - {user} offers {amount}x Ber Rune for {', '.join(wants) if wants else 'nothing?'}")