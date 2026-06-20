#!/usr/bin/env python3
"""
parse_iggm_offline.py — Extract D2R rune cash prices from captured IGGM rendered HTML.

Usage:
  python scripts/parse_iggm_offline.py                              # use default (browser-smoke)
  python scripts/parse_iggm_offline.py --input-dir <capture_dir>     # use specific capture dir

Input: research/sources/captures/iggm_*/page.html
Output: data/external/iggm_cash_prices.json
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ARTIFACT_DIR = ROOT_DIR / "research" / "sources" / "captures" / "iggm_2026-06-20_browser-smoke"
OUTPUT = ROOT_DIR / "data" / "external" / "iggm_cash_prices.json"

ITEM_SLUG_MAP = {
    "zod": "zod_rune", "cham": "cham_rune", "jah": "jah_rune", "ber": "ber_rune",
    "sur": "sur_rune", "lo": "lo_rune", "ohm": "ohm_rune", "vex": "vex_rune",
    "gul": "gul_rune", "ist": "ist_rune", "mal": "mal_rune", "um": "um_rune",
    "pul": "pul_rune", "lem": "lem_rune", "ko": "ko_rune", "fal": "fal_rune",
    "hel": "hel_rune", "io": "io_rune", "lum": "lum_rune", "eth": "eth_rune",
    "ith": "ith_rune", "dol": "dol_rune", "shael": "shael_rune", "sol": "sol_rune",
    "ort": "ort_rune", "ral": "ral_rune", "thul": "thul_rune", "amn": "amn_rune",
    "tal": "tal_rune", "nef": "nef_rune", "eld": "eld_rune", "el": "el_rune",
}

RUNES_LIST = list(ITEM_SLUG_MAP.keys())


def parse(input_dir: Path):
    input_html = input_dir / "page.html"
    if not input_html.exists():
        print(f"ERROR: artifact not found: {input_html}")
        return

    with open(input_html, "r", encoding="utf-8") as f:
        html = f.read()

    # Try to read metadata for segment context
    segment_confidence = "low"
    platform = None
    ladder = None
    hardcore = None
    softcore = None
    season = None
    parser_notes = ""

    meta_path = input_dir / "metadata.json"
    if meta_path.exists():
        try:
            with open(meta_path) as f:
                md = json.load(f)
            dp = md.get("detected_platform")
            dl = md.get("detected_ladder")
            dh = md.get("detected_hardcore")
            ds = md.get("detected_softcore")
            dsn = md.get("detected_season")

            if dp:
                platform = dp
            if dl is not None:
                ladder = dl
            if dh is not None:
                hardcore = dh
            if ds is not None:
                softcore = ds
            if dsn:
                season = dsn

            if platform and ladder is not None and hardcore is not None:
                segment_confidence = "high"
                parser_notes = (
                    f"Segment context from browser capture metadata: "
                    f"platform={platform}, ladder={ladder}, hardcore={hardcore}, "
                    f"softcore={softcore}, season={season}. "
                    f"Extracted from <span class='price' lkr='...'> attribute."
                )
            elif platform or ladder is not None:
                segment_confidence = "medium"
                parser_notes = (
                    f"Partial segment context from browser capture metadata: "
                    f"platform={platform}, ladder={ladder}, hardcore={hardcore}, "
                    f"softcore={softcore}, season={season}. "
                    f"Some dimensions unknown."
                )
        except Exception:
            pass

    if not parser_notes:
        parser_notes = (
            "No segment metadata available. Price from IGGM browser-captured rendered HTML. "
            "Extracted from <span class='price' lkr='...'> attribute. "
            "Segment confidence defaulting to low."
        )

    observations = []
    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    title_pattern = re.compile(r'<p\s+class="item-title">([^<]+)</p>')
    price_pattern = re.compile(r'<span\s+class="price"\s+lkr="([\d.]+)"')

    titles = list(title_pattern.finditer(html))
    prices = list(price_pattern.finditer(html))

    min_len = min(len(titles), len(prices))
    for i in range(min_len):
        title_text = titles[i].group(1).strip()
        price_str = prices[i].group(1)

        rune_m = re.match(r'(?i)\s*(' + '|'.join(RUNES_LIST) + r')\s*[–\-]', title_text)
        if not rune_m:
            continue

        rune_name = rune_m.group(1)
        rune_lower = rune_name.lower()
        item_slug = ITEM_SLUG_MAP.get(rune_lower, f"rune_{rune_lower}")

        try:
            price_val = round(float(price_str), 2)
        except ValueError:
            continue

        obs = {
            "source_slug": "iggm",
            "evidence_class": "cash_market_listing",
            "captured_at": captured_at,
            "source_artifact_path": str(input_html.resolve().relative_to(ROOT_DIR.resolve())),
            "source_url": "https://www.iggm.com/d2-resurrected-items",
            "item_name": rune_name.title(),
            "item_slug": item_slug,
            "item_category": "rune",
            "price": price_val,
            "currency": "USD",
            "quantity": 1,
            "unit_price": price_val,
            "platform": platform,
            "ladder": ladder,
            "hardcore": hardcore,
            "softcore": softcore,
            "season_or_ruleset": season,
            "segment_confidence": segment_confidence,
            "raw_text": title_text,
            "parser_notes": parser_notes,
        }
        observations.append(obs)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump({
            "schema_version": "0.1",
            "product": "iggm_cash_prices",
            "source_slug": "iggm",
            "generated_at": captured_at,
            "artifact_path": str(input_html.resolve().relative_to(ROOT_DIR.resolve())),
            "observation_count": len(observations),
            "observations": observations,
        }, f, indent=2)

    print(f"IGGM parser: {len(observations)} rune prices from {input_dir.name}")
    for obs in observations[:5]:
        print(f"  {obs['item_name']:8s} ${obs['price']:>5.2f}  seg={obs['segment_confidence']}")
    if len(observations) > 5:
        print(f"  ... and {len(observations)-5} more")
    return observations


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default=None, help="Path to capture directory containing page.html")
    args = parser.parse_args()

    if args.input_dir:
        input_dir = Path(args.input_dir)
    else:
        # Try focused capture first, fall back to browser-smoke
        focused = ROOT_DIR / "research" / "sources" / "captures" / "iggm_2026-06-20_runes-focused"
        if focused.exists():
            input_dir = focused
        else:
            input_dir = DEFAULT_ARTIFACT_DIR

    parse(input_dir)
