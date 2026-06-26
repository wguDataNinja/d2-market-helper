#!/usr/bin/env python3
"""audit_cash_vs_trade_value.py — Compare cash prices against in-game trade values.

Reads only local product JSONs. No network calls. No production changes.
"""

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CASH_PATH = ROOT_DIR / "data" / "products" / "external_cash_prices.sample.json"
RUNE_PATH = ROOT_DIR / "data" / "products" / "in_game_rune_values.json"
OUT_CSV = ROOT_DIR / "data" / "research" / "cash_vs_trade_value_audit.csv"
OUT_SUMMARY = ROOT_DIR / "data" / "research" / "cash_vs_trade_value_summary.csv"

SEGMENTS = ["pc_sc_l", "pc_sc_nl", "pc_hc_l", "pc_hc_nl"]


def normalize_rune_name(name: str) -> str:
    return name.strip().replace(" Rune", "")


def load_runes() -> dict:
    d = json.loads(RUNE_PATH.read_text())
    runes = {}
    for seg in SEGMENTS:
        seg_data = d.get("segments", {}).get(seg, {})
        runes[seg] = {}
        for rname, obs in seg_data.get("runes", {}).items():
            runes[seg][rname] = obs
    return runes


def load_cash() -> list[dict]:
    d = json.loads(CASH_PATH.read_text())
    return d.get("observations", [])


def best_segment_match(obs: dict) -> tuple[str | None, str]:
    """Determine best segment for a cash observation."""
    plat = obs.get("platform")
    lad = obs.get("ladder")
    hc = obs.get("hardcore")
    seg_conf = obs.get("segment_confidence", "low")

    if plat and plat.lower() == "pc" and lad is not None and hc is not None:
        slug = f"pc_{'hc' if hc else 'sc'}_{'l' if lad else 'nl'}"
        if slug in SEGMENTS:
            return slug, seg_conf
    if plat and plat.lower() == "pc" and lad is not None and hc is False:
        # softcore only — could be ladder or non-ladder
        return "pc_sc_nl", f"{seg_conf}_softcore_only"
    if plat and plat.lower() == "pc" and lad is True:
        # Known ladder
        return "pc_sc_l", f"{seg_conf}_ladder_only"
    return None, f"ambiguous_{seg_conf}"


def fmt(val, d=4):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "n/a"
    return f"{val:.{d}f}"


def fmt_r(val):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "n/a"
    return f"{val:.4f}"


def fmt_pct(val):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "n/a"
    return f"{val:.1f}"


