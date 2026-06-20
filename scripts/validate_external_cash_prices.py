#!/usr/bin/env python3
"""
validate_external_cash_prices.py — Validate external_cash_prices.sample.json.

Hardened validation for the external cash product schema (v0.2+).

Checks:
- product file exists
- schema_version is 0.2+
- observations is a list
- each observation has all required fields
- use_in_model must be false (cash observations are never in-model)
- source_slug must be present and non-empty
- item_name must be present and non-empty
- price_usd must be present and non-null for cash listings
- normalized_item_name must exist and be reasonable
- evidence_class must be "cash_listing"
- item_type must be one of: rune, bundle, item, unknown
- source_url and product_url are optional (allowed to be null/missing)
- checks no cash observations ended up in data/prices/
- validates source_slug exists in source_manifest.json
"""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PRODUCT_PATH = ROOT_DIR / "data" / "products" / "external_cash_prices.sample.json"
MANIFEST_PATH = ROOT_DIR / "data" / "source_manifest.json"

REQUIRED_OBS_FIELDS = [
    "source_slug",
    "evidence_class",
    "item_name",
    "normalized_item_name",
    "item_type",
    "price_usd",
    "price_cents",
    "currency",
    "segment_confidence",
    "use_in_model",
    "captured_at",
]

ALLOWED_EVIDENCE_CLASSES = {"cash_listing"}

ALLOWED_ITEM_TYPES = {"rune", "bundle", "item", "unknown"}

ALLOWED_SEGMENT_CONFIDENCE = {"low", "medium", "high"}

PRICES_DIR = ROOT_DIR / "data" / "prices"

CASH_SOURCE_NAMES = {"iggm", "itemnow", "items7", "d2stock", "g2g", "playerauctions", "odealo"}


def validate():
    errors = []
    warnings = []

    if not PRODUCT_PATH.exists():
        print(f"ERROR: product file not found: {PRODUCT_PATH}")
        sys.exit(1)

    with open(PRODUCT_PATH) as f:
        product = json.load(f)

    # Schema version
    sv = product.get("schema_version", "")
    if not sv:
        errors.append("missing 'schema_version'")
    elif sv < "0.2":
        warnings.append(f"schema_version '{sv}' is below 0.2 — consider upgrading")

    # Product name
    if product.get("product") != "external_cash_prices":
        errors.append(f"product should be 'external_cash_prices', got '{product.get('product')}'")

    # Freshness metadata (optional — warn if absent)
    if not product.get("product_generated_at"):
        warnings.append("missing product_generated_at (freshness metadata)")
    swl = product.get("source_window_label")
    if swl and swl not in ("current_snapshot", "unknown_window", "historical_window"):
        warnings.append(f"unrecognized source_window_label '{swl}'")
    if product.get("caveat_history") and not isinstance(product.get("caveat_history"), str):
        warnings.append("caveat_history should be a string")

    # Sources list
    sources_list = product.get("sources", [])
    if not isinstance(sources_list, list):
        errors.append("'sources' must be a list")
    elif len(sources_list) == 0:
        warnings.append("'sources' list is empty")

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

        # Required fields existence
        for field in REQUIRED_OBS_FIELDS:
            if field not in o:
                errors.append(f"{idx}: missing '{field}'")

        # source_slug must be non-empty
        slug = o.get("source_slug")
        if not slug:
            errors.append(f"{idx}: 'source_slug' is missing or empty")

        # item_name must be non-empty
        item_name = o.get("item_name")
        if not item_name:
            errors.append(f"{idx}: 'item_name' is missing or empty")

        # normalized_item_name must be non-empty and reasonable
        nin = o.get("normalized_item_name")
        if not nin:
            errors.append(f"{idx}: 'normalized_item_name' is missing or empty")
        elif len(nin) < 2 or len(nin) > 100:
            warnings.append(f"{idx}: 'normalized_item_name' has unusual length: '{nin}'")

        # price_usd must be present and non-null
        price = o.get("price_usd")
        if price is None:
            errors.append(f"{idx}: 'price_usd' is null or missing — cash listings require a price")

        # price_cents must be an integer when present
        pc = o.get("price_cents")
        if pc is not None and not isinstance(pc, int):
            errors.append(f"{idx}: 'price_cents' must be an integer, got {type(pc).__name__}")

        # Evidence class — must be cash_listing
        ec = o.get("evidence_class", "")
        if not ec:
            errors.append(f"{idx}: 'evidence_class' is missing")
        elif ec not in ALLOWED_EVIDENCE_CLASSES:
            errors.append(f"{idx}: evidence_class '{ec}' not in allowed: {ALLOWED_EVIDENCE_CLASSES}")

        # Item type
        it = o.get("item_type", "")
        if not it:
            errors.append(f"{idx}: 'item_type' is missing")
        elif it not in ALLOWED_ITEM_TYPES:
            errors.append(f"{idx}: item_type '{it}' not in allowed: {ALLOWED_ITEM_TYPES}")

        # Segment confidence
        sc = o.get("segment_confidence", "")
        if sc and sc not in ALLOWED_SEGMENT_CONFIDENCE:
            errors.append(f"{idx}: segment_confidence '{sc}' not in allowed: {ALLOWED_SEGMENT_CONFIDENCE}")

        # use_in_model MUST be false
        uim = o.get("use_in_model")
        if uim is True:
            errors.append(f"{idx}: 'use_in_model' is True — cash observations must never be in-model")
        elif uim is False:
            pass
        else:
            pass  # Missing is OK if generator always writes it

        # captured_at must exist
        ca = o.get("captured_at")
        if ca is None:
            errors.append(f"{idx}: 'captured_at' is missing")

        # No completed_player_trade claims
        if ec == "completed_player_trade":
            errors.append(f"{idx}: evidence_class is 'completed_player_trade' — cash prices must not claim this")

        # Source slug in manifest
        if slug and manifest_slugs and slug not in manifest_slugs:
            errors.append(f"{idx}: source_slug '{slug}' not found in data/source_manifest.json")

    # Check no cash prices ended up in data/prices/
    if PRICES_DIR.exists():
        for f in PRICES_DIR.glob("*"):
            if any(cn in f.name.lower() for cn in CASH_SOURCE_NAMES):
                errors.append(f"cash-market file found in data/prices/: {f.name}")

    # Report
    print(f"Validation: external_cash_prices.sample.json")
    print(f"  Schema version: {sv}")
    print(f"  Observations: {len(obs)}")
    print(f"  Sources in product: {len(sources_list)}")
    print()

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  {w}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("  All checks passed.")


if __name__ == "__main__":
    validate()
