# /Users/buddy/Desktop/traderie/scripts/scan_ads.py

import os
from bs4 import BeautifulSoup

TARGET_DIR = "/"

AD_KEYWORDS = [
    "ad", "ads", "ad-", "ad_", "adsbygoogle", "googlesyndication",
    "gpt", "anyclip", "2mdn", "leaderboard", "safeframe", "sponsored"
]

TAGS_TO_SCAN = ["div", "iframe", "script", "section", "aside", "canvas"]

def scan_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        matches = []
        for tag in soup.find_all(TAGS_TO_SCAN):
            tag_str = str(tag).lower()
            if any(kw in tag_str for kw in AD_KEYWORDS):
                summary = {
                    "tag": tag.name,
                    "id": tag.get("id", ""),
                    "class": " ".join(tag.get("class", [])),
                    "attrs": list(tag.attrs.keys()),
                }
                matches.append(summary)

        if matches:
            print(f"\n📄 File: {os.path.basename(filepath)}")
            print(f"Matches found: {len(matches)}")
            for i, m in enumerate(matches, 1):
                print(f"  {i:>2}. <{m['tag']}> id='{m['id']}' class='{m['class']}' attrs={m['attrs']}")
    except Exception as e:
        print(f"⚠️ Error reading {filepath}: {e}")

def main():
    for root, _, files in os.walk(TARGET_DIR):
        for file in files:
            if file.lower().endswith(".html"):
                scan_file(os.path.join(root, file))

if __name__ == "__main__":
    main()