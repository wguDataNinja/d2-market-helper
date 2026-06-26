#!/usr/bin/env python3
"""
generate_prices_json.py — Produce in_game_rune_values.json and traderie_tools_prices.json
from per-segment price CSVs.

Inputs: data/prices/rune_prices_{segment}.csv (4 files)
Outputs:
  data/products/in_game_rune_values.json
  data/products/traderie_tools_prices.json
"""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PRICES_DIR = ROOT_DIR / "data" / "prices"
OUTPUT_DIR = ROOT_DIR / "data" / "products"

SEGMENTS_ORDERED = ["pc_sc_l", "pc_sc_nl", "pc_hc_l", "pc_hc_nl"]

SEGMENT_META = {
    "pc_sc_l": {"platform": "pc", "mode": "softcore", "ladder": True, "hardcore": False},
    "pc_sc_nl": {"platform": "pc", "mode": "softcore", "ladder": False, "hardcore": False},
    "pc_hc_l": {"platform": "pc", "mode": "hardcore", "ladder": True, "hardcore": True},
    "pc_hc_nl": {"platform": "pc", "mode": "hardcore", "ladder": False, "hardcore": True},
}

CAVEATS = [
    "Traderie API behavior is unofficial and may be incomplete.",
    "Segment prices are not merged. Never merge segments.",
    "Current model uses Ist-pair completed listings and includes approved AND-trade handling.",
    "AND trades are included only through the approved proportional decomposition rule (capped at 2-item requests, flagged for audit).",
    "Non-Ist rune pairs are excluded. Only Ist-paired trades are used.",
    "Thin-volume runes may have low confidence and should be used with caution.",
    "Cash-market prices are external comparison only and are not included in this file.",
    "Reddit/community data is qualitative only and is not included in this file.",
    "Active listings are not completed trades and are not included.",
    "Prices are relative in-game trade values (Ist-normalized), not absolute cash values.",
    "Game version / ruleset (Classic, Lord of Destruction, Reign of the Warlock) is tracked but not split in pricing. ROTW dominates observed volume.",
    "Region (Americas, Europe, Asia) is visible in the Traderie website UI but unavailable in completed-trades API data.",
]

RULESET_CAVEAT = (
    "Prices aggregate all game versions/rulesets (Classic, Lord of Destruction, "
    "Reign of the Warlock). As of the latest audit, ROTW constitutes >95% of "
    "observed completed trades. LoD and Classic listings are included in the "
    "model but have insufficient volume for separate pricing. Region data is "
    "not available in the completed-trades API and is not included."
)


def rune_name_to_display(raw: str) -> str:
    """Convert 'Jah' to 'Jah Rune' format expected by userscript."""
    return raw.strip() + " Rune" if not raw.endswith(" Rune") else raw


def rune_name_to_short(raw: str) -> str:
    """Convert 'Jah Rune' to 'Jah'."""
    return raw.replace(" Rune", "")


def load_segment_csv(segment: str) -> list[dict]:
    path = PRICES_DIR / f"rune_prices_{segment}.csv"
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def confidence_from(total_trades: int) -> tuple[str, str]:
    if total_trades <= 0:
        return ("unavailable", "No trades available for this rune in this segment")
    if total_trades >= 50:
        return ("high", f"Based on {total_trades} trades — sufficient volume for stable VWAP")
    if total_trades >= 15:
        return ("medium", f"Based on {total_trades} trades — moderate volume")
    return ("low", f"Based on {total_trades} trades — thin volume")


SNAPSHOTS_DIR = ROOT_DIR / "data" / "snapshots" / "raw" / "traderie"


