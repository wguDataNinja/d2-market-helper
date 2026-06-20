#!/usr/bin/env python3
"""
parse_diablo2io_sold_search_offline.py — Multi-fixture research parser for
Diablo2.io Sold search results.

Reads saved rendered.html fixtures from diablo2.io sold-search captures and
extracts visible SOLD trade rows. Supports parsing multiple item fixtures in
one run via --items flag. Output is research-only — every row gets
use_in_model=false.

Usage:
  python scripts/parse_diablo2io_sold_search_offline.py
  python scripts/parse_diablo2io_sold_search_offline.py --item jah
  python scripts/parse_diablo2io_sold_search_offline.py --items jah,ber,sur

No network access. Works from saved artifacts only.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

ITEM_CONFIG = {
    "jah": {"name": "Jah Rune", "id": 43, "slug": "jah"},
    "ber": {"name": "Ber Rune", "id": 45, "slug": "ber"},
    "sur": {"name": "Sur Rune", "id": 47, "slug": "sur"},
    "lo":  {"name": "Lo Rune",  "id": 48, "slug": "lo"},
    "ohm": {"name": "Ohm Rune", "id": 49, "slug": "ohm"},
    "vex": {"name": "Vex Rune", "id": 50, "slug": "vex"},
    "gul": {"name": "Gul Rune", "id": 51, "slug": "gul"},
    "ist": {"name": "Ist Rune", "id": 52, "slug": "ist"},
    "mal": {"name": "Mal Rune", "id": 53, "slug": "mal"},
    "cham":{"name": "Cham Rune","id": 1330, "slug": "cham"},
}

FIXTURE_DIR = ROOT_DIR / "research" / "sources" / "captures" / "diablo2io"
OUTPUT_DIR = ROOT_DIR / "data" / "research"
COMBINED_OUTPUT = OUTPUT_DIR / "diablo2io_sold_rune_trades.sample.json"
MISSING_HTML_WARNING = "fixture file not found"

TRADE_SIDE_MAP = {
    "Want to Buy": "WTB",
    "Want to Sell": "WTS",
    "want to buy": "WTB",
    "want to sell": "WTS",
}

ITEM_NAME_MAP = {
    "runeJo_sicon": "Jah Rune",
    "runeBer_sicon": "Ber Rune",
    "runeSur_sicon": "Sur Rune",
    "runeLo_sicon": "Lo Rune",
    "runeOhm_sicon": "Ohm Rune",
    "runeVex_sicon": "Vex Rune",
    "runeGul_sicon": "Gul Rune",
    "runeMal_sicon": "Mal Rune",
    "runeIst_sicon": "Ist Rune",
    "runeCham_sicon": "Cham Rune",
    "runeZod_sicon": "Zod Rune",
    "runeJah_sicon": "Jah Rune",
}

ITEM_ID_MAP = {
    "Jah Rune": 43,
    "Ber Rune": 45,
    "Sur Rune": 47,
    "Lo Rune": 48,
    "Ohm Rune": 49,
    "Vex Rune": 50,
    "Gul Rune": 51,
    "Ist Rune": 52,
    "Mal Rune": 53,
    "Cham Rune": 1330,
}

ITEM_ICON_MAP = {v: k for k, v in ITEM_NAME_MAP.items()}

RUNE_NAMES = {
    "Ist", "Mal", "Gul", "Vex", "Ohm", "Lo", "Sur", "Ber", "Jah",
    "Cham", "Zod", "Pul", "Um", "Lem", "Ko", "Fal", "Lum", "Io",
    "Hel", "Dol", "Shael", "Sol", "Amn", "Thul", "Ort", "Ral",
    "Tal", "Eth", "Ith", "El", "Eld", "Tir", "Nef",
}

RUNES_SORTED = sorted(RUNE_NAMES, key=len, reverse=True)

# --- Rune registry lookup ---

def load_rune_registry():
    registry_path = ROOT_DIR / "data" / "rune_registry.json"
    with open(registry_path, "r") as f:
        entries = json.load(f)
    short_name_map = {}
    for entry in entries:
        short_name = entry["short_name"]
        short_name_map[short_name] = {
            "normalized_item_name": entry["name"],
            "rune_order": entry["id"],
        }
        for alias in entry.get("names", {}).values():
            if alias not in short_name_map:
                short_name_map[alias] = {
                    "normalized_item_name": entry["name"],
                    "rune_order": entry["id"],
                }
    return short_name_map


def enrich_consideration(consideration, rune_registry):
    if not consideration:
        return consideration
    enriched = []
    for c in consideration:
        item_name = c["item"]
        entry = rune_registry.get(item_name)
        if entry:
            enriched.append({
                "item": item_name,
                "quantity": c["quantity"],
                "normalized_item_name": entry["normalized_item_name"],
                "rune_order": entry["rune_order"],
            })
        else:
            enriched.append({
                "item": item_name,
                "quantity": c["quantity"],
            })
    return enriched


# --- HTML extraction ---

def extract_containers(html):
    pattern = r'<div class="zf-container zf-container-trade\s*">(.*?)</div>\s*<!-- container -->'
    return re.findall(pattern, html, re.DOTALL)


def extract_side(container):
    m = re.search(
        r'class="z-bone z-trusty z-trusty-wtbs[^"]*"\s*(?:title="([^"]+)")',
        container,
    )
    if m:
        title = m.group(1)
        return TRADE_SIDE_MAP.get(title, title)
    return "unknown"


def is_sold(container):
    return 'z-trusty-sold' in container


def extract_quantity(container):
    m = re.search(
        r'<span class="z-blue" title="Quantity">(\d+)</span>',
        container,
    )
    if m:
        return int(m.group(1))
    return 1


def extract_target_item(container):
    for icon_name, item_name in ITEM_NAME_MAP.items():
        if icon_name in container:
            return item_name
    m = re.search(r'class="z-trade-mini-icon\s*"[^>]*src="[^"]*/(\w+\.\w+)', container)
    if m:
        src = m.group(1)
        name = ITEM_NAME_MAP.get(src)
        if name:
            return name
    return "unknown"


def extract_description(container):
    m = re.search(
        r'<span class="z-inline-trade-desc">.*?<t>(.*?)</t>',
        container,
        re.DOTALL,
    )
    if m:
        text = m.group(1).strip()
        text = re.sub(r'<br\s*/?>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    return ""


def extract_sale_line(container):
    result = {}

    m = re.search(
        r'<i class="fas fa-check z-ic z-smaller"></i>\s*Sold\s*'
        r'<time[^>]*>.*?<span class="z-relative-date"[^>]*title="([^"]*)">'
        r'([^<]+)</span>',
        container,
        re.DOTALL,
    )
    if m:
        result["sold_timestamp"] = m.group(1)
        result["sold_relative"] = m.group(2).strip()

    m_seller = re.search(
        r'Sold[^<]*<time[^>]*>.*?</time>\s*by\s*<a[^>]*>([^<]+)</a>',
        container,
        re.DOTALL,
    )
    if m_seller:
        result["seller"] = m_seller.group(1).strip()

    m_buyer = re.search(
        r'to\s*<a[^>]*class="z-uniques-title"[^>]*>([^<]+)</a>',
        container,
    )
    if m_buyer:
        result["buyer"] = m_buyer.group(1).strip()

    consideration = []
    for m_item in re.finditer(
        r'<span class="z-blue">(\d+)</span>\s*'
        r'.*?<a[^>]*data-href="/ajax\.php\?var=\d+"[^>]*>.*?'
        r'</div>\s*([^<]+)</a>',
        container,
        re.DOTALL,
    ):
        qty = int(m_item.group(1))
        item_name = m_item.group(2).strip()
        consideration.append({"item": item_name, "quantity": qty})

    if consideration:
        result["consideration"] = consideration

    m_views = re.search(
        r'<i class="fas fa-eye"[^>]*></i>\s*(\d+)',
        container,
    )
    if m_views:
        result["views"] = int(m_views.group(1))

    m_offers = re.search(
        r'<i class="fas fa-comment"[^>]*></i>\s*(\d+)',
        container,
    )
    if m_offers:
        result["offers"] = int(m_offers.group(1))

    return result


def extract_segment(container):
    seg = {
        "platform": "unknown",
        "ladder": "unknown",
        "hardcore": "unknown",
        "region": "unknown",
        "ruleset": "unknown",
    }

    if "zi-nonladder" in container:
        seg["ladder"] = "non_ladder"
    elif "zi-ladder" in container:
        seg["ladder"] = "ladder"

    if "zi-softcore" in container:
        seg["hardcore"] = False
    elif "zi-hardcore" in container:
        seg["hardcore"] = True

    if "zi-pc" in container:
        seg["platform"] = "pc"

    if "zi-americas" in container:
        seg["region"] = "americas"
    elif "zi-europe" in container:
        seg["region"] = "europe"

    if "zi-tinylogrotw" in container:
        seg["ruleset"] = "rotw"

    confidence = "low"
    known_count = sum(1 for v in seg.values() if v not in ("unknown", None, False))
    if known_count >= 3:
        confidence = "medium"
    if known_count >= 5:
        confidence = "high"

    return seg, confidence


def extract_raw_title(container):
    title_parts = []
    side = extract_side(container)
    if side != "unknown":
        title_parts.append(side)
    title_parts.append("SOLD")
    qty = extract_quantity(container)
    if qty > 1:
        title_parts.append(str(qty))
    item = extract_target_item(container)
    if item != "unknown":
        title_parts.append(item.split(" ")[0])
    return " ".join(title_parts)


def extract_raw_sale_line(container, sale_data):
    parts = ["Sold"]
    if "sold_relative" in sale_data:
        parts.append(sale_data["sold_relative"])
    if "sold_timestamp" in sale_data:
        parts.append(f"({sale_data['sold_timestamp']})")
    if "seller" in sale_data:
        parts.append(f"by {sale_data['seller']}")
    if "buyer" in sale_data:
        parts.append(f"to {sale_data['buyer']}")
    if "consideration" in sale_data:
        for c in sale_data["consideration"]:
            parts.append("for")
            parts.append(str(c["quantity"]))
            parts.append(c["item"])
    elif "consideration" not in sale_data:
        if "consideration" not in sale_data:
            pass

    return " ".join(parts)


def classify_parse(target_item, consideration, description, side, quantity):
    if not consideration:
        if description:
            return "description_only_consideration"
        return "missing_consideration"

    total_items = sum(c.get("quantity", 1) for c in consideration)
    non_rune = [c["item"] for c in consideration if c["item"] not in RUNE_NAMES]

    if non_rune:
        return "non_rune_price"

    if quantity > 1:
        return "quantity_bundle"

    if len(consideration) == 1:
        return "clean_single_rune"
    elif len(consideration) > 1:
        return "clean_multi_rune"

    return "parse_failed"


def build_dedupe_key(obs):
    target_id = obs.get("target_item_id", "none")
    seller = obs.get("seller", "none") or "null"
    buyer = obs.get("buyer", "none") or "null"
    raw_line = obs.get("raw_sale_line", "none") or "none"
    cons_str = json.dumps(obs.get("consideration", []), sort_keys=True)
    return f"{obs['source']}|{target_id}|{raw_line}|{seller}|{buyer}|{cons_str}"


# --- Fixture parsing ---

def resolve_fixture_path(slug):
    p1 = FIXTURE_DIR / f"2026-06-20_{slug}_sold_search_p1" / "rendered.html"
    if p1.exists():
        return p1
    legacy = FIXTURE_DIR / f"2026-06-20_{slug}_sold_search" / "rendered.html"
    return legacy


def parse_fixture(item_cfg, rune_registry):
    slug = item_cfg["slug"]
    fixture_path = resolve_fixture_path(slug)
    per_item_output = OUTPUT_DIR / f"diablo2io_sold_{slug}_trades.sample.json"

    if not fixture_path.exists():
        print(f"  ⚠ WARNING: {MISSING_HTML_WARNING}: {fixture_path}")
        return []

    source_url = (
        f"https://diablo2.io/search.php?keywords={item_cfg['name'].split()[0]}"
        f"&terms=all&author=&fid%5B%5D=16&sc=0&sf=titleonly&sr=topics&sk=t"
        f"&sd=d&st=0&ch=300&t=0&submit=Search&activesold=1"
        f"&uitemid={item_cfg['id']}"
    )

    html = fixture_path.read_text(encoding="utf-8", errors="replace")
    containers = extract_containers(html)
    print(f"  Found {len(containers)} trade containers")

    observations = []
    parse_classes = {}
    skipped = 0

    for container in containers:
        if not is_sold(container):
            skipped += 1
            continue

        side = extract_side(container)
        quantity = extract_quantity(container)
        target_item = extract_target_item(container)
        description = extract_description(container)
        sale_data = extract_sale_line(container)
        segment, segment_confidence = extract_segment(container)

        consideration = sale_data.get("consideration", [])
        consideration = enrich_consideration(consideration, rune_registry)

        parse_class = classify_parse(
            target_item, consideration, description, side, quantity
        )

        parse_classes[parse_class] = parse_classes.get(parse_class, 0) + 1

        raw_title = extract_raw_title(container)
        raw_sale_line = extract_raw_sale_line(container, sale_data)

        fixture_rel = str(fixture_path.relative_to(ROOT_DIR))

        obs = {
            "source": "diablo2io",
            "surface": "sold_search",
            "evidence_class": "completed_player_trade_candidate",
            "source_url": source_url,
            "fixture_path": fixture_rel,
            "target_item": target_item,
            "target_item_id": ITEM_ID_MAP.get(target_item, None),
            "target_quantity": quantity,
            "trade_side": side,
            "segment": segment,
            "segment_confidence": segment_confidence,
            "seller": sale_data.get("seller", None),
            "buyer": sale_data.get("buyer", None),
            "sold_at_relative": sale_data.get("sold_relative", None),
            "sold_timestamp": sale_data.get("sold_timestamp", None),
            "consideration": consideration if consideration else None,
            "raw_title": raw_title,
            "raw_description": description if description else None,
            "raw_sale_line": raw_sale_line if raw_sale_line != "Sold" else None,
            "views": sale_data.get("views", None),
            "offers": sale_data.get("offers", None),
            "parse_class": parse_class,
            "use_in_model": False,
        }
        observations.append(obs)

    print(f"  Extracted {len(observations)} sold observations")
    print(f"  Skipped {skipped} non-sold containers")
    print(f"  Parse class distribution: {parse_classes}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(per_item_output, "w") as f:
        json.dump(observations, f, indent=2)
    print(f"  Per-fixture output: {per_item_output}")

    return observations


def main():
    parser = argparse.ArgumentParser(
        description="Parse diablo2.io sold-search fixture HTML."
    )
    parser.add_argument(
        "--item",
        default=None,
        choices=list(ITEM_CONFIG.keys()),
        help="Single target item slug (default: jah if --items not given)",
    )
    parser.add_argument(
        "--items",
        default=None,
        help="Comma-separated list of item slugs (e.g., jah,ber,sur)",
    )
    args = parser.parse_args()

    if args.item:
        slugs = [args.item]
    elif args.items:
        slugs = [s.strip() for s in args.items.split(",") if s.strip()]
    else:
        slugs = ["jah"]

    rune_registry = load_rune_registry()
    print(f"Loaded rune_registry with {len(rune_registry)} name mappings")
    print()

    all_observations = []
    parsed_slugs = []

    for slug in slugs:
        if slug not in ITEM_CONFIG:
            print(f"Unknown item slug: {slug}, skipping")
            continue
        item_cfg = ITEM_CONFIG[slug]
        fixture_path = resolve_fixture_path(slug)

        print("=" * 60)
        print(f"Item: {item_cfg['name']} (uitemid={item_cfg['id']})")
        print(f"Fixture: {fixture_path}")
        print()

        obs = parse_fixture(item_cfg, rune_registry)
        if obs:
            parsed_slugs.append(slug)
            all_observations.extend(obs)

        print()

    # --- Combined output ---
    if all_observations:
        COMBINED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with open(COMBINED_OUTPUT, "w") as f:
            json.dump(all_observations, f, indent=2)
        print(f"Combined output: {COMBINED_OUTPUT} ({len(all_observations)} rows)")
    else:
        print("No observations extracted — combined output not written.")
        return

    # --- Dedupe analysis ---
    dedupe_keys = {}
    for obs in all_observations:
        key = build_dedupe_key(obs)
        if key not in dedupe_keys:
            dedupe_keys[key] = []
        dedupe_keys[key].append(obs)

    duplicate_count = sum(len(v) - 1 for v in dedupe_keys.values() if len(v) > 1)
    unique_count = len(dedupe_keys)

    # --- Summary stats ---
    total = len(all_observations)
    parse_class_dist = {}
    for obs in all_observations:
        pc = obs["parse_class"]
        parse_class_dist[pc] = parse_class_dist.get(pc, 0) + 1

    clean_classes = {"clean_single_rune", "clean_multi_rune", "quantity_bundle"}
    excluded_classes = {"description_only_consideration", "missing_consideration", "parse_failed", "non_rune_price"}

    clean_count = sum(c for pc, c in parse_class_dist.items() if pc in clean_classes)
    excluded_count = sum(c for pc, c in parse_class_dist.items() if pc in excluded_classes)

    print()
    print("=" * 60)
    print("REPORT")
    print("=" * 60)
    print(f"Fixtures parsed: {', '.join(parsed_slugs)}")
    if not parsed_slugs:
        print("  (none)")
    print(f"Rows extracted per fixture:")
    for slug in parsed_slugs:
        count = sum(1 for o in all_observations if f"_{slug}_sold_search" in o.get("fixture_path", ""))
        print(f"  {slug}: {count}")
    print(f"Total combined rows: {total}")
    print(f"Clean row count: {clean_count} ({', '.join(sorted(clean_classes & set(parse_class_dist.keys())))})")
    print(f"Excluded row count: {excluded_count} ({', '.join(sorted(excluded_classes & set(parse_class_dist.keys())))})")
    print(f"Parse class distribution: {json.dumps(parse_class_dist, sort_keys=True)}")
    print(f"Dedupe keys: {unique_count} unique, {duplicate_count} duplicates")
    if duplicate_count > 0:
        print("  Duplicate details:")
        for key, obs_list in dedupe_keys.items():
            if len(obs_list) > 1:
                print(f"    Key: {key[:80]}... ({len(obs_list)} occurrences)")
    print()
    print("All rows have use_in_model=false — research only.")
    print("Done.")


if __name__ == "__main__":
    main()
