#!/usr/bin/env python3
"""
capture_source_smoke.py — One-shot Camoufox smoke test for any source URL.

Usage:
  /Users/buddy/projects/playwright_workbench/.venv/bin/python scripts/capture_source_smoke.py <url> <output_dir>

One page only. No login. No pagination. Max 3 minutes.
Saves page.html, screenshot.png, metadata.json, listing_samples.json, network_summary.json.
"""

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from camoufox.sync_api import Camoufox

REPO_ROOT = Path(__file__).resolve().parent.parent


def capture(url, out_dir):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"\n>> {url}")
    print(f">> {out}")

    meta = {
        "source_slug": out.parent.name.split("_")[0] if "_" in out.name else out.name,
        "captured_at": ts,
        "target_url": url,
        "final_url": "",
        "capture_method": "camoufox headless sync_api",
        "page_title": "",
        "page_rendered": False,
        "login_required": False,
        "visible_listings_found": 0,
        "breadcrumb": [],
        "selected_filters": {},
        "price_samples": [],
        "notes": [],
        "error": None,
    }

    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            meta["final_url"] = page.url
            page.wait_for_timeout(6000)

            page.screenshot(path=str(out / "screenshot.png"), full_page=True)
            html = page.content()
            with open(out / "page.html", "w", encoding="utf-8") as f:
                f.write(html)

            meta["page_title"] = page.title()
            body = (page.inner_text("body") or "")
            meta["page_rendered"] = len(body) > 200

            # Detect login wall
            low = body.lower()
            if ("sign in" in low and "log in" in low) or "login" in low:
                meta["login_required"] = True

            # Breadcrumb
            for sel in [".breadcrumb", "[class*='breadcrumb']", "nav[aria-label*='breadcrumb']", ".q-breadcrumbs", "ol.breadcrumb"]:
                try:
                    el = page.query_selector(sel)
                    if el:
                        items = el.query_selector_all("li, span, a")
                        meta["breadcrumb"] = [ (it.inner_text() or "").strip() for it in items if (it.inner_text() or "").strip() ]
                        if meta["breadcrumb"]:
                            break
                except:
                    pass

            # Price-like patterns in page text
            prices = re.findall(r'\$\s?(\d+[\.\d,]+)', body)
            if prices:
                meta["price_samples"] = sorted(set(prices), key=lambda x: float(x.replace(",","")), reverse=True)[:10]

            # Listing cards
            texts = []
            for sel in ["[class*='card']", "[class*='listing']", "[class*='product']", "[class*='item']", "[class*='offer']", "tr", ".q-card"]:
                cards = page.query_selector_all(sel)
                if len(cards) >= 3:
                    for c in cards[:25]:
                        try:
                            t = (c.inner_text() or "").strip()
                            if t and len(t) > 20:
                                texts.append(t[:300])
                        except:
                            pass
                    if texts:
                        break
            meta["visible_listings_found"] = len(texts)

            # Segment/ladder/SC/HC keywords in body
            for kw in ["ladder", "non-ladder", "non ladder", "softcore", "hardcore", "sc ", "hc ", "season", "rotw", "pc ", "xbox", "playstation", "nintendo", "switch"]:
                if re.search(r'\b' + re.escape(kw) + r'\b', low):
                    meta["selected_filters"][kw] = True

            meta["notes"].append(f"Page text length: {len(body)} chars")

        except Exception as e:
            meta["error"] = f"{type(e).__name__}: {e}"
            meta["notes"].append(f"Error: {meta['error']}")

        # Write artifacts
        with open(out / "metadata.json", "w") as f:
            json.dump(meta, f, indent=2, default=str)
        with open(out / "listing_samples.json", "w") as f:
            json.dump(texts if texts else ["(no structured listings detected)"], f, indent=2)
        with open(out / "network_summary.json", "w") as f:
            apis = list(set(re.findall(r'(https?://[^"\'<> ]*(?:api|graphql|rest|v[1-9]/|assets[^"\']*\.json)[^"\'<> ]*)', html, re.I)))[:10]
            json.dump({"source_url": url, "captured_at": ts, "har_available": False, "api_endpoints_found": apis, "notes": "API patterns from page source scan. Full traffic requires HAR capture."}, f, indent=2)

        elapsed = time.time() - start_time
        print(f"  title={meta['page_title'][:60]} rendered={meta['page_rendered']} login={meta['login_required']} listings={meta['visible_listings_found']} prices={len(meta['price_samples'])} filters={dict((k,v) for k,v in meta['selected_filters'].items() if v)} elapsed={elapsed:.0f}s")
        return meta


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: capture_source_smoke.py <url> <output_dir>")
        sys.exit(1)
    global start_time
    start_time = time.time()
    result = capture(sys.argv[1], sys.argv[2])
    total = time.time() - start_time
    if total > 180:
        print(f"WARNING: exceeded 3 minutes ({total:.0f}s)")
    print()
