#!/usr/bin/env python3
"""
capture_g2g_preview.py — One-shot Camoufox capture for G2G D2R rune listings.

Usage:
  /Users/buddy/projects/playwright_workbench/.venv/bin/python scripts/capture_g2g_preview.py

Constraints:
  - one page only
  - no login
  - no pagination
  - no repeated refresh
  - max 5 minute runtime
  - discovery/capture only
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from camoufox.sync_api import Camoufox

TARGET_URL = (
    "https://www.g2g.com/categories/diablo-2-resurrected-item-for-sale"
    "?fa=7075ff24%3A2c21e727%7C7071deb3%3A4d2c8b55&sort=lowest_price"
)
REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "research" / "sources" / "captures" / "g2g_2026-06-20_lowest-price-runes"
MAX_SECONDS = 240  # 4 minutes safety margin


def capture():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out_dir = OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Target: {TARGET_URL}")
    print(f"Output: {out_dir}")
    print("Opening Camoufox...")

    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})

        final_url = ""
        rendered = False
        login_required = False
        visible_listings = 0
        listing_data = []
        api_calls = []
        filter_options = []
        selected_filters = []
        notes = []

        try:
            print("Navigating...")
            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=45000)
            final_url = page.url

            # Wait for potential JS render
            print("Waiting for render (8s settle)...")
            page.wait_for_timeout(3000)

            # Try to detect if blocked or login-walled
            page_text = (page.inner_text("body") or "").lower()
            page_title = page.title()

            if "just a moment" in page_text or "cloudflare" in page_text:
                notes.append("Cloudflare challenge detected")
                print("  Cloudflare challenge — page may be blocked")
            elif "sign in" in page_text and "log in" in page_text:
                login_required = True
                notes.append("Login wall detected")
                print("  Login wall detected")

            # Wait more for listings to render
            page.wait_for_timeout(5000)

            # Full page screenshot
            print("Taking screenshot...")
            page.screenshot(path=str(out_dir / "screenshot.png"), full_page=True)

            # Save rendered HTML
            print("Saving rendered HTML...")
            html_content = page.content()
            with open(out_dir / "page.html", "w", encoding="utf-8") as f:
                f.write(html_content)

            # Detect listing elements on G2G
            # G2G typically uses listing cards with product titles and prices
            print("Detecting listing elements...")

            # Try common G2G selectors for listing items
            listing_candidates = []
            for selector in [
                ".product-item", ".listing-item", ".card-item", "[class*='product']",
                "[class*='listing']", "[class*='card']", "li[class*='item']",
                "div[class*='Grid'] > div", "[data-testid*='product']",
                ".item-card", ".offer-card",
            ]:
                elements = page.query_selector_all(selector)
                if len(elements) > 1:
                    listing_candidates = elements
                    notes.append(f"Found {len(elements)} elements via '{selector}'")
                    print(f"  Selector '{selector}': {len(elements)} candidates")
                    break

            # Also try to find price patterns in the page
            price_spans = page.query_selector_all("[class*='price'], [class*='Price']")
            if price_spans:
                notes.append(f"Found {len(price_spans)} price elements")
                print(f"  Price elements: {len(price_spans)}")

            # Extract visible listings from DOM
            max_samples = 20
            for el in listing_candidates[:max_samples]:
                try:
                    title = (el.inner_text() or "")[:200]
                    if not title.strip():
                        continue
                    visible_listings += 1
                    html_snippet = el.inner_html()[:300]

                    # Try to extract price
                    price_text = ""
                    for price_sel in [".price", "[class*='price']", ".amount", ".cost"]:
                        price_el = el.query_selector(price_sel)
                        if price_el:
                            price_text = (price_el.inner_text() or "").strip()
                            break

                    listing_data.append({
                        "title": title[:150],
                        "item_name": "",
                        "price": price_text,
                        "currency": "USD",
                        "seller": "",
                        "stock": "",
                        "delivery_text": "",
                        "listing_url": "",
                        "raw_text_snippet": title[:200],
                        "html_snippet": html_snippet,
                    })
                except Exception:
                    continue

            if listing_data:
                rendered = True
                notes.append(f"{len(listing_data)} listings extracted from DOM")
            else:
                # Check if page rendered at all
                body_text = page.inner_text("body") or ""
                word_count = len(body_text.split())
                if word_count > 50:
                    rendered = True
                    notes.append(f"Page rendered ({word_count} words) but no structured listings found")
                    print(f"  Page text length: {word_count} words")
                else:
                    notes.append("Page did not render meaningful content")
                    print("  Page content too sparse")

            # Try to detect filter UI elements
            for filter_sel in [
                "select", "[class*='filter']", "[class*='Filter']",
                "[class*='dropdown']", "[class*='segment']",
                "[class*='ladder']", "[class*='hardcore']",
            ]:
                filter_els = page.query_selector_all(filter_sel)
                if len(filter_els) > 0:
                    for fe in filter_els[:5]:
                        try:
                            text = (fe.inner_text() or "").strip()[:100]
                            if text:
                                filter_options.append(text)
                        except Exception:
                            continue

            # Check for ladder/softcore/hardcore keywords in page
            page_text_lower = page_text
            if "ladder" in page_text_lower:
                selected_filters.append("ladder")
            if "non-ladder" in page_text_lower or "non ladder" in page_text_lower:
                selected_filters.append("non-ladder")
            if "softcore" in page_text_lower or "sc " in page_text_lower:
                selected_filters.append("softcore")
            if "hardcore" in page_text_lower or "hc " in page_text_lower:
                selected_filters.append("hardcore")
            if "pc" in page_text_lower and "playstation" not in page_text_lower and "xbox" not in page_text_lower:
                selected_filters.append("pc")

            # Detect API calls from page (HAR not captured, just note observations)
            # Check page source for API patterns
            page_source = page.content()
            import re
            api_patterns = re.findall(
                r'(https?://[^"\'<> ]*(?:api|graphql|rest|v[1-9]/)[^"\'<> ]*)',
                page_source, re.I
            )
            for ap in set(api_patterns[:10]):
                api_calls.append({
                    "url": ap,
                    "method": "GET (inferred from page source)",
                    "status": None,
                    "content_type": None,
                    "purpose": "Found in page source or JS bundle",
                })

            if api_calls:
                notes.append(f"{len(api_calls)} API-like URLs found in page source")

        except Exception as e:
            notes.append(f"Error during capture: {type(e).__name__}: {e}")
            print(f"  Error: {e}")

        # Build metadata and write artifacts
        meta = {
            "source": "g2g",
            "captured_at": timestamp,
            "target_url": TARGET_URL,
            "final_url": final_url,
            "capture_method": "camoufox (headless, sync_api)",
            "camoufox_version": "0.4.11 (from playwright_workbench venv)",
            "page_title": page.title(),
            "visible_listings_found": len(listing_data),
            "page_rendered": rendered,
            "login_required": login_required,
            "visible_filters": filter_options[:10],
            "selected_filters": selected_filters,
            "platform_ladder_hc_notes": (
                "G2G category page filtered to D2R runes, sorted lowest price. "
                "Segment filters (ladder, SC/HC) may not be visible at this URL. "
                "G2G typically uses server/region tabs rather than explicit ladder/SC/HC toggles."
            ),
            "notes": notes,
        }

        with open(out_dir / "metadata.json", "w") as f:
            json.dump(meta, f, indent=2)

        with open(out_dir / "listing_samples.json", "w") as f:
            json.dump(listing_data, f, indent=2)

        net_summary = {
            "source": "g2g",
            "captured_at": timestamp,
            "har_available": False,
            "api_endpoints_found": api_calls[:15],
            "notes": (
                "No HAR capture performed. API endpoints listed here were found "
                "by scanning page source for URL patterns. Full API traffic requires "
                "HAR capture or CDP session monitoring."
            ),
        }
        with open(out_dir / "network_summary.json", "w") as f:
            json.dump(net_summary, f, indent=2)

        print(f"\nDone. {len(listing_data)} listing samples extracted")
        print(f"Page rendered: {rendered}")
        print(f"Artifacts in: {out_dir}")
        return meta


if __name__ == "__main__":
    start = time.time()
    result = capture()
    elapsed = time.time() - start
    print(f"Elapsed: {elapsed:.1f}s")

    # Fail if over 5 minutes
    if elapsed > 300:
        print("WARNING: Exceeded 5 minute limit")
        sys.exit(1)
