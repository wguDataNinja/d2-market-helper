#!/usr/bin/env python3
"""audit_traderie_raw_fetch.py - One-shot raw response audit for Jah Rune, pc_sc_nl.

Fetches ONE request, saves the FULL raw response, and prints a detailed
field-level analysis of the API envelope.

Usage:
    python scripts/audit_traderie_raw_fetch.py
"""

import json
import sys
import cloudscraper
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "research" / "traderie_raw_audit_jah_one_segment.sample.json"

JAH_ITEM_ID = 2552039455

URL = "https://traderie.com/api/diablo2resurrected/listings"

PARAMS = {
    "completed": "true",
    "auction": "false",
    "prop_Platform": "PC",
    "prop_Mode": "softcore",
    "prop_Ladder": "false",
    "item": JAH_ITEM_ID,
}


def deep_field_summary(obj, prefix="", seen=None):
    """Recursively enumerate every unique key path in a JSON-decoded object."""
    if seen is None:
        seen = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            seen.add(path)
            deep_field_summary(v, path, seen)
    elif isinstance(obj, list) and len(obj) > 0:
        deep_field_summary(obj[0], prefix, seen)
    return seen


def describe_type(v):
    t = type(v).__name__
    if t == "list":
        return f"list[{len(v)}]"
    if t == "dict":
        return f"dict(keys={list(v.keys())[:5]})"
    return t


def print_detailed_analysis(raw, meta):
    ts = datetime.now().strftime("%H:%M:%S")

    # 1. Response envelope at top level
    print("=" * 72)
    print(f"TRADERIE RAW RESPONSE AUDIT  —  {ts}")
    print("=" * 72)

    top_keys = list(raw.keys())
    print(f"\n  Top-level keys ({len(top_keys)}): {top_keys}")

    # 2. Pagination fields
    pagination_keys = [k for k in top_keys if k
                       in ("total", "page", "limit", "has_next", "has_more",
                           "pages", "offset", "count", "per_page")]
    print(f"\n── Pagination / Envelope ──")
    for k in pagination_keys:
        print(f"  {k}: {json.dumps(raw[k], default=str)}")
    # Also print any untagged integer/boolean top-level fields
    for k in top_keys:
        if isinstance(raw.get(k), (int, bool, float)) and k not in pagination_keys:
            print(f"  {k} ({type(raw[k]).__name__}): {raw[k]}")

    # 3. Listings array
    listings = raw.get("listings") if isinstance(raw.get("listings"), list) else []
    print(f"\n── Listings Array ──")
    print(f"  listing count: {len(listings)}")

    if not listings:
        print("  WARNING: No listings returned!")
        return

    # Deep field enumeration from first listing
    all_fields = sorted(deep_field_summary(listings[0]))
    print(f"\n── All Distinct Fields in a Listing ({len(all_fields)}) ──")
    for f in all_fields:
        val = resolve_path(listings[0], f)
        print(f"  {f:45s}  {describe_type(val):15s}  example: {json.dumps(val, default=str)[:80]}")

    # 4. Check listings that have buyer
    buyers = [l for l in listings if l.get("buyer")]
    if buyers:
        bf = sorted(deep_field_summary(buyers[0].get("buyer")))
        print(f"\n── Buyer fields (present in {len(buyers)}/{len(listings)} listings) ──")
        for f in bf:
            val = resolve_path(buyers[0], f"buyer.{f}")
            print(f"  buyer.{f:40s}  {describe_type(val):15s}  example: {json.dumps(val, default=str)[:80]}")

    # 5. Pricing / consideration
    prices = listings[0].get("prices", listings[0].get("consideration", listings[0].get("price_items", [])))
    if isinstance(prices, list) and len(prices) > 0:
        pf = sorted(deep_field_summary(prices[0]))
        print(f"\n── Price/Consideration Item Fields (from first listing) ──")
        for f in pf:
            val = resolve_path(prices[0], f)
            print(f"  price.{f:35s}  {describe_type(val):15s}  example: {json.dumps(val, default=str)[:80]}")

    # 6. Seller fields (expanded)
    seller = listings[0].get("seller", {})
    if isinstance(seller, dict):
        sf = sorted(deep_field_summary(seller))
        print(f"\n── Seller Fields ──")
        for f in sf:
            val = resolve_path(seller, f)
            print(f"  seller.{f:35s}  {describe_type(val):15s}  example: {json.dumps(val, default=str)[:80]}")

    # 7. Listing status / trade status
    status_keys = [k for k in all_fields if "status" in k.lower() or "trade" in k.lower()]
    if status_keys:
        print(f"\n── Status / Trade Status ──")
        for k in status_keys:
            val = resolve_path(listings[0], k)
            print(f"  {k:45s}  {describe_type(val):15s}  {json.dumps(val, default=str)[:80]}")

    # 8. Timestamps
    ts_keys = [k for k in all_fields if "time" in k.lower() or "date" in k.lower() or k in ("created_at", "updated_at", "completed_at")]
    if ts_keys:
        print(f"\n── Timestamps ──")
        for k in ts_keys:
            val = resolve_path(listings[0], k)
            print(f"  {k:45s}  {json.dumps(val, default=str)[:80]}")

    # 9. Properties
    prop_keys = [k for k in all_fields if "prop_" in k or k in ("platform", "ladder", "mode", "hardcore", "region")]
    if not prop_keys:
        prop_keys = [k for k in top_keys if "prop_" in k]
    print(f"\n── Segment Properties ──")
    if prop_keys:
        for k in prop_keys:
            val = resolve_path(listings[0], k) if "." in k else raw.get(k, listings[0].get(k, "N/A"))
            print(f"  {k:45s}  {json.dumps(val, default=str)[:80]}")
    else:
        print("  (none at listing level — check envelope)")
        for k in top_keys:
            if k.startswith("prop_"):
                print(f"  {k}: {json.dumps(raw[k], default=str)}")

    # 10. Listing IDs
    id_keys = [k for k in all_fields if k in ("id", "listing_id", "listingId", "trade_id", "item_id")]
    print(f"\n── IDs ──")
    for k in id_keys:
        val = resolve_path(listings[0], k)
        print(f"  {k:45s}  {json.dumps(val, default=str)[:80]}")

    # 11. HTTP metadata
    print(f"\n── HTTP Metadata ──")
    print(f"  status_code: {meta.get('status_code')}")
    for h in ("content-type", "x-ratelimit-", "x-total-", "link", "x-pagination-"):
        for k, v in meta.get("headers", {}).items():
            if h in k.lower():
                print(f"  header {k}: {v}")

    print("\n" + "=" * 72)
    print("END AUDIT")
    print("=" * 72)


