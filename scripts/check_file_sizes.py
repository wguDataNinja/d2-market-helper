# count_trades_in_files.py

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"

files = [
    str(RAW_DIR / "raw_trades_pc_hc_l.json"),
    str(RAW_DIR / "raw_trades_pc_sc_nl.json"),
    str(RAW_DIR / "raw_trades_pc_sc_l.json"),
    str(RAW_DIR / "raw_trades_pc_hc_nl.json"),
]

for file in files:
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            count = 0
            for category in data.values():
                for trades in category.values():
                    count += len(trades)
            print(f"{file}: {count} trades")
    except Exception as e:
        print(f"{file}: Error - {e}")