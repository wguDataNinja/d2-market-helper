import os
import csv
import json
from collections import defaultdict

def parse_rune_trades(data_dir):
    trade_data = defaultdict(lambda: defaultdict(int))

    for filename in os.listdir(data_dir):
        if not filename.endswith('_Rune.csv'):
            continue

        base_rune = filename.split('_')[0]
        file_path = os.path.join(data_dir, filename)

        with open(file_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    quantity = int(row['quantity'])
                    price_count = int(row['price_count'])
                    price_rune = row['price_rune']
                    key = f"{base_rune}:{price_rune}"
                    ratio = f"{quantity}:{price_count}"
                    trade_data[key][ratio] += 1
                except (ValueError, KeyError):
                    continue  # Skip malformed rows

    return trade_data

if __name__ == "__main__":
    base_dir = "/data"

    for combo_dir in os.listdir(base_dir):
        cleaned_dir = os.path.join(base_dir, combo_dir, "CleanedCSV")

        if not os.path.isdir(cleaned_dir):
            continue

        print(f"\n🔍 Parsing ratios for: {combo_dir}")

        trades = parse_rune_trades(cleaned_dir)

        if not trades:
            print(f"⚠️  No trade ratios found in {combo_dir}")
            continue

        output_filename = f"rune_trade_ratios_{combo_dir}.json"
        output_path = os.path.join(base_dir, output_filename)

        with open(output_path, "w") as f:
            json.dump(trades, f, indent=2)

        print(f"✅ Saved to: {output_path}")

    print("\n🎉 Done parsing all trade ratio sets.")