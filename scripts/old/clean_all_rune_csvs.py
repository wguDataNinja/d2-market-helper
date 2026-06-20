import os
import glob
import pandas as pd
import re

# Base directory containing PC_SC_L, PC_HC_L, etc.
base_dir = "/data"

# Regex pattern: e.g., "2 Ist Rune"
pattern = re.compile(r'^(\d+)\s+([A-Za-z]+)\s+Rune$')

# Loop through all subdirectories
for combo_dir in os.listdir(base_dir):
    full_combo_path = os.path.join(base_dir, combo_dir)
    completed_dir = os.path.join(full_combo_path, "CompletedCSV")

    if not os.path.isdir(completed_dir):
        continue  # Skip non-directories or folders without CSVs

    print(f"\n🔍 Cleaning rune trades in: {combo_dir}")

    cleaned_dir = os.path.join(full_combo_path, "CleanedCSV")
    os.makedirs(cleaned_dir, exist_ok=True)

    for filepath in glob.glob(os.path.join(completed_dir, '*_Rune.csv')):
        filename = os.path.basename(filepath)
        df = pd.read_csv(filepath)

        # Drop zero quantity trades
        df = df[df['quantity'] > 0]

        # Match valid single-rune trades, handling NaNs safely
        matches = df['price_summary'].fillna("").str.match(pattern)
        clean_df = df[matches].copy()

        if clean_df.empty:
            print(f"⚠️ No valid trades in {filename}")
            continue

        # Extract rune count and name
        extracted = clean_df['price_summary'].str.extract(pattern)
        clean_df['price_count'] = extracted[0].astype(int)
        clean_df['price_rune'] = extracted[1]

        # Save cleaned file
        out_path = os.path.join(cleaned_dir, filename)
        clean_df.to_csv(out_path, index=False)
        print(f"✅ Cleaned {filename}: {len(clean_df)} rows → {out_path}")

print("\n🎉 All folders cleaned successfully.")