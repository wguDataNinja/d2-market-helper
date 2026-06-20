# inspect_raw_trades.py

import json, statistics
from pathlib import Path
from collections import Counter, defaultdict
from tabulate import tabulate

# Base dir
BASE = Path(__file__).resolve().parent.parent
RAW_DIR = BASE / 'data' / 'raw'
SEGMENTS = ['pc_sc_l','pc_sc_nl','pc_hc_l','pc_hc_nl']


def inspect_segment(segment):
    path = RAW_DIR / f'raw_trades_{segment}.json'
    data = json.load(path.open())
    runes = data.get('Runes', {})

    total = 0
    lengths = Counter()
    direct = defaultdict(list)

    for offer, listings in runes.items():
        for t in listings:
            total += 1
            p = t.get('price') or []
            lengths[len(p)] += 1
            if len(p) == 1:
                ask = p[0]
                if ask['name'] in runes and ask['name'] != offer and t.get('quantity',0) > 0 and ask.get('quantity',0) > 0:
                    direct[(offer, ask['name'])].append(t['quantity']/ask['quantity'])

    # Summary of direct pairs
    stats = []
    for (o,a), ratios in direct.items():
        cnt = len(ratios)
        mean = statistics.mean(ratios)
        stats.append((cnt, o, a, mean))
    stats.sort(reverse=True)

    return total, lengths, stats


def main():
    for seg in SEGMENTS:
        try:
            total, lengths, stats = inspect_segment(seg)
            single = lengths.get(1, 0)
            multi = total - single

            print(f"\nSEGMENT {seg.upper()}")
            print(f"Total trades: {total}")
            print(tabulate(
                [[single, f"{single/total*100:.1f}%", multi, f"{multi/total*100:.1f}%"]],
                headers=['1-item','%','multi','%'], tablefmt='plain'
            ))

            print("\nTop Direct Pairs:")
            top = stats[:5]
            rows = [[f"{o}->{a}", cnt, f"{mean:.2f}"] for cnt,o,a,mean in top]
            print(tabulate(rows, headers=['Pair','Count','Avg ratio'], tablefmt='plain'))
        except Exception as e:
            print(f"\n{seg.upper()} ERROR: {e}")

if __name__ == '__main__':
    main()
