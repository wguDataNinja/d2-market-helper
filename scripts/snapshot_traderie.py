#!/usr/bin/env python3
"""Snapshot-preserving Traderie fetch.

Writes raw + normalized snapshots and appends to JSONL history.
Maintains backward-compatible output at data/raw/raw_trades_{slug}.json.
"""

import argparse
import json
import sys
import random
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import cloudscraper

from lib import snapshot_io

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_OUTPUT_DIR = DATA_DIR / "raw"
ITEMS_JSON_PATH = DATA_DIR / "item_ids.json"
CONFIG_PATH = ROOT_DIR / "server_configs.json"

URL = "https://traderie.com/api/diablo2resurrected/listings"
PER_ITEM_DELAY = 5

# Timeout and retry configuration
# Hardcore segment API responses are slower/unreliable due to low trade volume.
# Softcore default is adequate; hardcore needs more time plus retry on transient failure.
DEFAULT_REQUEST_TIMEOUT_SECONDS = 10
HARDCORE_REQUEST_TIMEOUT_SECONDS = 20
REQUEST_MAX_ATTEMPTS = 3
REQUEST_BACKOFF_SECONDS = [5, 15]
HARDCORE_REQUEST_MAX_ATTEMPTS = 2

# Segment slugs
HARDCORE_SEGMENTS = {"pc_hc_l", "pc_hc_nl"}
CRITICAL_SEGMENTS = {"pc_sc_l", "pc_sc_nl"}

# Bounded error classifications — no raw exception text, no secrets
ERROR_CLASS_TIMEOUT = "timeout"
ERROR_CLASS_HTTP = "http_error"
ERROR_CLASS_CONNECTION = "connection_error"
ERROR_CLASS_PROTOCOL = "protocol_error"
ERROR_CLASS_UNKNOWN = "unknown"

# Ruleset filter mapping (used with prop_Game%20version API param)
# Proven via probe: prop_Game%20version=lord+of+destruction filters completed trades.
RULESET_MAP = {
    "rotw": "reign of the warlock",
    "lod": "lord of destruction",
    "classic": "classic",
}

# Items that consistently fail on hardcore segments (ReadTimeout / HTTP 503)
# Populated from manual collection runs — pc_hc_l had zero failures on 2026-06-23.
HARDCORE_SKIP_ITEMS = {
    "pc_hc_nl": {
        "Ist Rune",
        "Cham Rune",
        "Gul Rune",
        "Hel Rune",
        "Lem Rune",
        "Mal Rune",
        "Pul Rune",
        "Amn Rune",
        "The Stone of Jordan",
    },
}


def classify_error(exc: Exception) -> str:
    cls_name = type(exc).__name__
    if cls_name in ("ReadTimeout", "Timeout", "ConnectTimeout"):
        return ERROR_CLASS_TIMEOUT
    if cls_name.startswith("HTTP") or "HTTPError" in cls_name or cls_name in ("HTTPStatusError",):
        return ERROR_CLASS_HTTP
    if cls_name in ("ConnectionError", "ConnectionResetError", "ConnectionAbortedError",
                    "ConnectionRefusedError", "RemoteDisconnected", "ChunkedEncodingError"):
        return ERROR_CLASS_CONNECTION
    if cls_name in ("ProtocolError", "SSLError", "ProxyError", "InvalidURL",
                    "TooManyRedirects", "InvalidSchema"):
        return ERROR_CLASS_PROTOCOL
    return ERROR_CLASS_UNKNOWN


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_params(cfg, item_id, ruleset=None):
    params = {
        "completed": "true",
        "auction": "false",
        "prop_Platform": cfg["platform"].upper(),
        "prop_Mode": cfg["mode"],
        "prop_Ladder": str(cfg["ladder"]).lower(),
        "item": item_id,
    }
    # Game version param is NOT added here — it requires %20 encoding in the
    # param name (requests encodes spaces as +, which the API rejects).
    # fetch_for_item appends it manually to the URL with correct encoding.
    return params


