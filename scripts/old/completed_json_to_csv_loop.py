import json
import csv
import os

# 👇 Change this block for each variant
platform = "PC"
mode = "hardcore"  # or "softcore"
ladder = "false"   # or "true"
shortcode = f"{platform}_{mode[:2].upper()}_{'L' if ladder == 'true' else 'NL'}"

# Paths
input_path = f"/data/{shortcode}/completed_{mode}_{'ladder' if ladder == 'true' else 'nonladder'}_{platform.lower()}.json"
output_dir = f"/data/{shortcode}/CompletedCSV"

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Load JSON
with open(input_path, "r") as f:
    data = json.load(f)

for rune_name, trades in data.items():
    safe_rune_name = rune_name.replace(" ", "_")
    output_file = os.path.join(output_dir, f"{safe_rune_name}.csv")

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["seller", "quantity", "updated_at", "price_summary"])
        for trade in trades:
            seller = trade.get("seller", "")
            quantity = trade.get("quantity", "")
            updated_at = trade.get("updated_at", "")
            price_summary = ", ".join(f"{item['quantity']} {item['name']}" for item in trade.get("price", []))
            writer.writerow([seller, quantity, updated_at, price_summary])

print(f"✅ Completed: {shortcode} → {output_dir}")