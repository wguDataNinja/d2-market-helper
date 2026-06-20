from bs4 import BeautifulSoup
import csv
import os

# Path to your saved HTML file
html_path = "/Users/buddy/Desktop/traderie/data/rune_list.html"
output_csv = "/Users/buddy/Desktop/traderie/data/rune_ids.csv"

# Load HTML
with open(html_path, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# Parse rune entries
items = []
for a_tag in soup.find_all("a", class_="item-img"):
    href = a_tag.get("href", "")
    img_tag = a_tag.find("img")
    alt = img_tag.get("alt") if img_tag else None

    if "/product/" in href and alt:
        try:
            item_id = href.split("/product/")[1].split("?")[0]
            items.append((alt.strip(), item_id.strip()))
        except IndexError:
            continue

# Save to CSV
with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Rune Name", "Item ID"])
    writer.writerows(items)

print(f"✅ Saved {len(items)} rune IDs to {output_csv}")