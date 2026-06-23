#!/usr/bin/env python3
"""
generate_external_cash_prices.py — Merge per-source external cash prices
into a single normalized product file.

Inputs:
- data/external/iggm_cash_prices.json
- data/external/itemnow_cash_prices.json
- data/external/items7_cash_prices.json
- data/external/d2stock_cash_prices.json

Output:
- data/products/external_cash_prices.sample.json
"""

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
INPUTS = [
    ROOT_DIR / "data" / "external" / "iggm_cash_prices.json",
    ROOT_DIR / "data" / "external" / "itemnow_cash_prices.json",
    ROOT_DIR / "data" / "external" / "items7_cash_prices.json",
    ROOT_DIR / "data" / "external" / "d2stock_cash_prices.json",
    ROOT_DIR / "data" / "external" / "mulefactory_cash_prices.json",
]
OUTPUT = ROOT_DIR / "data" / "products" / "external_cash_prices.sample.json"

CAVEATS = [
    "Cash/RMT listings are external comparison only. Not used for in-game rune ratios.",
    "Prices are asking prices from sellers, not completed transaction prices.",
    "Prices may include seller margin, delivery risk, site fees, minimum price floors, and stock constraints.",
    "Source segment metadata may differ — do not assume cross-source segment compatibility.",
    "Observations are from saved/captured artifacts, not live feeds.",
    "Do not blend these prices into the in-game rune value model.",
    "Low-value cash prices may have baseline padding due to transaction friction and minimum price floors.",
]

SOURCE_CAVEATS = {
    "iggm": [
        "IGGM: page-level URL only — all runes on a single listing page, no per-item deep links.",
        "IGGM: segment context confirmed PC Non-Ladder Softcore ROTW from browser capture metadata.",
    ],
    "itemnow": [
        "ItemNow: base/minimum variation prices from WooCommerce Store API — not segment-specific.",
        "ItemNow: prices are the same across all 4 D2R segments (Ladder, Non-Ladder, HC Ladder, HC Non-Ladder).",
        "ItemNow: per-segment variation prices require WC v3 API authentication — deferred.",
    ],
    "items7": [
        "items7: static HTML does not contain per-rune prices. Browser capture required.",
    ],
    "d2stock": [
        "D2Stock: segment context from RSS feed titles only — Softcore Ladder RotW / Softcore Non-Ladder RotW.",
        "D2Stock: single-rune prices are segment-specific (2 separate feed items per rune).",
        "D2Stock: 10-pack and runeword bundles excluded from single-rune comparisons.",
    ],
    "mulefactory": [
        "MuleFactory: prices are 'from' (minimum/base) prices from Schema.org microdata.",
        "MuleFactory: segment metadata not available — server/platform selector requires JavaScript.",
        "MuleFactory: 24 of 33 runes displayed (page 1); remaining runes hidden behind AJAX pagination.",
    ],
}

ITEM_CATEGORY_MAP = {
    "rune": "rune",
    "runes": "rune",
    "bundle": "bundle",
    "bundles": "bundle",
    "item": "item",
    "items": "item",
    None: "unknown",
}


def map_item_type(category):
    if category is None:
        return "unknown"
    key = str(category).lower().strip()
    return ITEM_CATEGORY_MAP.get(key, "unknown")


def normalize_item_name(name):
    if not name:
        return None
    return name.strip()


def load_source(path):
    if not path.exists():
        print(f"  WARNING: not found: {path}")
        return None
    with open(path) as f:
        return json.load(f)


def generate():
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    sources_data = []
    all_observations = []

    for path in INPUTS:
        data = load_source(path)
        if data is None:
            continue

        slug = data.get("source_slug", "?")
        obs = data.get("observations", [])
        count = len(obs)
        artifact_paths = [data.get("artifact_path", "")] if data.get("artifact_path") else []

        sources_data.append({
            "source_slug": slug,
            "observation_count": count,
            "artifact_paths": artifact_paths,
        })
        all_observations.extend(obs)
        print(f"  {slug}: {count} observations")

    normalized = []
    for obs in all_observations:
        item_name = obs.get("item_name") or ""
        raw_price = obs.get("price")

        source_caveats = SOURCE_CAVEATS.get(obs.get("source_slug"), [])

        price_cents = None
        if raw_price is not None:
            try:
                price_cents = round(float(raw_price) * 100)
            except (ValueError, TypeError):
                pass

        entry = {
            "source_slug": obs.get("source_slug"),
            "evidence_class": "cash_listing",
            "captured_at": obs.get("captured_at"),
            "source_artifact_path": obs.get("source_artifact_path"),
            "source_url": obs.get("source_url"),
            "product_url": obs.get("product_url"),
            "item_name": item_name,
            "normalized_item_name": normalize_item_name(item_name),
            "item_slug": obs.get("item_slug"),
            "item_type": map_item_type(obs.get("item_category")),
            "price_usd": raw_price,
            "price_cents": price_cents,
            "currency": obs.get("currency", "USD"),
            "quantity": obs.get("quantity"),
            "unit_price": obs.get("unit_price"),
            "platform": obs.get("platform"),
            "ladder": obs.get("ladder"),
            "hardcore": obs.get("hardcore"),
            "softcore": obs.get("softcore"),
            "season_or_ruleset": obs.get("season_or_ruleset"),
            "segment_confidence": obs.get("segment_confidence", "low"),
            "use_in_model": False,
            "caveats": source_caveats,
            "raw_text": obs.get("raw_text"),
            "parser_notes": obs.get("parser_notes"),
        }
        normalized.append(entry)

    product = {
        "schema_version": "0.2",
        "product": "external_cash_prices",
        "generated_at": generated_at,
        "product_generated_at": generated_at,
        "source_window_label": "current_snapshot",
        "model": "external_cash_listing_snapshot_v0",
        "caveats": CAVEATS,
        "caveat_history": "Project history starts when snapshots began. Prices are current snapshots, not historical time series.",
        "sources": sources_data,
        "observations": normalized,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(product, f, indent=2)

    total = len(normalized)
    print(f"\nGenerated: {OUTPUT}")
    print(f"Total observations: {total}")
    print(f"Sources: {len(sources_data)}")
    return product


if __name__ == "__main__":
    generate()