def count_rulesets_in_snapshots(segment: str) -> dict:
    """Scan raw API snapshots for Game version / ruleset distribution.

    Reads locally stored snapshot response.json files. No network calls.
    Returns dict with counts per ruleset, total, dominant_ruleset, share.
    """
    ruleset_map_raw = {
        "classic": "classic",
        "lord of destruction": "lod",
        "reign of the warlock": "rotw",
    }
    counts = {}
    seg_dir = SNAPSHOTS_DIR / segment
    if not seg_dir.exists():
        return {"counts": {}, "total": 0, "dominant_ruleset": None, "dominant_share": 0.0}

    for run_dir in sorted(seg_dir.iterdir()):
        resp_path = run_dir / "response.json"
        if not resp_path.exists():
            continue
        try:
            raw = json.loads(resp_path.read_text(errors="replace"))
        except Exception:
            continue
        for listing in raw.get("listings", []):
            gv = "unknown"
            for prop in (listing.get("properties") or []):
                if prop.get("property") == "Game version":
                    gv = (prop.get("string") or "").strip().lower()
                    break
            # Handle comma-separated multi-value
            parts = [p.strip() for p in gv.split(",")] if gv not in ("unknown", "") else ["unknown"]
            for p in parts:
                rs = ruleset_map_raw.get(p, "unknown")
                counts[rs] = counts.get(rs, 0) + 1

    total = sum(counts.values()) if counts else 0
    dominant = max(counts, key=counts.get) if counts else None
    dominant_share = round(counts[dominant] / total, 3) if dominant and total else 0.0
    return {
        "counts": dict(sorted(counts.items())),
        "total_observed_raw_listings": total,
        "dominant_ruleset": dominant,
        "dominant_ruleset_share": dominant_share,
    }


