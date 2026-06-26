#!/usr/bin/env python3
"""parse_g2g_cash_prices.py — Parse G2G captured HTML into cash price observations.

Reads locally saved browser captures only. No network calls.
Output: data/external/g2g_cash_prices.json
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from lib import snapshot_io

ROOT_DIR = Path(__file__).resolve().parent.parent
CAPTURE_DIRS = [
    ROOT_DIR / "research" / "sources" / "captures" / "g2g_2026-06-20_lowest-price-runes",
    ROOT_DIR / "research" / "sources" / "captures" / "g2g_2026-06-20_cat-filtered-runes",
]
OUTPUT_PATH = ROOT_DIR / "data" / "external" / "g2g_cash_prices.json"
SOURCE_SLUG = "g2g"
SOURCE_URL = "https://www.g2g.com/categories/diablo-2-resurrected-item-for-sale"

# Segment path patterns
SEGMENT_RE = re.compile(
    r"(\w+)\s*-\s*([A-Za-z]+)\s*-\s*(Ladder|NonLadder)\s*-\s*(SC|HC)"
)
RUNE_RE = re.compile(r"Runes:\d+#\s*([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+from")
PRICE_RE = re.compile(r"from\s+([\d.]+)\s+USD")
OFFERS_RE = re.compile(r"(\d+)\s+offers?")


def parse_g2g_listings(html: str) -> list[dict]:
    """Extract listing data from G2G captured HTML."""
    # Find all offer/group listing links
    links = re.findall(
        r'<a[^>]*href="/categories/diablo-2-resurrected-item-for-sale/offer/group[^"]*"[^>]*>.*?</a>',
        html,
        re.DOTALL,
    )
    results = []
    seen = set()

    for link in links:
        text = re.sub(r"<[^>]+>", " ", link)
        text = re.sub(r"\s+", " ", text).strip()
        if not text or text in seen:
            continue
        seen.add(text)

        # Parse segment path
        seg_match = SEGMENT_RE.search(text)
        if not seg_match:
            continue

        plat_raw, ruleset_raw, ladder_raw, mode_raw = seg_match.groups()

        # Parse rune name
        rune_match = RUNE_RE.search(text)
        if not rune_match:
            continue

        rune_name = rune_match.group(1).strip()

        # Parse price
        price_match = PRICE_RE.search(text)
        if not price_match:
            continue
        price_usd = float(price_match.group(1))

        # Parse offer count
        offers_match = OFFERS_RE.search(text)
        offer_count = int(offers_match.group(1)) if offers_match else None

        # Segment mapping
        platform = plat_raw.lower()
        ladder = ladder_raw == "Ladder"
        hardcore = mode_raw == "HC"

        # Segment slug: only map confidently when platform is PC
        seg_slug = None
        seg_confidence = "low"
        if platform == "pc":
            slug = f"pc_{'hc' if hardcore else 'sc'}_{'l' if ladder else 'nl'}"
            # All captured listings show "LoD" — this may be a G2G label for all
            # D2 content, not exclusive to Lord of Destruction. The category
            # URL targets D2R but listings use "LoD". Ambiguous.
            seg_slug = slug
            seg_confidence = "medium"

        results.append({
            "source_slug": SOURCE_SLUG,
            "evidence_class": "cash_listing",
            "item_name": rune_name,
            "item_slug": rune_name.lower().replace(" ", "_"),
            "item_type": "rune",
            "price": price_usd,
            "price_usd": price_usd,
            "price_cents": round(price_usd * 100),
            "price_type": "lowest_available_ask",
            "currency": "USD",
            "unit_price": price_usd,
            "quantity": 1,
            "platform": platform,
            "ladder": ladder,
            "hardcore": hardcore,
            "segment_slug": seg_slug,
            "segment_confidence": seg_confidence,
            "ruleset_label_raw": ruleset_raw,
            "use_in_model": False,
            "seller_offer_count": offer_count,
            "captured_at": "2026-06-20T02:31:00Z",
            "source_url": SOURCE_URL,
            "product_url": None,
            "raw_text": f"{seg_match.group(0)} > Runes > {rune_name}",
            "caveats": [
                "G2G: price is the lowest available unit ask from category page sorted lowest_price first.",
                "G2G: may be per-unit base price; pack/bulk discounts may differ.",
                "G2G: captured 2026-06-20 via Camoufox; prices may be stale.",
                "G2G: fees, minimum order thresholds, or delivery costs not included.",
            ],
            "parser_notes": (
                f"G2G captured listing: {text[:200]}. "
                f"All captured G2G listings use 'LoD' label — may be G2G-wide "
                f"naming convention, not guaranteed Lord of Destruction exclusivity."
            ),
        })

    return results


def main():
    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_observations = []
    seen_items = set()

    for cap_dir in CAPTURE_DIRS:
        html_path = cap_dir / "page.html"
        if not html_path.exists():
            print(f"  Skipping (not found): {cap_dir}")
            continue
        html = html_path.read_text(errors="replace")
        listings = parse_g2g_listings(html)
        for obs in listings:
            key = (obs["item_name"], obs["segment_slug"] or "none")
            if key not in seen_items:
                seen_items.add(key)
                all_observations.append(obs)

    # Count by segment
    seg_counts: dict[str, int] = {}
    for obs in all_observations:
        s = obs.get("segment_slug") or "none"
        seg_counts[s] = seg_counts.get(s, 0) + 1

    output = {
        "schema_version": "0.1",
        "product": "g2g_cash_prices",
        "source_slug": SOURCE_SLUG,
        "generated_at": captured_at,
        "product_generated_at": captured_at,
        "evidence_class": "cash_listing",
        "source_url": SOURCE_URL,
        "observation_count": len(all_observations),
        "segment_counts": seg_counts,
        "observations": all_observations,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    # Also write raw + normalized snapshots
    snapshot_io.write_raw_snapshot(output, f"cash/{SOURCE_SLUG}")
    snapshot_io.write_normalized_snapshot(all_observations, f"cash/{SOURCE_SLUG}")

    print(f"\nG2G Cash Parser")
    print(f"  Captures scanned: {len(CAPTURE_DIRS)}")
    print(f"  Observations extracted: {len(all_observations)}")
    for seg, cnt in sorted(seg_counts.items()):
        print(f"    {seg}: {cnt}")
    print(f"  Output: {OUTPUT_PATH}")

    # Price summary
    prices = [o["price_usd"] for o in all_observations if o["price_usd"]]
    if prices:
        print(f"  Price range: ${min(prices):.3f} – ${max(prices):.3f} USD")
        print(f"  Median price: ${sorted(prices)[len(prices)//2]:.3f} USD")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