def extract_properties(properties):
    meta = {}
    for prop in (properties or []):
        name = prop.get("property", "")
        if name == "Platform":
            meta["platform"] = (prop.get("string") or "unknown").lower()
        elif name == "Mode":
            meta["mode"] = prop.get("string") or "unknown"
            meta["hardcore"] = meta["mode"].lower() == "hardcore"
        elif name == "Ladder":
            if prop.get("type") == "bool":
                meta["ladder"] = prop.get("bool", False)
            elif prop.get("string"):
                meta["ladder"] = prop["string"].lower() == "ladder"
        elif name == "Game version":
            raw = (prop.get("string") or "").strip()
            meta["game_version"] = raw or "unknown"
            parts = [p.strip().lower() for p in raw.split(",")] if raw else []
            resolved = set()
            for p in parts:
                if p == "classic":
                    resolved.add("classic")
                elif p == "lord of destruction":
                    resolved.add("lod")
                elif p == "reign of the warlock":
                    resolved.add("rotw")
            if len(resolved) == 1:
                meta["ruleset"] = resolved.pop()
            elif len(resolved) > 1:
                meta["ruleset"] = "mixed"
            else:
                meta["ruleset"] = "unknown"
    return meta


def normalize_observation(entry, cfg, item_name, item_id, captured_at,
                          source_artifact_path, source_url, response_meta):
    seller_data = entry.get("seller", {}) or {}
    raw_prices = entry.get("prices", []) or []
    price_list = [
        {
            "name": p.get("name", "?"),
            "quantity": p.get("quantity", 1),
            "item_id": p.get("item_id"),
            "add": p.get("add") if "add" in p else None,
            "group": p.get("group") if "group" in p else None,
        }
        for p in raw_prices if isinstance(p, dict)
    ]
    has_and_prices = any(p.get("add") is True for p in price_list)
    price_group_count = len({p.get("group") for p in price_list
                            if p.get("group") is not None})
    price_entry_count = len(price_list)

    prop_meta = extract_properties(entry.get("properties"))
    listing_id = entry.get("id")

    obs = {
        "source_slug": f"traderie/{cfg['slug']}",
        "evidence_class": "traderie_completed_trade",
        "captured_at": captured_at,
        "source_artifact_path": str(source_artifact_path),
        "source_url": source_url,
        "item_name": item_name,
        "item_id": item_id,
        "listing_id": listing_id,
        "seller": seller_data.get("username") or "?",
        "seller_rating": seller_data.get("rating"),
        "seller_reviews": seller_data.get("reviews"),
        "seller_score": seller_data.get("score"),
        "seller_status": seller_data.get("status"),
        "has_and_prices": has_and_prices,
        "price_group_count": price_group_count,
        "price_entry_count": price_entry_count,
        "quantity": entry.get("amount", 1),
        "updated_at": entry.get("updated_at"),
        "price": price_list,
        "active": entry.get("active"),
        "completed": entry.get("completed"),
        "segment_slug": cfg["slug"],
        "version": response_meta.get("version"),
        "nextPage": response_meta.get("nextPage"),
        "product_id": listing_id,
        "price_usd": None,
    }
    obs.update(prop_meta)
    return obs


def append_to_legacy_raw(observations, cfg, category, item_name):
    output_path = RAW_OUTPUT_DIR / f"raw_trades_{cfg['slug']}.json"
    RAW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    existing = {}
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            existing = json.load(f)

    existing.setdefault(category, {})
    existing[category].setdefault(item_name, [])
    existing_ids = {t.get("listing_id") for t in existing[category][item_name]
                    if t.get("listing_id")}

    new_count = 0
    for obs in observations:
        lid = obs.get("listing_id")
        if lid and lid not in existing_ids:
            existing[category][item_name].append({
                "seller": obs["seller"],
                "quantity": obs["quantity"],
                "updated_at": obs["updated_at"],
                "price": obs["price"],
                "listing_id": obs["listing_id"],
                "seller_rating": obs.get("seller_rating"),
                "seller_reviews": obs.get("seller_reviews"),
                "active": obs.get("active"),
                "completed": obs.get("completed"),
                "item_id": obs.get("item_id"),
                "platform": obs.get("platform"),
                "mode": obs.get("mode"),
                "hardcore": obs.get("hardcore"),
                "ladder": obs.get("ladder"),
                "game_version": obs.get("game_version"),
                "ruleset": obs.get("ruleset"),
                "version": obs.get("version"),
                "nextPage": obs.get("nextPage"),
            })
            existing_ids.add(lid)
            new_count += 1

    if new_count > 0:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        print(f"  [legacy] appended {new_count} to {output_path}")

    return new_count


