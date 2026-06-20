import os
import json
import csv

# Base paths
input_dir = "/data/.old/completed_trades"
base_output_dir = "/data"

for filename in os.listdir(input_dir):
    if not filename.endswith(".json"):
        continue

    parts = filename.replace(".json", "").split("_")
    if len(parts) < 5:
        print(f"Skipping malformed file: {filename}")
        continue

    # Extract metadata
    rune_base = parts[0].capitalize()
    platform = parts[2].upper()
    mode = parts[3].lower()
    ladder = parts[4].lower()

    short_mode = "SC" if mode == "softcore" else "HC"
    short_ladder = "L" if ladder == "ladder" else "NL"
    combo_key = f"{platform}_{short_mode}_{short_ladder}"

    rune_name = rune_base + " Rune"
    safe_rune = rune_name.replace(" ", "_")

    output_dir = os.path.join(base_output_dir, combo_key, "CompletedCSV")
    os.makedirs(output_dir, exist_ok=True)

    # Load trade data
    input_path = os.path.join(input_dir, filename)
    with open(input_path, "r") as f:
        trades = json.load(f)

    if not isinstance(trades, list):
        print(f"❌ Unexpected format in {filename} (expected list)")
        continue

    # Write to CSV
    output_file = os.path.join(output_dir, f"{safe_rune}.csv")
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["seller", "quantity", "updated_at", "price_summary"])

        for trade in trades:
            seller = trade.get("seller", "")
            quantity = trade.get("quantity", "")
            updated_at = trade.get("updated_at", "")
            price_summary = ", ".join(f"{item['quantity']} {item['name']}" for item in trade.get("price", []))
            writer.writerow([seller, quantity, updated_at, price_summary])

    print(f"✅ {safe_rune}.csv → {combo_key}/CompletedCSV")

print("\n🎉 All single-rune JSONs converted to individual CSVs.")