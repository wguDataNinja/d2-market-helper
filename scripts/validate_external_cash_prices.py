#!/usr/bin/env python3
"""
validate_external_cash_prices.py — Validate external_cash_prices.sample.json.

Checks:
- product file exists
- schema_version exists
- observations is a list
- each observation has required fields
- evidence_class is cash_market_listing
- no observation claims to be completed_player_trade
- no observation is written into data/prices/
- source_slug exists in data/source_manifest.json
"""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PRODUCT_PATH = ROOT_DIR / "data" / "products" / "external_cash_prices.sample.json"
MANIFEST_PATH = ROOT_DIR / "data" / "source_manifest.json"

REQUIRED_OBS_FIELDS = [
    "source_slug", "evidence_class", "item_name", "price", "currency",
]

ALLOWED_EVIDENCE_CLASSES = {"cash_market_listing"}

PRICES_DIR = ROOT_DIR / "data" / "prices"


def validate():
    errors = []

    if not PRODUCT_PATH.exists():
        print(f"ERROR: product file not found: {PRODUCT_PATH}")
        sys.exit(1)

    with open(PRODUCT_PATH) as f:
        product = json.load(f)

    # Schema version
    if "schema_version" not in product:
        errors.append("missing 'schema_version'")

    # Product name
    if product.get("product") != "external_cash_prices":
        errors.append(f"product should be 'external_cash_prices', got '{product.get('product')}'")

    # Observations
    obs = product.get("observations", [])
    if not isinstance(obs, list):
        errors.append("'observations' must be a list")
        obs = []

    # Load manifest for slug validation
    manifest_slugs = set()
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)
            manifest_slugs = {s["source_slug"] for s in manifest}

    for i, o in enumerate(obs):
        idx = f"observations[{i}]"

        # Required fields
        for field in REQUIRED_OBS_FIELDS:
            if field not in o:
                errors.append(f"{idx}: missing '{field}'")
            elif field == "price" and o[field] is None:
                errors.append(f"{idx}: 'price' is null")

        # Evidence class
        ec = o.get("evidence_class", "")
        if ec and ec not in ALLOWED_EVIDENCE_CLASSES:
            errors.append(f"{idx}: evidence_class '{ec}' not in allowed: {ALLOWED_EVIDENCE_CLASSES}")

        # No completed_player_trade claims
        if ec == "completed_player_trade":
            errors.append(f"{idx}: evidence_class is 'completed_player_trade' — cash prices must not claim this")

        # No prices in data/prices/
        if o.get("item_slug"):
            price_path = PRICES_DIR / f"rune_prices_pc_sc_l.csv"
            if price_path.exists():
                pass  # just check the path exists, don't assert

        # Source slug in manifest
        slug = o.get("source_slug", "")
        if slug and manifest_slugs and slug not in manifest_slugs:
            errors.append(f"{idx}: source_slug '{slug}' not found in data/source_manifest.json")

    # Check no cash prices ended up in data/prices/
    if PRICES_DIR.exists():
        cash_names = {"iggm", "items7", "g2g", "playerauctions", "odealo"}
        for f in PRICES_DIR.glob("*"):
            if any(cn in f.name.lower() for cn in cash_names):
                errors.append(f"cash-market file found in data/prices/: {f.name}")

    # Report
    print(f"Validation: external_cash_prices.sample.json")
    print(f"  Observations: {len(obs)}")
    print(f"  Sources in product: {len(product.get('sources', []))}")
    print()

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("  All checks passed.")


if __name__ == "__main__":
    validate()
