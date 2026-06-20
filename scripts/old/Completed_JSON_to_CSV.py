import json
import csv
import os

# Paths
input_path = "/data/PC_SC_NL/completed_softcore_nonladder_pc.json"
output_dir = "/data/PC_SC_NL/CompletedCSV"

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Load JSON
with open(input_path, "r") as f:
    data = json.load(f)

# Loop through each rune
for rune_name, trades in data.items():
    # Create a valid filename
    safe_rune_name = rune_name.replace(" ", "_")
    output_file = os.path.join(output_dir, f"{safe_rune_name}.csv")

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow(["seller", "quantity", "updated_at", "price_summary"])

        for trade in trades:
            seller = trade.get("seller", "")
            quantity = trade.get("quantity", "")
            updated_at = trade.get("updated_at", "")
            price_list = trade.get("price", [])

            # Create readable price summary
            price_summary = ", ".join(f"{item['quantity']} {item['name']}" for item in price_list)

            # Write row
            writer.writerow([seller, quantity, updated_at, price_summary])

print("✅ All rune CSV files have been created.")