#!/usr/bin/env python3
"""
parse_itemnow_api.py — Extract D2R rune cash prices from ItemNow WooCommerce Store API.

Usage:
  python scripts/parse_itemnow_api.py                              # live fetch
  python scripts/parse_itemnow_api.py --offline <fixture.json>     # from saved fixture

Output: data/external/itemnow_cash_prices.json
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
from scripts.lib.snapshot_io import (
    append_history,
    write_normalized_snapshot,
    write_raw_snapshot,
)

OUTPUT = ROOT_DIR / "data" / "external" / "itemnow_cash_prices.json"
STORE_API_URL = "https://itemnow.com/wp-json/wc/store/v1/products?category=99&per_page=100"

RUNE_PATTERN = re.compile(r'^([A-Z][a-z]+) Rune$')
BUNDLE_PATTERN = re.compile(r'Multiple Rune Package')


def load_rune_registry():
    path = ROOT_DIR / "data" / "rune_registry.json"
    with open(path) as f:
        entries = json.load(f)
    registry = {}
    for e in entries:
        short = e["short_name"]
        registry[short.lower()] = {
            "id": e["id"],
            "name": e["name"],
            "short_name": short,
            "order": e["id"],
        }
    return registry


def fetch_products(offline_path=None):
    if offline_path:
        path = Path(offline_path)
        if not path.exists():
            print(f"ERROR: fixture not found: {path}")
            sys.exit(1)
        with open(path) as f:
            return json.load(f)
    print(f"Fetching: {STORE_API_URL}")
    with urlopen(STORE_API_URL, timeout=30) as resp:
        return json.load(resp)


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", default=None, help="Path to saved API fixture JSON")
    args = parser.parse_args()

    rune_registry = load_rune_registry()
    products = fetch_products(args.offline)
    write_raw_snapshot(products, "itemnow")
    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    artifact_path = ""
    if args.offline:
        ap = Path(args.offline)
        if not ap.is_absolute():
            ap = Path.cwd() / ap
        artifact_path = str(ap.resolve().relative_to(ROOT_DIR.resolve()))

    observations = []
    rune_count = 0
    bundle_count = 0

    for p in products:
        name = p["name"]
        slug = p["slug"]
        product_id = p["id"]
        permalink = p["permalink"]
        is_in_stock = p.get("is_in_stock", False)
        stock_status = "in_stock" if is_in_stock else "out_of_stock"

        price_str = p.get("prices", {}).get("price", "0")
        try:
            price_cents = int(price_str)
            price_usd = round(price_cents / 100, 2)
        except (ValueError, TypeError):
            price_usd = None

        price_range = p.get("prices", {}).get("price_range", {})
        price_min_cents = int(price_range.get("min_amount", 0)) if price_range else price_cents
        price_max_cents = int(price_range.get("max_amount", 0)) if price_range else price_cents
        price_min_usd = round(price_min_cents / 100, 2)
        price_max_usd = round(price_max_cents / 100, 2)

        attributes = p.get("attributes", [])
        segment_terms = []
        for attr in attributes:
            if attr.get("name") == "server" or attr.get("taxonomy") == "pa_server":
                for term in attr.get("terms", []):
                    segment_terms.append({
                        "slug": term.get("slug"),
                        "name": term.get("name"),
                    })

        variations = p.get("variations", [])
        variation_count = len(variations)

        is_bundle = bool(BUNDLE_PATTERN.search(name))
        rune_match = RUNE_PATTERN.match(name)

        if is_bundle:
            item_category = "bundle"
            bundle_count += 1
        elif rune_match:
            item_category = "rune"
            rune_count += 1
        else:
            item_category = "unknown"

        rune_short = rune_match.group(1).lower() if rune_match else None
        registry_entry = rune_registry.get(rune_short) if rune_short else None
        normalized_item_name = registry_entry["name"] if registry_entry else name

        rune_order = registry_entry["order"] if registry_entry else None

        caveats = []
        if is_bundle:
            caveats.append("Bundle product — excluded from individual rune price comparison")
        if not rune_match:
            caveats.append("Product name does not match expected rune pattern")
        if segment_terms:
            caveats.append(
                f"Product has {len(segment_terms)} server attribute terms "
                f"(D2R Ladder/Non-Ladder/HC Ladder/HC Non-Ladder + legacy). "
                f"Store API base price may be the minimum variation price — "
                f"per-segment prices require variation-level access."
            )
        if price_range and price_min_usd != price_max_usd:
            caveats.append(
                f"Price range: ${price_min_usd:.2f} – ${price_max_usd:.2f}. "
                f"Base price ${price_usd:.2f} is the minimum."
            )
        if not is_in_stock:
            caveats.append("Product is out of stock")

        parser_notes = (
            f"Extracted from WooCommerce Store API ({STORE_API_URL}). "
            f"Prices in USD cents, converted to dollars. "
            f"Score: segment_confidence=low (base price only, per-segment variation prices not accessible via public Store API). "
        )
        if is_bundle:
            parser_notes += f"Product is a bundle ({variation_count} variations). "
        else:
            parser_notes += f"Product is a variable rune ({variation_count} server variations). "

        item_slug = f"{rune_short}_rune" if rune_short else slug.replace("-", "_")
        item_name = registry_entry["short_name"] if registry_entry else (rune_match.group(1) if rune_match else name)

        obs = {
            "source_slug": "itemnow",
            "evidence_class": "cash_market_listing",
            "captured_at": captured_at,
            "source_artifact_path": artifact_path,
            "source_url": permalink,
            "item_name": item_name,
            "item_slug": item_slug,
            "item_category": item_category,
            "product_id": product_id,
            "product_slug": slug,
            "normalized_item_name": normalized_item_name,
            "rune_order": rune_order,
            "price": price_usd,
            "price_min_usd": price_min_usd,
            "price_max_usd": price_max_usd,
            "currency": "USD",
            "quantity": 1,
            "unit_price": price_usd,
            "stock_status": stock_status,
            "is_in_stock": is_in_stock,
            "segment_terms": segment_terms,
            "variation_count": variation_count,
            "platform": None,
            "ladder": None,
            "hardcore": None,
            "softcore": None,
            "season_or_ruleset": None,
            "segment_confidence": "low",
            "base_price_scope": "unknown",
            "use_in_model": False,
            "raw_text": name,
            "caveats": caveats,
            "parser_notes": parser_notes,
        }
        observations.append(obs)

    write_normalized_snapshot(observations, "itemnow")
    append_history("itemnow", "cash_prices", observations)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump({
            "schema_version": "0.1",
            "product": "itemnow_cash_prices",
            "source_slug": "itemnow",
            "generated_at": captured_at,
            "artifact_path": artifact_path or STORE_API_URL,
            "total_products": len(products),
            "rune_count": rune_count,
            "bundle_count": bundle_count,
            "observation_count": len(observations),
            "observations": observations,
        }, f, indent=2)

    print(f"ItemNow parser: {len(observations)} products ({rune_count} individual runes, {bundle_count} bundles)")
    print()
    for obs in observations:
        label = "RUN" if obs["item_category"] == "rune" else "BND"
        seg_label = f"seg={obs['segment_confidence']}"
        stock_label = "in_stock" if obs["is_in_stock"] else "OUT"
        min_p = obs.get("price_min_usd", obs["price"])
        max_p = obs.get("price_max_usd", obs["price"])
        if min_p != max_p:
            price_str = f"${min_p:.2f}–${max_p:.2f}"
        else:
            price_str = f"${obs['price']:.2f}"
        print(f"  [{label}] {obs['item_name']:15s} {price_str:>18s}  {stock_label:8s}  {seg_label}")
    print()
    print(f"Wrote: {OUTPUT}")
    return observations


if __name__ == "__main__":
    parse()
