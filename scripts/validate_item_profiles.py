#!/usr/bin/env python3
"""
validate_item_profiles.py — Validate item profile JSON files.

Recursively reads data/item_profiles/**/*.json, checks required fields,
nested sections, and data types. Exits nonzero on any invalid profile.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
PROFILES_DIR = ROOT_DIR / "data" / "item_profiles"

REQUIRED_TOP = [
    "schema_version",
    "item_id",
    "display_name",
    "category",
    "game",
    "trade_relevance",
    "gameplay_context",
    "pricing_context",
    "source_signals",
    "research_notes",
    "confidence",
]

REQUIRED_TRADE = [
    "market_role",
    "liquidity",
    "volatility",
    "new_player_risk",
    "commonly_used_as_currency",
]

REQUIRED_GAMEPLAY = [
    "uses",
    "demand_drivers",
]

REQUIRED_PRICING = [
    "common_quote_units",
    "common_trade_forms",
    "known_model_risks",
]

VALID_CATEGORIES = {
    "runes", "commodities", "uniques", "charms", "bases",
    "runewords", "sets", "jewels", "gems", "misc",
}

VALID_CONFIDENCE = {"draft", "validated", "mature", "archived"}

VALID_MARKET_ROLES = {
    "currency", "commodity", "sought_unique", "chase_unique",
    "common_unique", "crafting_base", "charm", "key", "token",
    "consumable", "vanity", "low_trade",
}

VALID_LIQUIDITY = {"very_high", "high", "medium", "low", "very_low", "unknown"}

VALID_VOLATILITY = {"very_high", "high", "medium", "low", "very_low", "unknown"}

VALID_NEW_PLAYER_RISK = {"high", "medium", "low", "unknown"}

VALID_SOURCE_USE = {"yes", "no", "research_only", "unknown"}

REQUIRED_SOURCE_FIELDS = ["use_for_pricing"]

SOURCES = ["traderie", "diablo2_io", "reddit", "d2jsp", "rmt_sites"]

REQUIRED_RESEARCH_NOTE_FIELDS = ["date", "source", "note"]


def validate_required(obj: Any, path: str, fields: List[str], label: str) -> List[str]:
    errors: List[str] = []
    for f in fields:
        if f not in obj:
            errors.append(f"{path}: missing required {label} field '{f}'")
        elif obj[f] is None:
            errors.append(f"{path}: required {label} field '{f}' is null")
    return errors


def validate_enum(obj: Any, path: str, field: str, valid: set) -> List[str]:
    errors: List[str] = []
    val = obj.get(field)
    if val is not None and val not in valid:
        errors.append(f"{path}: '{field}' = '{val}' not in valid values: {sorted(valid)}")
    return errors


def validate_profile(path: Path) -> Tuple[int, List[str]]:
    errors: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        return 0, [f"{path}: invalid JSON — {e}"]
    except Exception as e:
        return 0, [f"{path}: read error — {e}"]

    loc = str(path.relative_to(ROOT_DIR))

    # Top-level fields
    errors.extend(validate_required(data, loc, REQUIRED_TOP, "top-level"))

    if not data.get("item_id", "").strip():
        errors.append(f"{loc}: 'item_id' is empty")
    if not data.get("display_name", "").strip():
        errors.append(f"{loc}: 'display_name' is empty")

    category = data.get("category", "")
    if category and category not in VALID_CATEGORIES:
        errors.append(f"{loc}: 'category' = '{category}' not valid: {sorted(VALID_CATEGORIES)}")

    # Check parent directory matches category (heuristic)
    parent_dir = path.parent.name
    if category and parent_dir in VALID_CATEGORIES and category != parent_dir:
        errors.append(f"{loc}: 'category' = '{category}' but parent dir is '{parent_dir}'")

    errors.extend(validate_enum(data, loc, "confidence", VALID_CONFIDENCE))

    # trade_relevance
    tr = data.get("trade_relevance", {})
    errors.extend(validate_required(tr, f"{loc}.trade_relevance", REQUIRED_TRADE, "trade_relevance"))
    if isinstance(tr, dict):
        errors.extend(validate_enum(tr, f"{loc}.trade_relevance", "market_role", VALID_MARKET_ROLES))
        errors.extend(validate_enum(tr, f"{loc}.trade_relevance", "liquidity", VALID_LIQUIDITY))
        errors.extend(validate_enum(tr, f"{loc}.trade_relevance", "volatility", VALID_VOLATILITY))
        errors.extend(validate_enum(tr, f"{loc}.trade_relevance", "new_player_risk", VALID_NEW_PLAYER_RISK))

    # gameplay_context
    gc = data.get("gameplay_context", {})
    errors.extend(validate_required(gc, f"{loc}.gameplay_context", REQUIRED_GAMEPLAY, "gameplay_context"))
    if isinstance(gc.get("uses"), list) and len(gc["uses"]) == 0:
        errors.append(f"{loc}.gameplay_context.uses: must have at least one use")

    # pricing_context
    pc = data.get("pricing_context", {})
    errors.extend(validate_required(pc, f"{loc}.pricing_context", REQUIRED_PRICING, "pricing_context"))

    # source_signals
    ss = data.get("source_signals", {})
    if not isinstance(ss, dict):
        errors.append(f"{loc}.source_signals: must be an object")
    else:
        for src in SOURCES:
            if src not in ss:
                errors.append(f"{loc}.source_signals: missing source '{src}'")
                continue
            entry = ss[src]
            if not isinstance(entry, dict):
                errors.append(f"{loc}.source_signals.{src}: must be an object")
                continue
            use = entry.get("use_for_pricing")
            if use not in VALID_SOURCE_USE:
                errors.append(f"{loc}.source_signals.{src}: 'use_for_pricing' = '{use}' not valid: {sorted(VALID_SOURCE_USE)}")

    # research_notes
    rn = data.get("research_notes", [])
    if not isinstance(rn, list):
        errors.append(f"{loc}.research_notes: must be an array")
    elif len(rn) == 0:
        errors.append(f"{loc}.research_notes: must have at least one entry")
    else:
        for i, note in enumerate(rn):
            errors.extend(validate_required(note, f"{loc}.research_notes[{i}]", REQUIRED_RESEARCH_NOTE_FIELDS, "research_note"))

    return len(data.get("research_notes", [])), errors


def main() -> None:
    if not PROFILES_DIR.exists():
        print(f"ERROR: profiles directory not found: {PROFILES_DIR}")
        sys.exit(1)

    profile_files = sorted(PROFILES_DIR.rglob("*.json"))
    if not profile_files:
        print(f"ERROR: no JSON files found under {PROFILES_DIR}")
        sys.exit(1)

    total_errors = 0
    total_profiles = 0
    by_category: Dict[str, int] = {}

    for pf in profile_files:
        category = pf.parent.name
        note_count, errors = validate_profile(pf)
        total_profiles += 1
        by_category[category] = by_category.get(category, 0) + 1

        if errors:
            total_errors += len(errors)
            for e in errors:
                print(f"  FAIL  {e}")
        else:
            print(f"  OK    {pf.relative_to(ROOT_DIR)}  ({note_count} research notes)")

    print()
    print("=" * 50)
    print(f"Profiles found:    {total_profiles}")
    print(f"Profiles by category:")
    for cat in sorted(by_category):
        print(f"  {cat}: {by_category[cat]}")
    print(f"Validation errors: {total_errors}")
    print("=" * 50)

    if total_errors > 0:
        sys.exit(1)

    print("All profiles valid.")


if __name__ == "__main__":
    main()
