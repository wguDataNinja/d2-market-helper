#!/usr/bin/env python3
"""
parse_d2stock_rss.py — Parse D2Stock RSS/XML feed into cash price observations.

Usage:
  python3 scripts/parse_d2stock_rss.py              # fetch live feed from https://d2stock.com/rss.xml
  python3 scripts/parse_d2stock_rss.py --offline     # use saved fixture at research/sources/captures/d2stock/2026-06-20_search_probe/rss_feed.xml

Output: data/external/d2stock_cash_prices.json
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request

ROOT_DIR = Path(__file__).resolve().parent.parent
FIXTURE_PATH = ROOT_DIR / "research" / "sources" / "captures" / "d2stock" / "2026-06-20_search_probe" / "rss_feed.xml"
OUTPUT_PATH = ROOT_DIR / "data" / "external" / "d2stock_cash_prices.json"
RUNE_REGISTRY_PATH = ROOT_DIR / "data" / "rune_registry.json"
FEED_URL = "https://d2stock.com/rss.xml"

NS = {"g": "http://base.google.com/ns/1.0"}

SEGMENT_MAP = {
    "Softcore Ladder RotW": {"ladder": True, "hardcore": False, "softcore": True},
    "Softcore Non-Ladder RotW": {"ladder": False, "hardcore": False, "softcore": True},
}


def load_rune_registry():
    with open(RUNE_REGISTRY_PATH) as f:
        return json.load(f)


def build_rune_lookup(registry):
    lookup = {}
    for entry in registry:
        short = entry["short_name"]
        name = entry["name"]
        cash = entry["names"]["cash"]
        lookup[short.lower()] = entry
        lookup[name.lower()] = entry
        lookup[cash.lower()] = entry
    return lookup


def parse_price(price_str):
    if not price_str:
        return None
    m = re.match(r"([\d.]+)\s+(\w+)", price_str.strip())
    if m:
        return float(m.group(1)), m.group(2)
    return None


def extract_segment_from_title(title):
    m = re.search(r"•\s*(.+)$", title)
    if m:
        return m.group(1).strip()
    return None


def parse_item(item, rune_lookup, captured_at):
    title_el = item.find("g:title", NS)
    price_el = item.find("g:price", NS)
    type_el = item.find("g:product_type", NS)
    link_el = item.find("g:link", NS)
    avail_el = item.find("g:availability", NS)
    id_el = item.find("g:id", NS)
    group_el = item.find("g:item_group_id", NS)

    if title_el is None or title_el.text is None:
        return None

    title = title_el.text
    product_type = type_el.text if type_el is not None else ""
    product_url = link_el.text if link_el is not None else None
    raw_price = price_el.text if price_el is not None else None
    availability = avail_el.text if avail_el is not None else None
    product_id = id_el.text if id_el is not None else None
    item_group_id = group_el.text if group_el is not None else None

    if not product_type or "Runes" not in product_type:
        return None

    parsed = parse_price(raw_price)
    if parsed is None:
        return None
    price_usd, currency = parsed

    segment_label = extract_segment_from_title(title)
    title_before_segment = title.split("•")[0].strip() if segment_label else title.strip()

    has_pack_prefix = "×" in title_before_segment

    if product_type == "Runes > Runewords":
        item_category = "bundle"
        rune_order = None
        clean_item_name = title_before_segment
        normalized_name = title_before_segment
    elif product_type == "Runes > Rune Packs" or has_pack_prefix:
        item_category = "bundle"
        rune_name = extract_rune_name_from_title(title_before_segment)
        matched = match_rune(rune_name, rune_lookup)
        if matched:
            rune_order = matched["id"]
            base_name = matched["short_name"]
            clean_item_name = f"10 × {base_name} Rune"
            normalized_name = f"10 × {base_name} Rune"
        else:
            rune_order = None
            clean_item_name = title_before_segment
            normalized_name = title_before_segment
    else:
        item_category = "rune"
        rune_name = extract_rune_name_from_title(title_before_segment)
        matched = match_rune(rune_name, rune_lookup)
        if matched:
            rune_order = matched["id"]
            clean_item_name = matched["name"]
            normalized_name = matched["name"]
        else:
            rune_order = None
            clean_item_name = title_before_segment
            normalized_name = title_before_segment

    quantity = 10 if has_pack_prefix else 1

    segment_info = SEGMENT_MAP.get(segment_label, {})
    is_in_stock = availability and "in stock" in availability.lower()

    caveats = []
    if segment_label:
        caveats.append(f"Segment extracted from feed title: {segment_label}")
    if item_category == "bundle" and has_pack_prefix:
        caveats.append("10-pack bundle — price is for 10 units of the rune")
    if item_category == "bundle" and not has_pack_prefix:
        caveats.append("Runeword bundle — contains multiple rune types; not a single-rune listing")
    if product_type == "Runes > Runewords":
        caveats.append("Runeword product — price is for the completed runeword, not individual runes")

    item_slug = product_url.rstrip("/").split("/")[-1] if product_url else None

    observation = {
        "source_slug": "d2stock",
        "evidence_class": "cash_market_listing",
        "captured_at": captured_at,
        "source_artifact_path": str(FIXTURE_PATH.relative_to(ROOT_DIR)),
        "source_url": FEED_URL,
        "product_url": product_url,
        "item_name": clean_item_name,
        "item_slug": item_slug,
        "item_category": item_category,
        "product_id": product_id,
        "product_slug": item_slug,
        "normalized_item_name": normalized_name,
        "rune_order": rune_order,
        "price": price_usd,
        "price_min_usd": price_usd,
        "price_max_usd": price_usd,
        "currency": currency,
        "quantity": quantity,
        "unit_price": price_usd / quantity if quantity > 1 else price_usd,
        "stock_status": availability,
        "is_in_stock": is_in_stock,
        "segment_terms": [],
        "variation_count": None,
        "platform": None,
        "ladder": segment_info.get("ladder"),
        "hardcore": segment_info.get("hardcore"),
        "softcore": segment_info.get("softcore"),
        "season_or_ruleset": None,
        "segment_confidence": "low",
        "base_price_scope": "unknown",
        "use_in_model": False,
        "raw_text": title,
        "caveats": caveats,
        "parser_notes": f"Extracted from Google Shopping RSS feed ({FEED_URL}). Title segment: {segment_label}. Product type: {product_type}.",
    }

    return observation


def extract_rune_name_from_title(title):
    m = re.match(r"(?:\d+\s*×\s*)?(\w+)\s+Rune", title)
    if m:
        return m.group(1)
    return None


def match_rune(name, rune_lookup):
    if name is None:
        return None
    return rune_lookup.get(name.lower())


def fetch_feed():
    req = Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as resp:
        return resp.read()


def load_fixture():
    with open(FIXTURE_PATH, "rb") as f:
        return f.read()


def get_captured_at():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(args):
    captured_at = args.captured_at or get_captured_at()

    if args.offline:
        if not FIXTURE_PATH.exists():
            print(f"ERROR: fixture not found: {FIXTURE_PATH}")
            sys.exit(1)
        raw = load_fixture()
        print(f"Using offline fixture: {FIXTURE_PATH}")
    else:
        print(f"Fetching live feed: {FEED_URL}")
        raw = fetch_feed()

    root = ET.fromstring(raw)
    items = root.findall(".//item")
    print(f"Total items in feed: {len(items)}")

    registry = load_rune_registry()
    rune_lookup = build_rune_lookup(registry)

    observations = []
    rune_count = 0
    bundle_count = 0
    other_count = 0

    for item in items:
        obs = parse_item(item, rune_lookup, captured_at)
        if obs is None:
            continue
        cat = obs["item_category"]
        if cat == "rune":
            rune_count += 1
        elif cat == "bundle":
            bundle_count += 1
        else:
            other_count += 1
        observations.append(obs)

    artifact_path = str(FIXTURE_PATH.relative_to(ROOT_DIR))

    output = {
        "schema_version": "0.1",
        "product": "d2stock_cash_prices",
        "source_slug": "d2stock",
        "generated_at": captured_at,
        "artifact_path": artifact_path,
        "total_products": len(observations),
        "rune_count": rune_count,
        "bundle_count": bundle_count,
        "observation_count": len(observations),
        "observations": observations,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWritten: {OUTPUT_PATH}")
    print(f"  Total observations: {len(observations)}")
    print(f"  Rune singles: {rune_count}")
    print(f"  Bundles (10-packs + runewords): {bundle_count}")

    return output


def main():
    parser = argparse.ArgumentParser(description="Parse D2Stock RSS feed into cash price observations")
    parser.add_argument("--offline", action="store_true", help="Use saved fixture instead of live feed")
    parser.add_argument("--captured-at", help="Override captured_at timestamp (ISO format)")
    args = parser.parse_args()
    parse(args)


if __name__ == "__main__":
    main()
