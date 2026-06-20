#!/usr/bin/env python3
"""
validate_in_game_rune_values.py — Validate both generated price product files.
"""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
V2_PATH = ROOT_DIR / "data" / "products" / "in_game_rune_values.json"
COMPAT_PATH = ROOT_DIR / "data" / "products" / "traderie_tools_prices.json"

REQUIRED_SEGMENTS = {"pc_sc_l", "pc_sc_nl", "pc_hc_l", "pc_hc_nl"}
ALLOWED_CONFIDENCE = {"high", "medium", "low", "unavailable"}
REQUIRED_RUNE_FIELDS = [
    "rune", "value_ist", "bid_price", "ask_price",
    "bid_count", "ask_count", "total_trades", "confidence", "confidence_reason",
]


def validate_v2():
    errors = []
    warnings = []

    if not V2_PATH.exists():
        return [f"NOT FOUND: {V2_PATH}"], warnings

    with open(V2_PATH) as f:
        d = json.load(f)

    # Top-level fields
    if d.get("schema_version") != "0.1":
        errors.append("schema_version not '0.1'")
    if d.get("product") != "in_game_rune_values":
        errors.append("product not 'in_game_rune_values'")
    if d.get("evidence_class") != "completed_player_trades":
        errors.append("evidence_class should be 'completed_player_trades'")
    if not d.get("generated_at"):
        errors.append("missing generated_at")
    if not d.get("product_generated_at"):
        warnings.append("missing product_generated_at (freshness metadata)")
    if not d.get("model"):
        errors.append("missing model block")

    if d.get("source_window_label") and d["source_window_label"] not in ("unknown_window", "current_snapshot", "historical_window", "rolling_recent_trades_50_cap"):
        warnings.append(f"unrecognized source_window_label '{d.get('source_window_label')}'")

    # Model
    model = d.get("model", {})
    if model.get("numeraire") != "Ist Rune":
        errors.append("numeraire should be 'Ist Rune'")

    # Segments
    segs = d.get("segments", {})
    seg_keys = set(segs.keys())
    if seg_keys != REQUIRED_SEGMENTS:
        errors.append(f"segments mismatch: got {seg_keys}, expected {REQUIRED_SEGMENTS}")

    prev_rune = None
    for slug in REQUIRED_SEGMENTS:
        seg = segs.get(slug, {})
        if not seg:
            errors.append(f"segment {slug} is empty")
            continue

        runes = seg.get("runes", {})
        if not runes:
            errors.append(f"segment {slug} has no runes")

        for rname, r in runes.items():
            for field in REQUIRED_RUNE_FIELDS:
                if field not in r:
                    errors.append(f"{slug}.{rname}: missing field '{field}'")

            conf = r.get("confidence", "")
            if conf not in ALLOWED_CONFIDENCE:
                errors.append(f"{slug}.{rname}: invalid confidence '{conf}'")

            if r.get("confidence") == "unavailable" and r.get("value_ist") is not None:
                errors.append(f"{slug}.{rname}: unavailable confidence but value_ist is not null")

    return errors, warnings


def validate_compat():
    errors = []

    if not COMPAT_PATH.exists():
        return [f"NOT FOUND: {COMPAT_PATH}"]

    with open(COMPAT_PATH) as f:
        d = json.load(f)

    if not d.get("schema_version"):
        errors.append("compat: missing schema_version")
    if not d.get("generated_at"):
        errors.append("compat: missing generated_at")
    if not d.get("last_update"):
        errors.append("compat: missing last_update")

    segs = d.get("segments", {})
    seg_keys = set(segs.keys())
    if seg_keys != REQUIRED_SEGMENTS:
        errors.append(f"compat segments mismatch: got {seg_keys}, expected {REQUIRED_SEGMENTS}")

    for slug in REQUIRED_SEGMENTS:
        runes = segs.get(slug, {})
        for rname, r in runes.items():
            if "ist_value" not in r:
                errors.append(f"compat {slug}.{rname}: missing ist_value")
            if "low_confidence" not in r:
                errors.append(f"compat {slug}.{rname}: missing low_confidence")
            if not isinstance(r.get("low_confidence"), bool):
                errors.append(f"compat {slug}.{rname}: low_confidence should be boolean")

    return errors


def main():
    print("=== in_game_rune_values.json ===")
    v2_errors, v2_warnings = validate_v2()
    if v2_warnings:
        print(f"WARNINGS ({len(v2_warnings)}):")
        for w in v2_warnings:
            print(f"  {w}")
    if v2_errors:
        print(f"ERRORS ({len(v2_errors)}):")
        for e in v2_errors:
            print(f"  {e}")
    else:
        print("  All checks passed.")

    print()
    print("=== traderie_tools_prices.json ===")
    compat_errors = validate_compat()
    if compat_errors:
        print(f"ERRORS ({len(compat_errors)}):")
        for e in compat_errors:
            print(f"  {e}")
    else:
        print("  All checks passed.")

    if v2_errors or compat_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
