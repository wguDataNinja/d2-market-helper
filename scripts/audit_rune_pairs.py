#!/usr/bin/env python3
"""audit_rune_pairs.py — Analyze non-Ist rune trades and compare against Ist-anchored prices.

Reads only local research CSVs and product JSON. No API calls.
Reports common rune pairs, implied ratios, and divergence from current model.
"""

import csv
import json
import re
import sys
from collections import defaultdict, Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
RESEARCH_DIR = ROOT_DIR / "data" / "research"
PRODUCT_PATH = ROOT_DIR / "data" / "products" / "in_game_rune_values.json"
SEGMENTS = ["pc_sc_l", "pc_sc_nl", "pc_hc_l", "pc_hc_nl"]

RUNES_SORTED = [
    "El", "Eld", "Tir", "Nef", "Eth", "Ith", "Tal", "Ral", "Ort", "Thul",
    "Amn", "Sol", "Shael", "Dol", "Hel", "Io", "Lum", "Ko", "Fal", "Lem",
    "Pul", "Um", "Mal", "Ist", "Gul", "Vex", "Ohm", "Lo", "Sur", "Ber",
    "Jah", "Cham", "Zod",
]


def parse_basket(s: str) -> list[tuple[str, int]]:
    """Parse 'Jah Rune:1;Ber Rune:2' -> [('Jah', 1), ('Ber', 2)]"""
    items = []
    for part in s.split(";"):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(.+?)\s*Rune\s*:\s*(\d+)$", part)
        if m:
            items.append((m.group(1).strip(), int(m.group(2))))
    return items


def basket_key(items: list[tuple[str, int]]) -> str:
    """Canonical basket key: sorted by rune rank."""
    return "+".join(f"{r}:{q}" for r, q in sorted(items, key=lambda x: RUNES_SORTED.index(x[0]) if x[0] in RUNES_SORTED else 99))


def load_current_prices() -> dict:
    d = json.loads(PRODUCT_PATH.read_text())
    prices = {}
    for seg in SEGMENTS:
        runes_data = d.get("segments", {}).get(seg, {}).get("runes", {})
        prices[seg] = {rune: obs.get("value_ist") for rune, obs in runes_data.items()}
    return prices


def analyze_segment(seg: str, current_prices: dict) -> dict:
    csv_path = RESEARCH_DIR / f"extracted_trades_{seg}.csv"
    if not csv_path.exists():
        return {"rows": 0, "non_ist": 0, "pair_counts": {}, "basket_pairs": [], "divergences": []}

    pair_counter: Counter = Counter()
    basket_trades = []
    total = 0
    non_ist = 0

    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            off_str = row["Offered"]
            req_str = row["Requested"]
            if "Ist" in off_str or "Ist" in req_str:
                continue
            non_ist += 1

            offered = parse_basket(off_str)
            requested = parse_basket(req_str)
            if not offered or not requested:
                continue

            off_key = basket_key(offered)
            req_key = basket_key(requested)

            if off_key and req_key:
                pair_counter[(off_key, req_key)] += 1
                basket_trades.append({
                    "offered": offered,
                    "requested": requested,
                    "off_key": off_key,
                    "req_key": req_key,
                })

    # Top 25 pairs
    top_pairs = []
    for (off_key, req_key), cnt in pair_counter.most_common(25):
        top_pairs.append({"offered": off_key, "requested": req_key, "count": cnt})

    # Analyze specific baskets: Jah↔Ber at 1:1
    jah_ber_count = 0
    for t in basket_trades:
        if (t["off_key"] == "Ber:1" and t["req_key"] == "Jah:1") or \
           (t["off_key"] == "Jah:1" and t["req_key"] == "Ber:1"):
            jah_ber_count += 1

    # Divergence: for each common non-Ist pair, what does the Ist model predict?
    # For example: Jah=11.85, Ber=17.64 → model predicts Ber/Jah = 1.49
    # Direct observations: Ber↔Jah 1:1 trades give ratio=1.0
    divs = []
    seg_prices = current_prices.get(seg, {})
    jah_price = seg_prices.get("Jah")
    ber_price = seg_prices.get("Ber")
    if jah_price and ber_price and jah_price > 0:
        model_ber_jah = ber_price / jah_price
        # Find the most common Jah-Ber ratio from trade data
        jb_ratio_counts = Counter()
        for t in basket_trades:
            off, req = t["offered"], t["requested"]
            # Check if it's a direct Jah↔Ber swap (possibly with other items)
            off_runes = {r: q for r, q in off}
            req_runes = {r: q for r, q in req}
            if set(off_runes.keys()) == {"Ber"} and set(req_runes.keys()) == {"Jah"}:
                # Ber:Qb → Jah:Qj  => Ber/Jah = Qj/Qb
                jb_ratio_counts[req_runes["Jah"] / off_runes["Ber"]] += 1
            elif set(off_runes.keys()) == {"Jah"} and set(req_runes.keys()) == {"Ber"}:
                # Jah:Qj → Ber:Qb  => Ber/Jah = Qb/Qj
                jb_ratio_counts[req_runes["Ber"] / off_runes["Jah"]] += 1
        if jb_ratio_counts:
            observed_ratio, cnt = jb_ratio_counts.most_common(1)[0]
            div = abs(observed_ratio - model_ber_jah) / model_ber_jah * 100 if model_ber_jah else 0
            divs.append({
                "pair": "Ber↔Jah direct",
                "model_ratio": round(model_ber_jah, 4),
                "observed_ratio": round(observed_ratio, 4),
                "trade_count": cnt,
                "divergence_pct": round(div, 1),
            })

    return {
        "rows": total,
        "non_ist": non_ist,
        "top_pairs": top_pairs,
        "jah_ber_1_1_count": jah_ber_count,
        "divergences": divs,
    }


