#!/usr/bin/env python3
"""
capture_diablo2io_fixtures.py — Playwright Chromium capture for diablo2.io sold-search pages.
Skips Camoufox (Firefox crashes on diablo2.io page JS errors).

Usage:
  /Users/buddy/projects/playwright_workbench/.venv/bin/python scripts/capture_diablo2io_fixtures.py

Saves to: research/sources/captures/diablo2io/{slug}/
Artifacts: rendered.html, screenshot.png, metadata.json
"""

import json
import os
import re
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FIXTURES = [
    {
        "item": "Jah",
        "page": 1,
        "slug": "2026-06-20_jah_sold_search_p1",
        "url": "https://diablo2.io/search.php?keywords=Jah&terms=all&author=&fid%5B%5D=16&sc=0&sf=titleonly&sr=topics&sk=t&sd=d&st=0&ch=300&t=0&submit=Search&activesold=1&uitemid=43",
    },
    {
        "item": "Ber",
        "page": 1,
        "slug": "2026-06-20_ber_sold_search_p1",
        "url": "https://diablo2.io/search.php?keywords=Ber&terms=all&author=&fid%5B%5D=16&sc=0&sf=titleonly&sr=topics&sk=t&sd=d&st=0&ch=300&t=0&submit=Search&activesold=1&uitemid=45",
    },
    {
        "item": "Lo",
        "page": 1,
        "slug": "2026-06-20_lo_sold_search_p1",
        "url": "https://diablo2.io/search.php?keywords=Lo&terms=all&author=&fid%5B%5D=16&sc=0&sf=titleonly&sr=topics&sk=t&sd=d&st=0&ch=300&t=0&submit=Search&activesold=1&uitemid=48",
    },
    {
        "item": "Sur",
        "page": 1,
        "slug": "2026-06-20_sur_sold_search_p1",
        "url": "https://diablo2.io/search.php?keywords=Sur&terms=all&author=&fid%5B%5D=16&sc=0&sf=titleonly&sr=topics&sk=t&sd=d&st=0&ch=300&t=0&submit=Search&activesold=1&uitemid=47",
    },
]


def safe_capture(fixture):
    url = fixture["url"]
    out_path = REPO_ROOT / "research" / "sources" / "captures" / "diablo2io" / fixture["slug"]
    out_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    result = {
        "captured_at": timestamp,
        "target_url": url,
        "final_url": "",
        "item": fixture["item"],
        "page": fixture["page"],
        "capture_method": "playwright chromium (headless)",
        "page_title": "",
        "visible_trade_count": 0,
        "total_match_count": 0,
        "capture_success": False,
        "page_rendered": False,
        "login_required": False,
        "permission_denied": False,
        "notes": [],
        "row_count_estimate": 0,
    }

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        result["notes"].append("playwright not available in this venv")
        return False, result

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()

            # Suppress JS errors before page loads
            page.add_init_script("""
                window.addEventListener('error', function(e) {
                    e.preventDefault(); e.stopPropagation(); return true;
                }, true);
                window.addEventListener('unhandledrejection', function(e) {
                    e.preventDefault(); e.stopPropagation(); return true;
                }, true);
            """)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                result["notes"].append(f"goto error: {type(e).__name__}: {e}")

            result["final_url"] = page.url

            try:
                page.wait_for_timeout(7000)
            except Exception:
                pass

            # Screenshot
            try:
                page.screenshot(path=str(out_path / "screenshot.png"), full_page=True)
            except Exception as e:
                result["notes"].append(f"screenshot error: {e}")

            # HTML
            try:
                html = page.content()
                with open(out_path / "rendered.html", "w", encoding="utf-8") as f:
                    f.write(html)
            except Exception as e:
                result["notes"].append(f"content error: {e}")
                html = ""

            # Title
            try:
                result["page_title"] = page.title()
            except Exception:
                pass

            # Body text
            try:
                body_text = (page.inner_text("body") or "")
            except Exception:
                body_text = ""

            result["page_rendered"] = bool(body_text)

            # Checks
            body_lower = body_text.lower()
            if "not permitted" in body_lower:
                result["permission_denied"] = True
                result["notes"].append("PERMISSION DENIED — search system blocked by site")

            if "sign in" in body_lower and len(body_text) < 500:
                result["login_required"] = True
                result["notes"].append("Login wall detected")

            # Match count from body
            m = re.search(r'Found\s+(\d+)\s+matches?\s+for', body_text)
            if m:
                result["total_match_count"] = int(m.group(1))
                result["notes"].append(f"Match count: {m.group(1)}")

            # Visible trade count
            try:
                rows = page.query_selector_all("a[class*='z-trade'], div.post, div[class*='topic'], li[class*='post']")
                if rows:
                    result["visible_trade_count"] = len(rows)
                    result["notes"].append(f"Visible trade elements: {len(rows)}")
            except Exception:
                pass

            # Trade samples from body
            samples = []
            for line in body_text.split("\n"):
                s = line.strip()
                if s and ("Sold" in s or "WTS" in s or "WTB" in s):
                    samples.append(s[:200])
                    if len(samples) >= 15:
                        break
            result["trade_samples"] = samples

            result["row_count_estimate"] = result["total_match_count"] or result["visible_trade_count"]

            if html and result["page_rendered"] and not result["permission_denied"]:
                result["capture_success"] = True

            result["notes"].append(
                f"Done — {len(body_text)} chars body, {len(html)} chars HTML, "
                f"{len(samples)} trade samples"
            )

            browser.close()

    except Exception as e:
        result["notes"].append(f"Fatal: {type(e).__name__}: {e}")
        traceback.print_exc()

    try:
        with open(out_path / "metadata.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
    except Exception as e:
        print(f"  metadata write error: {e}")

    return result["capture_success"], result


def main():
    results = []
    for fixture in FIXTURES:
        slug = fixture["slug"]
        print(f"\n{'='*60}")
        print(f"Capturing: {fixture['item']} page {fixture['page']}  →  {slug}")
        print(f"{'='*60}")

        start = time.time()
        success, meta = safe_capture(fixture)
        elapsed = time.time() - start
        status = "OK" if success else "FAILED"
        print(f"  Status: {status} ({elapsed:.1f}s)")
        print(f"  Title:  {meta.get('page_title','N/A')[:80]}")
        print(f"  Matches: {meta.get('total_match_count','?')}")
        print(f"  Trades:  {meta.get('visible_trade_count','?')}")
        for n in meta.get("notes", [])[-2:]:
            print(f"  Note:   {n}")

        results.append({
            "slug": slug, "item": fixture["item"], "page": fixture["page"],
            "success": success,
            "match_count": meta.get("total_match_count", 0),
            "trade_count": meta.get("visible_trade_count", 0),
            "permission_denied": meta.get("permission_denied", False),
        })

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    total_rows = sum(r["match_count"] or r["trade_count"] for r in results)
    for r in results:
        icon = "✓" if r["success"] else "✗"
        pd = " [BLOCKED]" if r.get("permission_denied") else ""
        print(f"  {icon} {r['slug']}  ({r['item']} p{r['page']}) — {r['match_count']} matches, {r['trade_count']} trades{pd}")
    print(f"\n  Captured: {len(successful)}")
    print(f"  Failed:   {len(failed)}")
    print(f"  Rows:     {total_rows}")


if __name__ == "__main__":
    main()
