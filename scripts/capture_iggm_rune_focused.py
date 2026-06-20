#!/usr/bin/env python3
"""
capture_iggm_rune_focused.py — Targeted IGGM capture for segment-aware rune prices.

Navigates the IGGM D2R items page, tries to identify segment filters,
and captures the most specific rune-listing view available.

One page only. No login. No pagination. Max 5 minutes.
"""

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from camoufox.sync_api import Camoufox

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "research" / "sources" / "captures" / "iggm_2026-06-20_runes-focused"


def capture():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    meta = {
        "captured_at": ts,
        "target_url": "https://www.iggm.com/d2-resurrected-items",
        "final_url": "",
        "capture_method": "camoufox headless sync_api + DOM navigation",
        "page_title": "",
        "page_rendered": False,
        "login_required": False,
        "selected_filters": {},
        "detected_platform": None,
        "detected_ladder": None,
        "detected_hardcore": None,
        "detected_softcore": None,
        "detected_season": None,
        "visible_listings_found": 0,
        "price_samples": [],
        "navigation_attempts": [],
        "notes": [],
    }

    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})

        # Step 1: Load the D2R items page
        print("1. Loading IGGM D2R items page...")
        page.goto("https://www.iggm.com/d2-resurrected-items", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(5000)
        meta["final_url"] = page.url
        meta["page_title"] = page.title()

        # Step 2: Detect and try filter navigation
        print("2. Inspecting page for segment filters...")
        body_text = (page.inner_text("body") or "").lower()
        html_content = page.content()

        # Check for ladder/non-ladder/SC/HC/ROTW/PC filters
        filter_keywords = {
            "ladder": r'\bladder\b',
            "non-ladder": r'\bnon[\s-]?ladder\b',
            "softcore": r'\bsoftcore\b',
            "hardcore": r'\bhardcore\b',
            "rotw": r'\brotw\b',
            "pc": r'\bpc\b',
            "xbox": r'\bxbox\b',
            "switch": r'\bswitch\b',
            "playstation": r'\bplaystation\b',
            "season": r'\bseason\b',
        }
        for label, pat in filter_keywords.items():
            if re.search(pat, body_text, re.I):
                meta["detected_filters_present"] = meta.get("detected_filters_present", [])
                meta["detected_filters_present"].append(label)

        # Step 3: Look for a "Runes" link/category and try to click it
        print("3. Looking for runes navigation...")
        runes_clicked = False
        for selector in [
            "a[href*='rune']", "a[href*='Rune']",
            "a:has-text('Rune')", "a:has-text('rune')",
            "[class*='rune'] a", "[class*='Rune'] a",
            "a[href*='runes']", "nav a",
        ]:
            try:
                links = page.query_selector_all(selector)
                for link in links[:5]:
                    try:
                        text = (link.inner_text() or "").lower()
                        href = (link.get_attribute("href") or "").lower()
                        if "rune" in text or "rune" in href:
                            print(f"  Found rune link: text='{text[:40]}' href='{href[:60]}'")
                            link.click()
                            page.wait_for_timeout(4000)
                            runes_clicked = True
                            meta["navigation_attempts"].append(f"Clicked rune link: {text}")
                            break
                    except Exception as e:
                        meta["navigation_attempts"].append(f"Error clicking link: {e}")
                if runes_clicked:
                    break
            except Exception:
                continue

        if not runes_clicked:
            meta["notes"].append("No dedicated runes link found — using current page")

        # Step 4: Try to detect and interact with segment filter toggles
        print("4. Inspecting segment filters...")
        body_text2 = (page.inner_text("body") or "").lower()
        meta["final_url"] = page.url

        # Detect current filter state from page text
        for label, pat in [
            ("ladder", r'\bladder\b'), ("non_ladder", r'\bnon[\s-]ladder\b'),
            ("softcore", r'\bsoftcore\b'), ("hardcore", r'\bhardcore\b'),
            ("rotw", r'\brotw\b'), ("pc", r'\bpc\b'),
            ("xbox", r'\bxbox\b'), ("season", r'\bseason\b'),
        ]:
            if re.search(pat, body_text2, re.I):
                meta["selected_filters"][label] = True

        # Detect platform
        if meta["selected_filters"].get("pc"):
            meta["detected_platform"] = "pc"
        elif meta["selected_filters"].get("xbox"):
            meta["detected_platform"] = "xbox"
        if meta["selected_filters"].get("ladder"):
            meta["detected_ladder"] = True
        if meta["selected_filters"].get("non_ladder"):
            meta["detected_ladder"] = False
        if meta["selected_filters"].get("hardcore"):
            meta["detected_hardcore"] = True
            meta["detected_softcore"] = False
        if meta["selected_filters"].get("softcore"):
            meta["detected_softcore"] = True
            meta["detected_hardcore"] = False
        if meta["selected_filters"].get("rotw"):
            meta["detected_season"] = "ROTW"
        if meta["selected_filters"].get("season"):
            if not meta["detected_season"]:
                meta["detected_season"] = "present (specific season unknown)"

        # Step 5: Wait for rendering, then capture
        page.wait_for_timeout(3000)

        # Screenshot
        page.screenshot(path=str(OUT_DIR / "screenshot.png"), full_page=True)
        meta["page_rendered"] = True

        # Save HTML
        html_final = page.content()
        with open(OUT_DIR / "page.html", "w", encoding="utf-8") as f:
            f.write(html_final)

        # Extract prices
        price_spans = re.findall(r'<span\s+class="price"\s+lkr="([\d.]+)"', html_final)
        meta["price_samples"] = sorted(set(price_spans), key=float)[:10]

        # Count item-title elements (rune listings)
        titles = re.findall(r'<p\s+class="item-title">([^<]+)</p>', html_final)
        meta["visible_listings_found"] = len(titles)

        meta["notes"].append(f"Rune listings found: {len(titles)}")
        meta["notes"].append(f"Price elements found: {len(price_spans)}")
        meta["notes"].append(f"Page text length: {len(body_text2)} chars")

        # Save listing_samples
        listing_texts = []
        for sel in ["[class*='item-title']", "[class*='item-price']", "[class*='item']"]:
            els = page.query_selector_all(sel)
            for el in els[:40]:
                try:
                    t = (el.inner_text() or "").strip()
                    if t:
                        listing_texts.append(t[:200])
                except:
                    pass
        with open(OUT_DIR / "listing_samples.json", "w") as f:
            json.dump(listing_texts[:40], f, indent=2)

        # Network summary
        apis = list(set(re.findall(r'(https?://[^"\'<> ]*(?:api|graphql|rest|v[1-9]/|assets[^"\']*\.json)[^"\'<> ]*)', html_final, re.I)))[:10]
        with open(OUT_DIR / "network_summary.json", "w") as f:
            json.dump({"source_url": meta["final_url"], "captured_at": ts, "har_available": False, "api_endpoints_found": apis}, f, indent=2)

        # Write metadata
        with open(OUT_DIR / "metadata.json", "w") as f:
            json.dump(meta, f, indent=2, default=str)

        # Write source_review
        with open(OUT_DIR / "source_review.md", "w") as f:
            f.write("# IGGM Runes-Focused Capture\n\n")
            f.write(f"Captured: {ts}\n\n")
            f.write(f"## Segment Context\n\n")
            f.write(f"- Platform: {meta['detected_platform'] or 'not detected'}\n")
            f.write(f"- Ladder: {meta['detected_ladder']}\n")
            f.write(f"- Hardcore: {meta['detected_hardcore']}\n")
            f.write(f"- Softcore: {meta['detected_softcore']}\n")
            f.write(f"- Season/Ruleset: {meta['detected_season'] or 'not detected'}\n")
            f.write(f"- Filters present: {meta.get('detected_filters_present', [])}\n\n")
            f.write(f"## Prices\n\n")
            f.write(f"- Rune listings: {len(titles)}\n")
            f.write(f"- Price elements: {len(price_spans)}\n")
            f.write(f"- Sample prices: {', '.join(meta['price_samples'][:5])}\n\n")
            f.write(f"## Navigation\n\n")
            for a in meta.get("navigation_attempts", []):
                f.write(f"- {a}\n")
            f.write(f"\n## Verdict\n\n")
            if meta.get("detected_platform") or meta.get("detected_ladder") is not None:
                f.write("Segment context detected — confidence can be improved.\n")
            else:
                f.write("Segment context ambiguous — no explicit filter labels found.\n")

        print(f"\nResults:")
        print(f"  Final URL: {meta['final_url']}")
        print(f"  Platform: {meta['detected_platform']}")
        print(f"  Ladder: {meta['detected_ladder']}")
        print(f"  Hardcore: {meta['detected_hardcore']}")
        print(f"  Softcore: {meta['detected_softcore']}")
        print(f"  Season: {meta['detected_season']}")
        print(f"  Rune titles: {len(titles)}")
        print(f"  Prices: {len(price_spans)}")
        meta["elapsed_seconds"] = time.time() - start_time
        return meta


if __name__ == "__main__":
    global start_time
    start_time = time.time()
    result = capture()
    elapsed = time.time() - start_time
    print(f"Elapsed: {elapsed:.0f}s")