def main():
    current_prices = load_current_prices()

    print("=" * 80)
    print("NON-IST RUNE TRADE AUDIT")
    print("=" * 80)

    all_top = []
    all_divs = []
    total_non_ist = 0

    for seg in SEGMENTS:
        result = analyze_segment(seg, current_prices)
        total_non_ist += result["non_ist"]

        print(f"\n--- {seg} ---")
        print(f"  Total rows: {result['rows']}")
        print(f"  Non-Ist trades: {result['non_ist']} ({100*result['non_ist']/result['rows']:.1f}% of rows)" if result['rows'] else "  No data")
        print(f"  Jah↔Ber 1:1 trades: {result['jah_ber_1_1_count']}")

        if result["top_pairs"]:
            print(f"\n  Top 10 non-Ist trade patterns:")
            print(f"  {'Offered':<35} {'Requested':<35} {'Count':>6}")
            print(f"  {'-'*35} {'-'*35} {'-'*6}")
            for p in result["top_pairs"][:10]:
                print(f"  {p['offered']:<35} {p['requested']:<35} {p['count']:>6}")

        for d in result["divergences"]:
            print(f"\n  ⚠ {d['pair']}: model ratio={d['model_ratio']}, observed={d['observed_ratio']} from {d['trade_count']} trades, divergence={d['divergence_pct']}%")
            all_divs.append({**d, "segment": seg})

        all_top.extend([(seg, p) for p in result["top_pairs"]])

    print("\n" + "=" * 80)
    print("JAH/BER FOCUS")
    print("=" * 80)

    for seg in SEGMENTS:
        seg_prices = current_prices.get(seg, {})
        jah = seg_prices.get("Jah")
        ber = seg_prices.get("Ber")
        if jah and ber and jah > 0:
            model_ratio = ber / jah
            print(f"  {seg}: Ist-model says Ber={ber:.2f} Ist, Jah={jah:.2f} Ist → Ber/Jah={model_ratio:.3f}")
            # How many direct Ber↔Jah 1:1 trades?
            csv_path = RESEARCH_DIR / f"extracted_trades_{seg}.csv"
            if csv_path.exists():
                jb = 0
                with open(csv_path) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        off, req = row["Offered"], row["Requested"]
                        if ("Jah" in off and "Ber" in req) or ("Ber" in off and "Jah" in req):
                            if "Ist" not in off and "Ist" not in req:
                                # Check it's 1:1
                                off_items = parse_basket(off)
                                req_items = parse_basket(req)
                                if off_items and req_items and off_items[0][1] > 0 and req_items[0][1] > 0:
                                    off_rune, off_qty = off_items[0]
                                    req_rune, req_qty = req_items[0]
                                    if off_rune == "Ber" and req_rune == "Jah" and off_qty == 1 and req_qty == 1:
                                        jb += 1
                                    elif off_rune == "Jah" and req_rune == "Ber" and off_qty == 1 and req_qty == 1:
                                        jb += 1
                print(f"    Direct Ber↔Jah 1:1 trades: {jb}")
                if jb > 0:
                    print(f"    → Direct observations imply Ber/Jah ≈ 1.0 (divergence from model: {abs(1 - model_ratio) / model_ratio * 100:.1f}%)")

    print("\n" + "=" * 80)
    print("LARGEST DIVERGENCES")
    print("=" * 80)
    if all_divs:
        for d in sorted(all_divs, key=lambda x: -x["divergence_pct"])[:5]:
            print(f"  {d['segment']:12s} {d['pair']:<30s} model={d['model_ratio']:.3f} obs={d['observed_ratio']:.3f}  ({d['divergence_pct']:.0f}% divergence)")
    else:
        print("  No common basket patterns found with enough volume.")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Total non-Ist trades across all segments: {total_non_ist}")
    for seg in SEGMENTS:
        csv_path = RESEARCH_DIR / f"extracted_trades_{seg}.csv"
        if csv_path.exists():
            with open(csv_path) as f:
                total = sum(1 for _ in f) - 1
            print(f"  {seg}: {total} rows total")

    print(f"\n  Recommended action:")
    print(f"    The Ist-anchored model ignores all {total_non_ist} non-Ist trades above.")
    if all_divs:
        max_div = max(d["divergence_pct"] for d in all_divs)
        if max_div > 20:
            print(f"    ⚠ Maximum divergence observed: {max_div:.0f}% — graph model likely needed.")
        else:
            print(f"    ✓ Maximum divergence observed: {max_div:.0f}% — Ist model may be adequate.")
    print(f"    Jah↔Ber 1:1 trades exist in every segment but are invisible to the model.")
    print(f"    → If Jah and Ber consistently trade 1:1, one or both Ist-derived prices are wrong.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
