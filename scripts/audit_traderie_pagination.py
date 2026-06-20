#!/usr/bin/env python3
"""audit_traderie_pagination.py - Pagination/window audit for Traderie.

Fetches Jah Rune (pc_sc_nl) across up to 10 pages using nextPage cursor.
Saves all pages and analyzes pagination behavior, window limits, and
historical coverage.
"""

import json
import sys
import time
import cloudscraper
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "research" / "traderie_pagination_audit_jah_pc_sc_nl.sample.json"

JAH_ITEM_ID = 2552039455
URL = "https://traderie.com/api/diablo2resurrected/listings"
MAX_PAGES = 10
PAGE_DELAY_S = 2.5

BASE_PARAMS = {
    "completed": "true",
    "auction": "false",
    "prop_Platform": "PC",
    "prop_Mode": "softcore",
    "prop_Ladder": "false",
    "item": JAH_ITEM_ID,
}


def fetch_page(scraper, params, page_num):
    """Fetch one page; return (listings, nextPage, response_dict, meta) or None on error."""
    print(f"  Page {page_num}: GET {URL} params={ {k:v for k,v in params.items()} }")
    try:
        res = scraper.get(URL, params=params, timeout=15)
        meta = {
            "status_code": res.status_code,
            "elapsed_seconds": res.elapsed.total_seconds(),
            "headers": dict(res.headers),
        }
        if res.status_code != 200:
            print(f"  -> HTTP {res.status_code}")
            print(f"  -> Body[:500]: {res.text[:500]}")
            return None, meta
        raw = res.json()
        listings = raw.get("listings", [])
        if not isinstance(listings, list):
            print(f"  -> Warning: listings is {type(listings).__name__}, not list")
            listings = []
        next_page = raw.get("nextPage")
        print(f"  -> {len(listings)} listings, nextPage={next_page}, {res.elapsed.total_seconds():.2f}s")
        return {
            "page": page_num,
            "params": dict(params),
            "meta": meta,
            "listings_count": len(listings),
            "nextPage": next_page,
            "version": raw.get("version"),
            "listing_ids": [l.get("id") for l in listings if isinstance(l, dict)],
            "listings": listings,
        }, meta
    except Exception as e:
        print(f"  -> Exception: {e}")
        return None, {"error": str(e)}


