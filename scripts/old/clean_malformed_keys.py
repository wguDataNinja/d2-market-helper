# /Users/buddy/Desktop/traderie/scripts/clean_malformed_keys.py

import json
from pathlib import Path

FILES = [
    "/Users/buddy/Desktop/traderie/data/completed_pc_hc_l.json",
    "/Users/buddy/Desktop/traderie/data/completed_pc_hc_nl.json",
    "/Users/buddy/Desktop/traderie/data/completed_pc_sc_l.json",
    "/Users/buddy/Desktop/traderie/data/completed_pc_sc_nl.json",
]

def clean_file(path):
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned = {k: v for k, v in data.items() if ':' in k}
    removed = len(data) - len(cleaned)

    if removed:
        print(f"🧹 {path.name}: removed {removed} malformed keys")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2)
    else:
        print(f"✅ {path.name}: no malformed keys found")

def main():
    for f in FILES:
        clean_file(f)

if __name__ == "__main__":
    main()