def generate():
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    segments_out = {}
    compat_segments = {}
    total_trades_all = 0
    total_runes_all = 0
    high_c = medium_c = low_c = unav_c = 0

    for seg in SEGMENTS_ORDERED:
        rows = load_segment_csv(seg)
        meta = SEGMENT_META[seg]
        runes_out = {}
        compat_runes = {}
        seg_trades = 0

        for row in rows:
            rune_raw = row["Rune"]
            display_name = rune_raw + " Rune"
            try:
                bid_price = float(row["Bid_Price"]) if row["Bid_Price"] else None
                ask_price = float(row["Ask_Price"]) if row["Ask_Price"] else None
                bid_count = int(row["Bid_Count"])
                ask_count = int(row["Ask_Count"])
                blended = float(row["Blended_FMV"]) if row["Blended_FMV"] else None
                total = int(row["Total_Trades"])
            except (ValueError, KeyError):
                continue

            confidence, reason = confidence_from(total)
            seg_trades += total

            runes_out[rune_raw] = {
                "rune": rune_raw,
                "value_ist": round(blended, 4) if blended is not None else None,
                "bid_price": round(bid_price, 4) if bid_price is not None else None,
                "ask_price": round(ask_price, 4) if ask_price is not None else None,
                "bid_count": bid_count,
                "ask_count": ask_count,
                "total_trades": total,
                "confidence": confidence,
                "confidence_reason": reason,
            }

            compat_runes[display_name] = {
                "ist_value": round(blended, 4) if blended is not None else None,
                "low_confidence": confidence in ("low", "unavailable"),
                "confidence": confidence,
                "bid_price": round(bid_price, 4) if bid_price is not None else None,
                "ask_price": round(ask_price, 4) if ask_price is not None else None,
                "total_trades": total,
            }

            if confidence == "high":
                high_c += 1
            elif confidence == "medium":
                medium_c += 1
            elif confidence == "low":
                low_c += 1
            else:
                unav_c += 1

        total_trades_all += seg_trades
        total_runes_all += len(runes_out)

        ruleset_breakdown = count_rulesets_in_snapshots(seg)

        segments_out[seg] = {
            "segment_slug": seg,
            "platform": meta["platform"],
            "mode": meta["mode"],
            "ladder": meta["ladder"],
            "hardcore": meta["hardcore"],
            "source_file": f"data/prices/rune_prices_{seg}.csv",
            "total_modeled_trades": seg_trades,
            "ruleset_breakdown": ruleset_breakdown,
            "caveat_ruleset": RULESET_CAVEAT,
            "runes": runes_out,
        }

        compat_segments[seg] = compat_runes

    # Aggregate ruleset breakdown across all segments
    aggregate_rulesets = {"counts": {}, "total": 0}
    for seg in SEGMENTS_ORDERED:
        rb = segments_out[seg].get("ruleset_breakdown", {}).get("counts", {})
        for rs, c in rb.items():
            aggregate_rulesets["counts"][rs] = aggregate_rulesets["counts"].get(rs, 0) + c
            aggregate_rulesets["total"] += c

    # Output 1: in_game_rune_values.json
    product_v2 = {
        "schema_version": "0.1",
        "product": "in_game_rune_values",
        "game": "diablo2resurrected",
        "generated_at": generated_at,
        "product_generated_at": generated_at,
        "evidence_class": "completed_player_trades",
        "source": "Traderie completed trades",
        "source_window_label": "rolling_recent_trades_50_cap",
        "caveat_window": "Traderie completed-trade API returns at most 50 recent completed listings per item/segment. Not a full historical archive. Project history depends on scheduled polling and deduped snapshot retention.",
        "caveat_pagination": "nextPage is a boolean/repeating cursor, not a sequential page index. No deeper API pagination observed beyond 50 listings.",
        "caveat_history": "Project history for this source starts when scheduled snapshot retention began. Pre-snapshot history is not available.",
        "ruleset_aggregate": aggregate_rulesets,
        "caveat_ruleset": RULESET_CAVEAT,
        "model": {
            "name": "ist_normalized_vwap_v1",
            "numeraire": "Ist Rune",
            "description": "Volume-weighted average price (VWAP) normalized to Ist Rune using completed player-to-player trades from Traderie.com. Bid and ask sides are computed separately and blended as a simple average.",
            "excludes": [
                "Cash/RMT prices",
                "Reddit/community data",
                "Active listings (non-completed)",
                "Multi-item AND trades (>2 items in request)",
                "Cross-segment merged prices",
                "Non-Ist rune pairs",
            ],
        },
        "caveats": CAVEATS,
        "segments": segments_out,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "in_game_rune_values.json", "w") as f:
        json.dump(product_v2, f, indent=2)

    # Output 2: traderie_tools_prices.json (compatibility feed)
    # Find the most recent source file timestamp for last_update
    last_update = generated_at
    try:
        timestamps = []
        for seg in SEGMENTS_ORDERED:
            p = PRICES_DIR / f"rune_prices_{seg}.csv"
            if p.exists():
                timestamps.append(datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc))
        if timestamps:
            last_update = max(timestamps).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        pass

    compat_product = {
        "schema_version": "0.2",
        "generated_at": generated_at,
        "last_update": last_update,
        "segments": compat_segments,
    }

    with open(OUTPUT_DIR / "traderie_tools_prices.json", "w") as f:
        json.dump(compat_product, f, indent=2)

    # Legacy flat format for backward compatibility with existing userscript
    # The userscript expects ONLY per-segment keys at the top level.
    # No metadata wrapper — the userscript iterates keys as segment names.
    # See docs/USERSCRIPT.md for more details.
    with open(OUTPUT_DIR / "rune_prices_legacy.json", "w") as f:
        json.dump(compat_segments, f, indent=2)

    print(f"Generated: {OUTPUT_DIR / 'rune_prices_legacy.json'} (legacy flat format, no metadata wrapper)")

    # Summary
    print(f"Generated: {OUTPUT_DIR / 'in_game_rune_values.json'}")
    print(f"Generated: {OUTPUT_DIR / 'traderie_tools_prices.json'}")
    print(f"Segments: {len(segments_out)}")
    print(f"Total rune observations: {total_runes_all}")
    print(f"Total modeled trades across all segments: {total_trades_all}")
    print(f"Confidence: high={high_c} medium={medium_c} low={low_c} unavailable={unav_c}")
    for seg in SEGMENTS_ORDERED:
        s = segments_out[seg]
        runes = s["runes"]
        h = sum(1 for r in runes.values() if r["confidence"] == "high")
        m = sum(1 for r in runes.values() if r["confidence"] == "medium")
        l = sum(1 for r in runes.values() if r["confidence"] == "low")
        u = sum(1 for r in runes.values() if r["confidence"] == "unavailable")
        print(f"  {seg}: {len(runes):>2} runes, {s['total_modeled_trades']:>5} trades, h={h} m={m} l={l} u={u}")


if __name__ == "__main__":
    generate()
