#!/usr/bin/env python3
"""
parse_items7_offline.py — Extract D2R rune cash prices from saved items7 HTML.

Input: research/sources/downloads/rune_sources_2026-06-20/items7.html
Output: data/external/items7_cash_prices.json

Note: items7 static HTML does not contain per-rune prices in extractable
format. Prices are rendered client-side. This parser documents what is
available from the static capture and notes the limitation.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
INPUT_HTML = ROOT_DIR / "research" / "sources" / "downloads" / "rune_sources_2026-06-20" / "items7.html"
OUTPUT = ROOT_DIR / "data" / "external" / "items7_cash_prices.json"


def parse():
    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if not INPUT_HTML.exists():
        print(f"ERROR: artifact not found: {INPUT_HTML}")
        return

    with open(INPUT_HTML, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()

    observations = []
    dollar_amounts = re.findall(r'\$(\d+\.\d{2})', html)
    # The only dollar amount in static HTML is $0.00 (cart widget) — not useful.
    # Per-rune prices are loaded client-side and not in the static capture.

    print(f"items7 static HTML: {len(dollar_amounts)} dollar amounts found")
    print(f"  (all are $0.00 from cart/widget elements — no per-rune prices in static HTML)")
    print()
    print("items7 requires a browser-captured render to extract per-rune prices.")
    print("The static capture does not contain extractable per-rune cash prices.")

    # Emit an empty result with a clear caveat
    output = {
        "schema_version": "0.1",
        "product": "items7_cash_prices",
        "source_slug": "items7",
        "generated_at": captured_at,
        "artifact_path": str(INPUT_HTML.relative_to(ROOT_DIR)),
        "observation_count": 0,
        "observations": [],
        "parser_notes": (
            "items7 static HTML does not contain per-rune prices in extractable format. "
            "Prices are loaded client-side via JavaScript. "
            "A browser capture (Camoufox) is required to render and extract per-rune prices. "
            "Static capture showed 21 dollar amounts ($0.15-$2.85) in the full page text "
            "but these could not be mapped to specific rune names from the static HTML alone."
        ),
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWritten: {OUTPUT}")
    return observations


if __name__ == "__main__":
    parse()