def resolve_path(obj, dotted):
    parts = dotted.split(".")
    cur = obj
    for p in parts:
        if isinstance(cur, dict):
            cur = cur.get(p, "<MISSING>")
        elif isinstance(cur, list) and p.lstrip("-").isdigit():
            idx = int(p)
            cur = cur[idx] if 0 <= idx < len(cur) else "<OOB>"
        else:
            return "<UNRESOLVABLE>"
        if cur == "<MISSING>":
            break
    return cur


def main():
    scraper = cloudscraper.create_scraper()
    print(f"Fetching: {URL}")
    print(f"Params: {json.dumps(PARAMS, indent=2)}")
    print(f"Item: Jah Rune (id={JAH_ITEM_ID})  Segment: pc_sc_nl\n")

    res = scraper.get(URL, params=PARAMS, timeout=15)
    meta = {
        "status_code": res.status_code,
        "headers": dict(res.headers),
        "url": res.url,
        "elapsed_seconds": res.elapsed.total_seconds(),
    }

    print(f"HTTP {res.status_code} in {res.elapsed.total_seconds():.2f}s")
    print(f"Response size: {len(res.text):,} bytes\n")

    if res.status_code != 200:
        print(f"Error response body:\n{res.text[:2000]}")
        sys.exit(1)

    raw = res.json()

    # Save FULL raw response
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"meta": meta, "response": raw}, indent=2, default=str), encoding="utf-8")
    print(f"Full raw response saved to: {OUT}\n")

    print_detailed_analysis(raw, meta)


if __name__ == "__main__":
    main()