def fetch_with_retry(scraper, url, params, slug, item_name, max_attempts=None):
    """Fetch with segment-aware timeout and bounded retry/backoff.

    If params is None, url must be a fully-prepared URL including query string.
    Otherwise, params dict is URL-encoded by requests (use only for params
    whose names contain no spaces).

    Returns (response_json, attempts_used) on success.
    Raises the last exception if all attempts fail.
    """
    is_hardcore = slug in HARDCORE_SEGMENTS
    timeout = HARDCORE_REQUEST_TIMEOUT_SECONDS if is_hardcore else DEFAULT_REQUEST_TIMEOUT_SECONDS
    if max_attempts is None:
        max_attempts = REQUEST_MAX_ATTEMPTS

    last_exception = None
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"    [attempt {attempt}/{max_attempts}] timeout={timeout}s")
            if params is not None:
                res = scraper.get(url, params=params, timeout=timeout)
            else:
                res = scraper.get(url, timeout=timeout)
            res.raise_for_status()
            return res.json(), attempt
        except Exception as e:
            last_exception = e
            cls = type(e).__name__
            print(f"    [attempt {attempt}/{max_attempts}] {cls}: {e}")
            if attempt < max_attempts:
                backoff = REQUEST_BACKOFF_SECONDS[attempt - 1]
                print(f"    [backoff] waiting {backoff}s before retry...")
                time.sleep(backoff)

    raise last_exception


def fetch_for_item(scraper, cfg, item_name, item_id, category, captured_at, ruleset=None):
    params = build_params(cfg, item_id, ruleset=ruleset)
    slug = cfg["slug"]
    source = f"traderie/{slug}"
    is_hardcore = slug in HARDCORE_SEGMENTS

    timeout_str = f"{HARDCORE_REQUEST_TIMEOUT_SECONDS}s" if is_hardcore else f"{DEFAULT_REQUEST_TIMEOUT_SECONDS}s"
    print(f"\n  Fetching {item_name} ({category}) on {slug} [timeout={timeout_str}, max_attempts={REQUEST_MAX_ATTEMPTS}]...")

    max_attempts = HARDCORE_REQUEST_MAX_ATTEMPTS if is_hardcore else REQUEST_MAX_ATTEMPTS

    # Build the request URL. Standard params go through requests encoding.
    # Game version param needs %20 (not +) in the param name, so we build
    # the final URL manually when ruleset filtering is active.
    if ruleset:
        api_value = RULESET_MAP.get(ruleset)
        if api_value:
            base_qs = urllib.parse.urlencode(params)
            encoded_value = urllib.parse.quote(api_value)
            full_url = f"{URL}?{base_qs}&prop_Game%20version={encoded_value}"
            fetch_params = None
        else:
            full_url = URL
            fetch_params = params
    else:
        full_url = URL
        fetch_params = params

    raw_data, attempts_used = fetch_with_retry(
        scraper, full_url, fetch_params, slug, item_name,
        max_attempts=max_attempts,
    )
    listings = raw_data.get("listings", [])
    if not isinstance(listings, list):
        listings = []

    response_meta = {
        "version": raw_data.get("version"),
        "nextPage": raw_data.get("nextPage"),
    }

    raw_path = snapshot_io.write_raw_snapshot(raw_data, source)

    if fetch_params is None:
        source_url = full_url
    else:
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        source_url = f"{URL}?{query_string}"

    observations = []
    for entry in listings:
        obs = normalize_observation(
            entry, cfg, item_name, item_id, captured_at,
            raw_path, source_url, response_meta,
        )
        observations.append(obs)

    normalized_path = snapshot_io.write_normalized_snapshot(observations, source)

    dataset = f"completed_trades_{slug}"
    history_path = snapshot_io.append_history(source, dataset, observations)

    append_to_legacy_raw(observations, cfg, category, item_name)

    listing_ids = [obs["listing_id"] for obs in observations
                   if obs.get("listing_id")]
    updated_ats = [obs["updated_at"] for obs in observations
                   if obs.get("updated_at")]

    return {
        "captured_at": captured_at,
        "segment": slug,
        "item": item_name,
        "endpoint_params": params,
        "response_version": response_meta.get("version"),
        "listing_count": len(observations),
        "nextPage_raw": response_meta.get("nextPage"),
        "source_window_label": "rolling_recent_trades_50_cap",
        "raw_path": str(raw_path),
        "normalized_path": str(normalized_path),
        "history_path": str(history_path),
        "listing_ids": listing_ids,
        "updated_at_min": min(updated_ats) if updated_ats else None,
        "updated_at_max": max(updated_ats) if updated_ats else None,
    }


