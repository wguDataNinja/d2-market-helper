# /Users/buddy/Desktop/traderie/scripts/deep_integrity_check.py

import json
from pathlib import Path

FILES = [
    "/Users/buddy/Desktop/traderie/data/completed_trades_pc_hc_l.json",
    "/Users/buddy/Desktop/traderie/data/completed_trades_pc_hc_nl.json",
    "/Users/buddy/Desktop/traderie/data/completed_trades_PC_SC_L.json",
    "/Users/buddy/Desktop/traderie/data/completed_trades_PC_SC_NL.json",
]

def is_valid_ratio_string(ratio):
    try:
        a, b = map(int, ratio.split(":"))
        return b > 0
    except Exception:
        return False

def check_entry(key, entry):
    problems = []

    if ':' not in key:
        problems.append("Malformed key (missing ':')")

    meta = entry.get("metadata", {})
    if not isinstance(meta, dict):
        problems.append("Missing or invalid 'metadata'")

    ratios = entry.get("ratios", {})
    if not isinstance(ratios, dict) or not ratios:
        problems.append("Missing or empty 'ratios'")

    recommended = meta.get("recommended_ratio")
    numeric = meta.get("numeric_ratios", {})

    if not recommended or recommended not in numeric:
        problems.append(f"'recommended_ratio' ({recommended}) not in 'numeric_ratios'")

    for ratio_str in numeric:
        if not is_valid_ratio_string(ratio_str):
            problems.append(f"Invalid ratio format: {ratio_str}")

    return problems

def scan_file(path):
    path = Path(path)
    print(f"\n📂 Checking {path.name}")
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        print(f"❌ Could not parse {path.name}: {e}")
        return

    total = len(data)
    bad = 0

    for k, v in data.items():
        issues = check_entry(k, v)
        if issues:
            print(f"  ⚠️ {k}")
            for msg in issues:
                print(f"     - {msg}")
            bad += 1

    print(f"✅ Checked {total} entries, found {bad} with problems.")

def main():
    for f in FILES:
        scan_file(f)

if __name__ == "__main__":
    main()