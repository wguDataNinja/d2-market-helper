import os
import re
import json
from bs4 import BeautifulSoup

TRADERIE_PATH = "/Traderie_page_files"

def extract_json_from_text(text):
    # Try to extract JSON-like blobs
    pattern = r'({.*?})'
    matches = re.findall(pattern, text, re.DOTALL)
    json_objects = []
    for match in matches:
        try:
            obj = json.loads(match)
            json_objects.append(obj)
        except json.JSONDecodeError:
            continue
    return json_objects

def explore_html(file_path):
    print(f"\n🧾 HTML: {file_path}")
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f, "html.parser")
        title = soup.title.string if soup.title else "No title"
        metas = soup.find_all("meta")
        print(f"Title: {title}")
        for meta in metas[:3]:  # Print first 3 meta tags
            print(f"  Meta: {meta}")

def explore_text_file(file_path):
    print(f"\n📄 TXT/JS: {file_path}")
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        jsons = extract_json_from_text(content)
        print(f"  Found {len(jsons)} JSON-like blobs")
        if jsons:
            print("  Sample keys:", list(jsons[0].keys())[:5])

def main():
    print(f"Exploring: {TRADERIE_PATH}\n")
    for root, _, files in os.walk(TRADERIE_PATH):
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith((".html",)):
                explore_html(filepath)
            elif file.endswith((".txt", ".js", ".json")):
                explore_text_file(filepath)

if __name__ == "__main__":
    main()