import json
from pathlib import Path

INPUT = Path("/Users/buddy/Desktop/traderie/data/completed_pc_hc_l.json")

def find_reversed_pairs(trades):
    pairs = set(trades.keys())
    return [(p, f"{b}:{a}") for p in pairs
            for a, b in [p.split(":",1)]
            if f"{b}:{a}" in pairs]

if __name__ == "__main__":
    data = json.loads(INPUT.read_text())
    rev = find_reversed_pairs(data)
    if rev:
        print("Reversed-direction entries found:")
        for p,q in rev:
            print(f"  {p}  ↔  {q}")
    else:
        print("No reversed-direction entries.")