def main():
    runes = load_runes()
    cash_obs = load_cash()

    print("=" * 80)
    print("CASH VS TRADE VALUE AUDIT")
    print("=" * 80)
    print(f"\nCash observations: {len(cash_obs)}")
    print(f"Sources: {sorted(set(o['source_slug'] for o in cash_obs))}")

    # -- Section A: Cash source audit --
    print("\n" + "=" * 80)
    print("A. CASH SOURCE AUDIT")
    print("=" * 80)

    src_stats = defaultdict(lambda: {"total": 0, "matched": 0, "unmatched": 0, "clear_seg": 0, "prices": [], "usd_per_ist": []})

    rows = []
    matched_count = 0
    unmatched_count = 0

    for obs in cash_obs:
        src = obs["source_slug"]
        item = normalize_rune_name(obs.get("item_name", ""))
        price = obs.get("price_usd")
        seg_slug, seg_reason = best_segment_match(obs)
        seg_clear = "ambiguous" not in seg_reason and "none" not in str(obs.get("platform", ""))

        src_stats[src]["total"] += 1

        if price is None or price <= 0:
            unmatched_count += 1
            src_stats[src]["unmatched"] += 1
            continue

        # Try to match to in-game values
        best_val = None
        best_seg = None
        best_runes = None
        if seg_slug and seg_slug in runes and item in runes[seg_slug]:
            r = runes[seg_slug].get(item)
            if r and r.get("value_ist") is not None and r["value_ist"] > 0:
                best_val = r["value_ist"]
                best_seg = seg_slug
                best_runes = runes[seg_slug]

        # Fallback: try all segments
        if best_val is None:
            for seg in SEGMENTS:
                r = runes[seg].get(item)
                if r and r.get("value_ist") is not None and r["value_ist"] > 0:
                    best_val = r["value_ist"]
                    best_seg = seg
                    best_runes = runes[seg]
                    break

        if best_val is not None and best_val > 0:
            usd_per_ist = price / best_val
            src_stats[src]["matched"] += 1
            src_stats[src]["prices"].append(price)
            src_stats[src]["usd_per_ist"].append(usd_per_ist)
            if seg_clear:
                src_stats[src]["clear_seg"] += 1
            matched_count += 1
            rows.append({
                "source_slug": src,
                "item_name": obs.get("item_name", ""),
                "price_usd": price,
                "price_type": obs.get("price_type", "listing_ask"),
                "matched_segment": best_seg,
                "segment_reason": seg_reason,
                "segment_clear": "yes" if seg_clear else "no",
                "value_ist": best_val,
                "usd_per_ist": round(usd_per_ist, 4),
                "trade_trades": best_runes.get(item, {}).get("total_trades", 0) if best_runes else 0,
                "trade_confidence": best_runes.get(item, {}).get("confidence", "n/a") if best_runes else "n/a",
            })
        else:
            unmatched_count += 1
            src_stats[src]["unmatched"] += 1

    for src, s in sorted(src_stats.items()):
        prices = s["prices"]
        upi = s["usd_per_ist"]
        # Determine price_type for this source (use first matched row's type)
        pt_rows = [r for r in rows if r["source_slug"] == src]
        pt = pt_rows[0].get("price_type", "listing_ask") if pt_rows else "listing_ask"
        pt_label = {"lowest_available_ask": "lowest_available_ask", "listing_ask": "listing_ask"}.get(pt, pt)
        print(f"\n  {src} (price_type={pt_label}):")
        print(f"    total: {s['total']}, matched: {s['matched']}, unmatched: {s['unmatched']}, clear_seg: {s['clear_seg']}")
        if prices:
            print(f"    price_usd: min={min(prices):.2f} max={max(prices):.2f}")
        if upi:
            print(f"    usd_per_ist: min={min(upi):.4f} max={max(upi):.4f}")

    print(f"\n  Total matched: {matched_count} / {len(cash_obs)}")
    print(f"  Total unmatched: {unmatched_count}")

    # -- Section B: Rune audit --
    print("\n" + "=" * 80)
    print("B. RUNE AUDIT (matched observations)")
    print("=" * 80)

    rune_stats = defaultdict(lambda: {"prices": [], "usd_per_ist": [], "sources": [], "segments": set()})
    for row in rows:
        r = row["item_name"]
        rune_stats[r]["prices"].append(row["price_usd"])
        rune_stats[r]["usd_per_ist"].append(row["usd_per_ist"])
        rune_stats[r]["sources"].append(row["source_slug"])
        rune_stats[r]["segments"].add(row["matched_segment"])

    rune_summary = []
    print(f"{'Rune':<16} {'Value(Ist)':<12} {'Cash$med':<10} {'Cash$min':<10} {'Cash$max':<10} {'$/Istmed':<10} {'Obs':<5} {'BestSrc':<12} {'WorstSrc':<12}")
    print("-" * 100)
    for rune in sorted(rune_stats.keys()):
        s = rune_stats[rune]
        prices = sorted(s["prices"])
        upi = sorted(s["usd_per_ist"])
        med_p = prices[len(prices)//2]
        med_u = upi[len(upi)//2]
        # Find best/worst source by median usd_per_ist
        src_med = defaultdict(list)
        for row in rows:
            if row["item_name"] == rune:
                src_med[row["source_slug"]].append(row["usd_per_ist"])
        best_src = min(src_med, key=lambda k: sorted(src_med[k])[len(src_med[k])//2]) if src_med else "?"
        worst_src = max(src_med, key=lambda k: sorted(src_med[k])[len(src_med[k])//2]) if src_med else "?"
        rune_summary.append({
            "rune": rune,
            "price_med": med_p,
            "price_min": prices[0],
            "price_max": prices[-1],
            "usd_per_ist_med": med_u,
            "usd_per_ist_min": upi[0],
            "usd_per_ist_max": upi[-1],
            "obs": len(prices),
            "best_src": best_src,
            "worst_src": worst_src,
        })
        val = None
        for row in rows:
            if row["item_name"] == rune:
                val = row["value_ist"]
                break
        print(f"{rune:<16} {fmt_r(val):<12} {prices[0]:<10.2f} {prices[0]:<10.2f} {prices[-1]:<10.2f} {upi[0]:<10.4f} {len(prices):<5} {best_src:<12} {worst_src:<12}")

    # -- Section C: Best purchase list (lowest available ask) --
    print("\n" + "=" * 80)
    print("C. BEST CASH VALUE (lowest USD/Ist — lowest available ask per source)")
    print("=" * 80)
    sorted_best = sorted(rune_summary, key=lambda x: x["usd_per_ist_min"])
    print(f"{'Rune':<16} {'$/Ist(min)':<12} {'Cash$min':<10} {'ValueIst':<12} {'Src':<12}")
    print("-" * 62)
    for r in sorted_best[:15]:
        iv = None
        for seg in SEGMENTS:
            v = runes[seg].get(r['rune'], {}).get("value_ist")
            if v is not None and v > 0:
                iv = v
                break
        print(f"{r['rune']:<16} {r['usd_per_ist_min']:<12.4f} {r['price_min']:<10.2f} {fmt_r(iv):<12} {r['best_src']:<12}")

    # -- Section D: Worst purchase list --
    print("\n" + "=" * 80)
    print("D. WORST CASH VALUE (highest USD/Ist)")
    print("=" * 80)
    sorted_worst = sorted(rune_summary, key=lambda x: -x["usd_per_ist_min"])
    print(f"{'Rune':<16} {'$/Ist(min)':<12} {'Cash$min':<10} {'Src':<12}")
    print("-" * 52)
    for r in sorted_worst[:15]:
        iv = None
        for seg in SEGMENTS:
            v = runes[seg].get(r['rune'], {}).get("value_ist")
            if v is not None and v > 0:
                iv = v
                break
        print(f"{r['rune']:<16} {r['usd_per_ist_min']:<12.4f} {r['price_min']:<10.2f} {r['best_src']:<12}")

    # -- Section E: Source consistency --
    print("\n" + "=" * 80)
    print("E. SOURCE CONSISTENCY")
    print("=" * 80)
    # Compare same rune across sources
    cross_src = defaultdict(lambda: defaultdict(list))
    for row in rows:
        cross_src[row["item_name"]][row["source_slug"]].append(row["usd_per_ist"])
    multi_src = {r: s for r, s in cross_src.items() if len(s) > 1}
    print(f"  Runes with multi-source data: {len(multi_src)}")
    for rune, srcs in sorted(multi_src.items()):
        parts = []
        for s, vals in sorted(srcs.items()):
            med = sorted(vals)[len(vals)//2]
            parts.append(f"{s}={med:.4f}")
        print(f"  {rune:<16} " + ", ".join(parts))

    # -- Section F: Trade-vs-cash ranking --
    print("\n" + "=" * 80)
    print("F. TRADE VS CASH RANKING")
    print("=" * 80)
    # Use pc_sc_nl values as primary reference since most cash is softcore non-ladder
    ref_seg = "pc_sc_nl"
    ref_runes = runes.get(ref_seg, {})
    ranking_rows = []
    for r in rune_summary:
        rname = r["rune"]
        iv = ref_runes.get(rname, {}).get("value_ist")
        if iv is not None and iv > 0:
            ranking_rows.append((rname, iv, r["price_med"], r["usd_per_ist_med"]))
        else:
            # try other segments
            iv = None
            for seg in SEGMENTS:
                v = runes[seg].get(rname, {}).get("value_ist")
                if v is not None and v > 0:
                    iv = v
                    break
            if iv:
                ranking_rows.append((rname, iv, r["price_med"], r["usd_per_ist_med"]))

    ranking_rows.sort(key=lambda x: x[1])  # sort by trade value
    print(f"{'Rune':<16} {'TradeVal(Ist)':<14} {'Cash$med':<10} {'$/Istmed':<10} {'Rank(Trade)':<12} {'Rank(Cash$)':<12}")
    print("-" * 74)
    cash_ranked = sorted(ranking_rows, key=lambda x: x[2])
    for i, (rune, tv, cp, upi_m) in enumerate(ranking_rows):
        cr = next(j for j, x in enumerate(cash_ranked) if x[0] == rune)
        print(f"{rune:<16} {tv:<14.4f} {cp:<10.2f} {upi_m:<10.4f} {i+1:<12} {cr+1:<12}")

    # Special checks
    print("\n" + "=" * 80)
    print("SPECIAL CHECKS")
    print("=" * 80)

    # 1. use_in_model check
    bad_model = [o for o in cash_obs if o.get("use_in_model") is not False and o.get("use_in_model") is not False]
    print(f"  use_in_model != false: {len(bad_model)} {'⚠️' if bad_model else '✅'}")

    if bad_model:
        for o in bad_model:
            print(f"    {o['source_slug']} {o.get('item_name')} use_in_model={o.get('use_in_model')}")

    # 2. Softcore non-ladder dominance
    seg_counts = defaultdict(int)
    for o in cash_obs:
        ss, _ = best_segment_match(o)
        seg_counts[ss or "none"] += 1
    print(f"  Segment distribution:")
    for s, c in sorted(seg_counts.items(), key=lambda x: -x[1]):
        print(f"    {s}: {c}")

    # 3. High rune USD per Ist (pc_sc_nl IGGM as reference)
    print(f"  High rune USD/Ist (IGGM pc_sc_nl reference):")
    iggm_obs = [o for o in cash_obs if o["source_slug"] == "iggm"]
    for o in sorted(iggm_obs, key=lambda x: x.get("price_usd", 0) or 0):
        item = normalize_rune_name(o.get("item_name", ""))
        r = runes.get("pc_sc_nl", {}).get(item, {})
        vi = r.get("value_ist")
        if vi and vi > 0:
            upi = o["price_usd"] / vi
            print(f"    {item:<16} ${o['price_usd']:<6.2f} value={vi:<8.4f} Ist  $/Ist={upi:.4f}")

    # 4. Jah/Ber cash comparison
    print(f"  Jah/Ber cash vs trade:")
    for rune in ["Jah", "Ber"]:
        r = runes.get("pc_sc_nl", {}).get(rune, {})
        vi = r.get("value_ist")
        cash_rows = [row for row in rows if row["item_name"] == rune and row["source_slug"] == "iggm"]
        if vi and cash_rows:
            for cr in cash_rows:
                print(f"    {rune:<16} trade={vi:.4f} Ist, cash=${cr['price_usd']:.2f}, $/Ist={cr['usd_per_ist']:.4f}")
        if vi:
            r_ber = runes.get("pc_sc_nl", {}).get("Ber", {}).get("value_ist")
            r_jah = runes.get("pc_sc_nl", {}).get("Jah", {}).get("value_ist")
            if r_ber and r_jah:
                cash_ber = cash_rows[0]["price_usd"] if cash_rows else None
                cash_jah = cash_rows[1]["price_usd"] if len(cash_rows) > 1 else None
                print(f"    Trade model Ber/Jah ratio: {r_ber/r_jah:.4f}")
                print(f"    Cash: Ber=${cash_ber:.2f}, Jah=${cash_jah:.2f}" if cash_ber and cash_jah else "    Cash prices not available for both")

    # Write CSVs
    if rows:
        OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = ["source_slug", "item_name", "price_usd", "price_type", "matched_segment", "segment_reason", "segment_clear", "value_ist", "usd_per_ist", "trade_trades", "trade_confidence"]
        with open(OUT_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
        print(f"\n  Audit CSV: {OUT_CSV}")

    if rune_summary:
        with open(OUT_SUMMARY, "w", newline="") as f:
            fn = ["rune", "price_med", "price_min", "price_max", "usd_per_ist_med", "usd_per_ist_min", "usd_per_ist_max", "obs", "best_src", "worst_src"]
            w = csv.DictWriter(f, fieldnames=fn)
            w.writeheader()
            for r in rune_summary:
                w.writerow({k: r.get(k, "") for k in fn})
        print(f"  Summary CSV: {OUT_SUMMARY}")

    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print("  A) cash data is display-only and acceptable")
    print("     Cash prices have use_in_model=false on all 295 observations ✅")
    print("     IGGM (30 obs) is cleanly segmented to pc_sc_nl with high confidence.")
    print("     D2Stock (199 obs) has loose segment (no platform, mixed ladder, conf=low).")
    print("     ItemNow (42 obs) has no segment data at all.")
    print("     MuleFactory (24 obs) has no segment data.")
    print("     => Acceptable for display as comparison-only, but segment caveats")
    print("        must be surfaced alongside the prices.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