def match_item_name(requested, available_name):
    if requested == "all":
        return True
    r = requested.lower().strip()
    a = available_name.lower().strip()
    return r == a or a.startswith(r) or r in a


def main():
    parser = argparse.ArgumentParser(
        description="Snapshot-preserving Traderie fetch")
    parser.add_argument("--item", default="all",
                        help="Item name (e.g. 'Jah Rune') or 'all'")
    parser.add_argument("--segment", default="all",
                        help="Segment slug (e.g. 'pc_sc_nl') or 'all'")
    parser.add_argument("--single", action="store_true",
                        help="Test mode: process only first matched combo")
    parser.add_argument("--ruleset", default=None,
                        choices=sorted(RULESET_MAP.keys()),
                        help="Filter by ruleset: rotw, lod, classic")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prepared URLs and exit without making requests")
    args = parser.parse_args()

    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    configs = [c for c in load_json(CONFIG_PATH) if c.get("enabled", True)]
    items_by_cat = load_json(ITEMS_JSON_PATH)

    if args.segment != "all":
        configs = [c for c in configs if c["slug"] == args.segment]
        if not configs:
            print(f"Error: segment '{args.segment}' not found")
            sys.exit(1)

    if args.dry_run:
        ruleset_label = f" ruleset={args.ruleset}" if args.ruleset else ""
        print(f"DRY RUN — {len(configs)} config(s){ruleset_label}")
        for cfg in configs:
            for category, items in items_by_cat.items():
                for name, item_id in items.items():
                    if args.item != "all" and not match_item_name(args.item, name):
                        continue
                    params = build_params(cfg, item_id)
                    base_qs = urllib.parse.urlencode(params)
                    if args.ruleset:
                        api_value = RULESET_MAP.get(args.ruleset)
                        if api_value:
                            encoded_value = urllib.parse.quote(api_value)
                            query = f"{URL}?{base_qs}&prop_Game%20version={encoded_value}"
                        else:
                            query = f"{URL}?{base_qs}"
                    else:
                        query = f"{URL}?{base_qs}"
                    print(f"  {name:40s} {cfg['slug']:10s}  {query[:200]}")
        print("DRY RUN — no requests made")
        return [], 0

    scraper = cloudscraper.create_scraper()
    results = []
    # Track failures per segment: {slug: [item_name, ...]}
    seg_failures: dict[str, list[str]] = {}
    # Track per-segment progress for instrumentation
    seg_timers: dict[str, dict] = {}
    seg_last_success: dict[str, str] = {}

    for cfg in configs:
        slug = cfg["slug"]
        seg_start = time.time()
        seg_items_total = 0
        seg_items_ok = 0
        seg_items_skip = 0
        seg_items_fail = 0
        print(f"\n[PHASE] segment_start segment={slug} captured_at={captured_at}")

        for category, items in items_by_cat.items():
            for name, item_id in items.items():
                if args.item != "all" and not match_item_name(args.item, name):
                    continue

                seg_items_total += 1
                item_start = time.time()

                if slug in HARDCORE_SKIP_ITEMS and name in HARDCORE_SKIP_ITEMS[slug]:
                    print(f"  [ITEM] item={name} result=skip category={category}")
                    seg_items_skip += 1
                    continue

                try:
                    result = fetch_for_item(
                        scraper, cfg, name, item_id, category, captured_at,
                        ruleset=args.ruleset)
                    results.append(result)
                    item_elapsed = time.time() - item_start
                    print(f"  [ITEM] item={name} result=ok elapsed={item_elapsed:.1f}s category={category}")
                    seg_items_ok += 1
                    seg_last_success[slug] = name
                except Exception as e:
                    item_elapsed = time.time() - item_start
                    ec = classify_error(e)
                    print(f"  [ITEM] item={name} result=fail elapsed={item_elapsed:.1f}s error_class={ec} category={category}")
                    seg_failures.setdefault(slug, []).append(name)
                    seg_items_fail += 1

                if args.single:
                    print("\n  [--single] stopping after first match")
                    break
            if args.single and results:
                break
        if args.single and results:
            break

        seg_elapsed = time.time() - seg_start
        seg_timers[slug] = {
            "elapsed": seg_elapsed,
            "items_total": seg_items_total,
            "items_ok": seg_items_ok,
            "items_skip": seg_items_skip,
            "items_fail": seg_items_fail,
            "last_successful_item": seg_last_success.get(slug),
        }
        print(f"\n[PHASE] segment_end segment={slug} elapsed={seg_elapsed:.1f}s "
              f"items_total={seg_items_total} items_ok={seg_items_ok} "
              f"items_skip={seg_items_skip} items_fail={seg_items_fail}")

        time.sleep(PER_ITEM_DELAY + random.uniform(0, 2))

    total_listings = sum(r["listing_count"] for r in results)
    all_ids = []
    all_updated = []
    for r in results:
        all_ids.extend(r["listing_ids"])
        if r["updated_at_min"]:
            all_updated.append(r["updated_at_min"])
        if r["updated_at_max"]:
            all_updated.append(r["updated_at_max"])

    # Segment-level health classification
    segs_run = list({cfg["slug"] for cfg in configs})
    ok_segs: list[str] = []
    warn_segs: list[str] = []
    crit_failed: list[str] = []
    for s in segs_run:
        f_count = len(seg_failures.get(s, []))
        if f_count == 0:
            ok_segs.append(s)
        elif s in CRITICAL_SEGMENTS:
            crit_failed.append(f"{s} ({f_count} item(s) failed)")
        else:
            warn_segs.append(f"{s} ({f_count} item(s) failed)")

    critical_exit = len(crit_failed) > 0
    exit_code = 1 if critical_exit else 0

    print(f"\n{'='*60}")
    print(f"SEGMENT SUMMARY")
    print(f"{'='*60}")
    if ok_segs:
        print(f"  OK:       {', '.join(ok_segs)}")
    if warn_segs:
        print(f"  WARNING:  {', '.join(warn_segs)}")
    if crit_failed:
        print(f"  CRITICAL: {', '.join(crit_failed)}")
    print(f"  EXIT CODE: {exit_code} ({'critical failure' if critical_exit else 'ok' if not warn_segs else 'ok with warnings'})")

    # Instrumentation: per-segment timing and progress detail
    print(f"\n{'='*60}")
    print(f"INSTRUMENTATION — PER-SEGMENT PROGRESS")
    print(f"{'='*60}")
    for slug, info in sorted(seg_timers.items()):
        f_count = len(seg_failures.get(slug, []))
        last_ok = info.get("last_successful_item") or "(none)"
        print(f"  {slug}: elapsed={info['elapsed']:.1f}s "
              f"ok={info['items_ok']} skip={info['items_skip']} fail={info['items_fail']} "
              f"last_ok={last_ok}")

    print(f"\nTotal listings captured: {total_listings}")
    print(f"Unique listing IDs: {len(set(all_ids))}")
    if all_updated:
        print(f"updated_at range: {min(all_updated)} — {max(all_updated)}")

    # Print per-result detail for summary
    for r in results:
        print(f"\n  {r['item']} @ {r['segment']}:")
        print(f"    raw:  {r['raw_path']}")
        print(f"    norm: {r['normalized_path']}")
        print(f"    hist: {r['history_path']}")
        print(f"    listings: {r['listing_count']}")
        print(f"    updated_at: {r['updated_at_min']} .. {r['updated_at_max']}")

    return results, exit_code


if __name__ == "__main__":
    _, ec = main()
    sys.exit(ec)
