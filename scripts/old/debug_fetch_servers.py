# debug_ist_fetch.py - Debug Ist Rune API calls for non-PC platforms

import json
import cloudscraper

CONFIG_PATH = "/server_configs.json"
IST_RUNE_ID = "2290642411"
TRADERIE_PLATFORM_MAP = {
    "pc": "pc",
    "xbox": "xbox",
    "switch": "switch",
    "playstation": "playstation"
}

# Load enabled configs
def load_enabled_configs(path):
    with open(path, "r", encoding="utf-8") as f:
        return [cfg for cfg in json.load(f) if cfg.get("enabled", False)]

# Perform request for each config
def debug_fetch():
    url = "https://traderie.com/api/diablo2resurrected/listings"
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    configs = load_enabled_configs(CONFIG_PATH)
    print("\nFetching Ist Rune listings from enabled non-PC platforms...\n")
    for cfg in configs:
        slug = cfg["slug"]
        platform_key = cfg["platform"].lower()
        platform = TRADERIE_PLATFORM_MAP.get(platform_key, "pc")
        mode = cfg["mode"]
        ladder = str(cfg["ladder"]).lower()

        params = {
            "completed": "true",
            "auction": "false",
            "prop_Platform": platform,
            "prop_Mode": mode,
            "prop_Ladder": ladder,
            "item": IST_RUNE_ID
        }

        print(f"\nConfig: {slug} | Platform: {platform} | Mode: {mode} | Ladder: {ladder}")
        try:
            response = scraper.get(url, params=params)
            print("Status Code:", response.status_code)
            content_type = response.headers.get("Content-Type", "")

            if "application/json" in content_type:
                data = response.json()
                print("Listings returned:", len(data.get("listings", [])))
            else:
                print("Unexpected content type:", content_type)
                print("Raw response:\n", response.text[:500])
        except Exception as e:
            print("Request failed:", e)

if __name__ == "__main__":
    debug_fetch()