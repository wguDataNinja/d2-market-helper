# har_inspector.py

import json

# Update this to your actual HAR file path
har_path = "/traderie.com_Archive [25-05-22 12-18-02].har"

with open(har_path, "r") as f:
    har = json.load(f)

entries = har["log"]["entries"]

seen_urls = set()
seen_types = set()
json_snippets = []

for entry in entries:
    req = entry.get("request", {})
    res = entry.get("response", {})
    content = res.get("content", {})

    url = req.get("url", "")
    mime = content.get("mimeType", "")
    text = content.get("text", "")

    seen_urls.add(url)
    if mime:
        seen_types.add(mime)

    if mime == "application/json" and text:
        try:
            data = json.loads(text)
            snippet = json.dumps(data, indent=2)[:1000]  # Truncate long content
            json_snippets.append((url, snippet))
        except Exception:
            pass

# Output
print(f"🧵 Found {len(entries)} total entries\n")
print("🔗 Unique URL samples:")
for url in list(seen_urls)[:10]:
    print(" -", url)

print("\n🧾 Unique mimeTypes:")
for mt in seen_types:
    print(" -", mt)

print("\n📦 Sample JSON responses:")
for url, snippet in json_snippets[:3]:
    print(f"\nFrom {url}:\n{snippet}")