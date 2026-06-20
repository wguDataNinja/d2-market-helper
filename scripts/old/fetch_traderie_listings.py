import cloudscraper

scraper = cloudscraper.create_scraper()

url = "https://traderie.com/api/diablo2resurrected/listings"
params = {
    "itemTags": "true",
    "item": "4149485449",
    "selling": "true",
    "auction": "false",
    "page": "0",
    "prop_Platform": "PC",
    "prop_Ladder": "false"
}

response = scraper.get(url, params=params)

if response.status_code == 200:
    listings = response.json()
    print(f"✅ {len(listings)} listings found")
else:
    print(f"❌ Cloudflare blocked it: {response.status_code}")