def main():
    print("=" * 70)
    print("TRADERIE PAGINATION / WINDOW AUDIT")
    now = datetime.now(timezone.utc).isoformat()
    print(f"Started: {now}")
    print(f"Item: Jah Rune (id={JAH_ITEM_ID})  Segment: pc_sc_nl")
    print(f"Max pages: {MAX_PAGES}  Delay: {PAGE_DELAY_S}s")
    print("=" * 70)

    scraper = cloudscraper.create_scraper()
    pages_data = []
    params = dict(BASE_PARAMS)
    all_listing_ids = set()

    for page_num in range(1, MAX_PAGES + 1):
        result, meta = fetch_page(scraper, params, page_num)
        if result is None:
            print(f"  Stopping at page {page_num} due to error/block (HTTP {meta.get('status_code')})")
            break

        pages_data.append(result)

        # Track IDs for duplicate detection
        before_count = len(all_listing_ids)
        page_ids = set(result["listing_ids"])
        all_listing_ids.update(page_ids)
        new_ids = all_listing_ids - (all_listing_ids - page_ids) if before_count > 0 else page_ids
        dupes_in_page = len(page_ids) - len(page_ids - all_listing_ids) if before_count > 0 else 0

        print(f"    -> Unique so far: {len(all_listing_ids)}, new this page: {len(page_ids - (set() if before_count == 0 else page_ids))}")

        # Check nextPage
        next_page = result["nextPage"]
        if next_page is None:
            print(f"  Reached end: nextPage is null after page {page_num}")
            break

        # Duplicate loop detection: if all IDs on this page already seen
        if before_count > 0 and page_ids.issubset(all_listing_ids - page_ids if before_count > 0 else set()):
            print(f"  Stopping: all {len(page_ids)} listing IDs on page {page_num} already seen (pagination loop)")
            break

        params["nextPage"] = next_page
        print(f"  Waiting {PAGE_DELAY_S}s...")
        time.sleep(PAGE_DELAY_S)
    else:
        print(f"  Reached max pages ({MAX_PAGES})")

    # === Analyze ===
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)

    np_values = []
    all_updated_ats = []
    page_sizes = []

    for p in pages_data:
        pn = p["page"]
        nc = p["listings_count"]
        np_val = p["nextPage"]
        ids = p["listing_ids"]
        np_values.append(np_val)
        page_sizes.append(nc)

        # Collect updated_ats from raw listings
        for listing in p["listings"]:
            if isinstance(listing, dict) and listing.get("updated_at"):
                all_updated_ats.append(listing["updated_at"])

        print(f"  Page {pn}: {nc} listings, nextPage={np_val}")

    total_unique = len(all_listing_ids)
    total_raw = sum(p["listings_count"] for p in pages_data)
    dupe_count = total_raw - total_unique

    print(f"\n  Total pages fetched: {len(pages_data)}")
    print(f"  Listings per page: {page_sizes}")
    print(f"  Total raw listings: {total_raw}")
    print(f"  Total unique listing IDs: {total_unique}")
    print(f"  Duplicate count: {dupe_count}")

    if all_updated_ats:
        sorted_ts = sorted(all_updated_ats)
        print(f"  updated_at range: {sorted_ts[0]}  ->  {sorted_ts[-1]}")

    print(f"  nextPage values: {np_values}")
    if len(np_values) >= 2:
        print(f"  nextPage type: {'cursor (opaque string)' if all(isinstance(v, str) for v in np_values if v is not None) else 'mixed'}")
        diffs = [v for v in np_values if v is not None]
        if len(diffs) >= 2:
            print(f"  nextPage monotonic? {'Yes (values increase)' if all(str(diffs[i]) < str(diffs[i+1]) for i in range(len(diffs)-1) if diffs[i] is not None and diffs[i+1] is not None) else 'Not clearly monotonic'}")

    # Window analysis
    if all_updated_ats:
        window_start = sorted_ts[0]
        window_end = sorted_ts[-1]
        start_dt = datetime.fromisoformat(window_start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(window_end.replace("Z", "+00:00"))
        window_hours = (end_dt - start_dt).total_seconds() / 3600
        print(f"  Time window: {window_hours:.1f} hours ({window_start} -> {window_end})")

    # Rate limit / blocking
    rate_info = []
    for p in pages_data:
        m = p.get("meta", {})
        hdrs = m.get("headers", {})
        for k, v in hdrs.items():
            kl = k.lower()
            if "ratelimit" in kl or "retry" in kl or "cf-" in kl:
                rate_info.append((p["page"], k, v))
    if rate_info:
        print(f"  Rate/block headers: {rate_info}")
    else:
        print(f"  Rate/block headers: none observed")

    print("\n  Historical coverage implications:")
    if all_updated_ats:
        print(f"    completed=true returns only ~{window_hours:.0f}h window of recent trades")
        print(f"    Cannot paginate back beyond this window — nextPage eventually goes null")
        print(f"    Historical depth is limited to whatever the server retains in active results")
    print(f"    Long-term history requires periodic snapshots, not deep pagination")

    print("\n" + "=" * 70)
    print("END AUDIT")
    print("=" * 70)

    # === Save ===
    output = {
        "meta": {
            "audit_type": "pagination_window_audit",
            "item": "Jah Rune",
            "item_id": JAH_ITEM_ID,
            "segment": "pc_sc_nl",
            "fetched_at": now,
            "max_pages": MAX_PAGES,
            "page_delay_s": PAGE_DELAY_S,
        },
        "summary": {
            "pages_fetched": len(pages_data),
            "total_raw_listings": total_raw,
            "total_unique_listing_ids": total_unique,
            "duplicate_count": dupe_count,
            "page_sizes": page_sizes,
            "nextPage_values": np_values,
            "updated_at_min": sorted_ts[0] if all_updated_ats else None,
            "updated_at_max": sorted_ts[-1] if all_updated_ats else None,
        },
        "pages": pages_data,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print(f"\nFull data saved to: {OUT}")


if __name__ == "__main__":
    main()
