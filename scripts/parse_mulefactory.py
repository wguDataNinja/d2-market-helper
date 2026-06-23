#!/usr/bin/env python3
"""
parse_mulefactory.py — Parse MuleFactory static HTML with Schema.org
microdata into cash price observations.

Usage:
  python3 scripts/parse_mulefactory.py

Output: data/external/mulefactory_cash_prices.json
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import extruct
from w3lib.html import get_base_url

from lib import snapshot_io

ROOT_DIR = Path(__file__).resolve().parent.parent
FIXTURE_PATH = ROOT_DIR / "research" / "sources" / "downloads" / "rune_sources_2026-06-20" / "mulefactory.html"
OUTPUT_PATH = ROOT_DIR / "data" / "external" / "mulefactory_cash_prices.json"
RUNE_REGISTRY_PATH = ROOT_DIR / "data" / "rune_registry.json"
SOURCE_URL = "https://www.mulefactory.com/buy_diablo_2_remaster_rune/"
PRODUCT_BASE_URL = "https://www.mulefactory.com/buy_diablo_2_remaster_rune/"


def load_rune_registry():
    with open(RUNE_REGISTRY_PATH) as f:
        return json.load(f)


def build_rune_lookup(registry):
    lookup = {}
    for entry in registry:
        lookup[entry["name"].lower()] = entry
    return lookup


def match_rune(name, rune_lookup):
    if name is None:
        return None
    return rune_lookup.get(name.lower())


def parse():
    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    html = FIXTURE_PATH.read_text(errors="replace")
    base_url = get_base_url(html, SOURCE_URL)
    data = extruct.extract(html, base_url=base_url, syntaxes=["microdata"])

    registry = load_rune_registry()
    rune_lookup = build_rune_lookup(registry)

    products = [
        x for x in data.get("microdata", [])
        if x.get("type") in ("http://schema.org/Product", "https://schema.org/Product")
    ]

    observations = []
    for product in products:
        props = product.get("properties", {})
        name = props.get("name")
        if not name:
            continue

        matched = match_rune(name, rune_lookup)
        if matched is None:
            continue

        offers = props.get("offers", {})
        if not isinstance(offers, dict):
            continue
        offer_props = offers.get("properties", {})

        raw_price = offer_props.get("price")
        currency = offer_props.get("priceCurrency", "USD")
        if raw_price is None:
            continue

        try:
            price_usd = float(raw_price)
        except (ValueError, TypeError):
            continue

        price_cents = round(price_usd * 100)

        obs = {
            "source_slug": "mulefactory",
            "evidence_class": "cash_listing",
            "item_name": matched["names"]["cash"],
            "normalized_item_name": matched["names"]["cash"],
            "item_type": "rune",
            "price": price_usd,
            "price_cents": price_cents,
            "currency": currency,
            "segment_confidence": "low",
            "use_in_model": False,
            "captured_at": captured_at,
            "source_artifact_path": str(FIXTURE_PATH.relative_to(ROOT_DIR)),
            "source_url": SOURCE_URL,
            "product_url": None,
            "item_slug": matched["names"]["cash_slug"],
            "raw_text": name,
            "parser_notes": "Extracted from Schema.org microdata on MuleFactory rune listing page.",
            "item_category": "rune",
        }
        observations.append(obs)

    raw_payload = {
        "url": SOURCE_URL,
        "captured_at": captured_at,
        "product_count": len(products),
        "rune_count": len(observations),
    }

    snapshot_io.write_raw_snapshot(raw_payload, "mulefactory")
    snapshot_io.write_normalized_snapshot(observations, "mulefactory")
    snapshot_io.append_history("mulefactory", "cash_prices", observations)

    artifact_path = str(FIXTURE_PATH.relative_to(ROOT_DIR))

    output = {
        "schema_version": "0.1",
        "product": "mulefactory_cash_prices",
        "source_slug": "mulefactory",
        "generated_at": captured_at,
        "artifact_path": artifact_path,
        "observation_count": len(observations),
        "observations": observations,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWritten: {OUTPUT_PATH}")
    print(f"  Total observations: {len(observations)}")

    return output


if __name__ == "__main__":
    parse()
