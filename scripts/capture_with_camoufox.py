#!/usr/bin/env python3
"""
capture_with_camoufox.py — One-shot Camoufox capture for any single URL.
Usage:
  /Users/buddy/projects/playwright_workbench/.venv/bin/python scripts/capture_with_camoufox.py <url> <output_dir>

Saves: page.html, screenshot.png, metadata.json, listing_samples.json, network_summary.json
"""

import json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
from camoufox.sync_api import Camoufox

REPO_ROOT = Path(__file__).resolve().parent.parent

def capture_url(target_url, out_dir):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Capturing: {target_url}")
    print(f"Output:    {out_path}")
    print(f"{'='*60}")

    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})

        result = {
            "captured_at": timestamp,
            "target_url": target_url,
            "final_url": "",
            "capture_method": "camoufox (headless, sync_api)",
            "page_title": "",
            "visible_listings_found": 0,
            "page_rendered": False,
            "login_required": False,
            "breadcrumb": [],
            "all_listing_texts": [],
            "notes": [],
        }

        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
            result["final_url"] = page.url
            page.wait_for_timeout(5000)

            page.screenshot(path=str(out_path / "screenshot.png"), full_page=True)
            html = page.content()
            with open(out_path / "page.html", "w", encoding="utf-8") as f:
                f.write(html)

            result["page_title"] = page.title()
            body_text = (page.inner_text("body") or "")
            result["page_body_snippet"] = body_text[:2000]

            for sel in [".breadcrumb", "[class*='breadcrumb']", "[class*='Breadcrumb']", "nav[aria-label*='breadcrumb']", "ol.breadcrumb"]:
                try:
                    el = page.query_selector(sel)
                    if el:
                        items = el.query_selector_all("a, li, span")
                        crumbs = [(it.inner_text() or "").strip() for it in items if (it.inner_text() or "").strip()]
                        if crumbs:
                            result["breadcrumb"] = crumbs
                            break
                except Exception:
                    continue

            try:
                h1 = page.query_selector("h1")
                if h1:
                    result["title_h1"] = (h1.inner_text() or "").strip()
            except Exception:
                pass

            for sel in ["[class*='card']", "[class*='listing']", "[class*='product']", "[class*='item']", "tr", "[class*='offer']"]:
                cards = page.query_selector_all(sel)
                if len(cards) > 1:
                    texts = []
                    for c in cards[:20]:
                        try:
                            t = (c.inner_text() or "").strip()
                            if t:
                                texts.append(t[:300])
                        except Exception:
                            continue
                    if texts:
                        result["all_listing_texts"] = texts[:20]
                        result["visible_listings_found"] = len(texts)
                    break

            result["page_rendered"] = True
            result["notes"].append(f"Page rendered OK — {len(body_text)} chars body text")

            if "sign in" in body_text.lower() and "log in" in body_text.lower() and len(body_text) < 500:
                result["login_required"] = True
                result["notes"].append("Login wall detected")

        except Exception as e:
            result["notes"].append(f"Error: {type(e).__name__}: {e}")
            print(f"  Error: {e}")

        with open(out_path / "metadata.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        with open(out_path / "listing_samples.json", "w") as f:
            json.dump(result.get("all_listing_texts", []), f, indent=2)
        with open(out_path / "network_summary.json", "w") as f:
            json.dump({
                "captured_at": timestamp,
                "notes": "Page source inspected for API endpoints.",
                "api_endpoints_found": list(set(re.findall(
                    r'(https?://[^"\'<> ]*(?:api|graphql|rest|v[1-9]/|assets[^"\']*\.json)[^"\'<> ]*)',
                    html, re.I
                )))[:10],
            }, f, indent=2)

        print(f"  Title:   {result['page_title'][:80]}")
        print(f"  Rendered: {result['page_rendered']}")
        print(f"  Login:    {result['login_required']}")
        print(f"  Breadcrumb: {result.get('breadcrumb',[])}")
        print(f"  Samples:  {len(result.get('all_listing_texts',[]))}")

        return result

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: capture_with_camoufox.py <url> <output_dir>")
        sys.exit(1)

    target_url = sys.argv[1]
    out_dir = sys.argv[2]
    start_time = time.time()

    result = capture_url(target_url, out_dir)
    elapsed = time.time() - start_time
    print(f"\nTotal: {elapsed:.1f}s")

    if elapsed > 180:
        print("WARNING: Exceeded 3 minute limit")
        sys.exit(1)
