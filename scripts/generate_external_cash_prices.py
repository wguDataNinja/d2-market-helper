#!/usr/bin/env python3
"""
generate_external_cash_prices.py — Merge per-source external cash prices
into a single normalized product file.

Inputs:
- data/external/iggm_cash_prices.json
- data/external/items7_cash_prices.json

Output:
- data/products/external_cash_prices.sample.json
"""

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
INPUTS = [
    ROOT_DIR / "data" / "external" / "iggm_cash_prices.json",
    ROOT_DIR / "data" / "external" / "items7_cash_prices.json",
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

    # Normalize each observation to required fields
    normalized = []
    for obs in all_observations:
        normalized.append({
            "source_slug": obs.get("source_slug"),
            "evidence_class": obs.get("evidence_class", "cash_market_listing"),
            "captured_at": obs.get("captured_at"),
            "source_artifact_path": obs.get("source_artifact_path"),
            "source_url": obs.get("source_url"),
            "item_name": obs.get("item_name"),
            "item_slug": obs.get("item_slug"),
            "item_category": obs.get("item_category"),
            "price": obs.get("price"),
            "currency": obs.get("currency", "USD"),
            "quantity": obs.get("quantity"),
            "unit_price": obs.get("unit_price"),
            "platform": obs.get("platform"),
            "ladder": obs.get("ladder"),
            "hardcore": obs.get("hardcore"),
            "softcore": obs.get("softcore"),
            "season_or_ruleset": obs.get("season_or_ruleset"),
            "segment_confidence": obs.get("segment_confidence", "low"),
            "raw_text": obs.get("raw_text"),
            "parser_notes": obs.get("parser_notes"),
        })

    product = {
        "schema_version": "0.1",
        "product": "external_cash_prices",
        "generated_at": generated_at,
        "model": "external_cash_listing_snapshot_v0",
        "caveats": CAVEATS,
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
