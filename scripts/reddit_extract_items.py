#!/usr/bin/env python3
"""
reddit_extract_items.py — Registry-based item term extraction from Reddit posts.

Uses data/item_registry/ for canonical matching. Reports raw vs registry-matched
counts and surfaces unresolved high-frequency terms.
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter

ROOT_DIR = Path(__file__).resolve().parent.parent


def load_registry():
    with open(ROOT_DIR / "data" / "item_registry" / "items.json") as f:
        items = json.load(f)
    with open(ROOT_DIR / "data" / "item_registry" / "aliases.json") as f:
        aliases = json.load(f)

    # Build canonical name -> item_id map (lowered)
    canonical_map = {}
    for item in items:
        canonical_map[item["canonical_name"].lower()] = item["item_id"]

    # Build alias -> item_id map
    alias_map = {}
    for a in aliases:
        if a.get("item_id"):
            alias_map[a["alias"].lower()] = a["item_id"]

    # Item lookup by id
    item_lookup = {i["item_id"]: i for i in items}

    return items, aliases, canonical_map, alias_map, item_lookup


def load_submissions(paths):
    posts = []
    for p in paths:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        posts.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return posts


SHORT_RUNE_NAMES = {"el", "eld", "eth", "io", "ith", "ko", "lo", "lum", "nef", "ral", "sol", "tal", "thul", "ort", "amn", "hel"}


def is_short_rune(word):
    return word.lower() in SHORT_RUNE_NAMES


GENERIC_BASE_TYPES = {
    "ring", "amulet", "helm", "boots", "belt", "gloves", "jewel", "charm",
    "circlet", "diadem", "crown", "coronet", "tiara",
    "weapon", "armor", "shield", "scepter", "wand", "staff", "bow",
    "blade", "axe", "mace", "hammer", "spear", "polearm", "sword",
    "helmet", "mask", "hat", "cap", "bone", "gold",
}

SIGNIFICANT_CATEGORIES = {
    "runes", "uniques", "charms", "runewords", "commodities", "jewelry",
}

ENGLISH_WORD_RUNEWORDS = {
    "chaos", "death", "black", "dream", "faith", "fury", "glory",
    "harmony", "honor", "ice", "insight", "justice", "light", "memory",
    "myth", "passion", "peace", "principle", "prudence", "radiance",
    "rhyme", "silence", "smoke", "splendor", "steadfast", "storm",
    "strength", "treachery", "voice", "wealth", "white", "wind",
    "wisdom", "wrath",
}

# Items that are also common English words — require " Rune" or " Runeword" context
AMBIGUOUS_ITEMS = {
    "lo rune", "el rune", "eth rune", "io rune", "ith rune",
    "ko rune", "lum rune", "hel rune", "sol rune", "tal rune",
    "ort rune", "ral rune", "amn rune", "nef rune",
}


def extract_terms(text, canonical_map, alias_map, item_lookup):
    text_lower = text.lower()
    found = Counter()
    unresolved = Counter()
    generic = Counter()

    # 1. Alias match first (word-boundary required) — most specific
    for alias, item_id in alias_map.items():
        pattern = re.compile(r'\b' + re.escape(alias) + r'\b')
        matches = pattern.findall(text_lower)
        if matches:
            found[item_id] += len(matches)

    # 2. Multi-word canonical name match
    for cname, item_id in canonical_map.items():
        if " " not in cname:
            continue
        pattern = re.compile(r'\b' + re.escape(cname) + r'\b')
        matches = pattern.findall(text_lower)
        if matches:
            item = item_lookup.get(item_id, {})
            cat = item.get("category", "")
            if cat in SIGNIFICANT_CATEGORIES:
                found[item_id] += len(matches)
            elif item_id in ENGLISH_WORD_RUNEWORDS:
                # require "runeword" context for English-word runewords
                context_check = re.search(r'\b' + re.escape(cname) + r'.{0,30}(runeword|rune word|rw)\b', text_lower, re.I)
                if context_check:
                    found[item_id] += len(matches)
                else:
                    generic[item_id] += len(matches)
            else:
                generic[item_id] += len(matches)

    # 3. Single-word canonical names (with care)
    for cname, item_id in canonical_map.items():
        if " " in cname:
            continue
        # Skip generic base types
        if cname in GENERIC_BASE_TYPES:
            generic[item_id] += text_lower.count(cname)
            continue
        # Skip ambiguous single-word items
        if cname in AMBIGUOUS_ITEMS:
            continue
        # Full-word rune names: "ist", "ber", "jah", etc.
        if cname.endswith(" rune") and len(cname.split()) == 2:
            pattern = re.compile(r'\b' + re.escape(cname) + r'\b')
            matches = pattern.findall(text_lower)
            if matches:
                found[item_id] += len(matches)
            else:
                # Try standalone short form with word boundary if it's a distinctive rune
                short = cname.split()[0]
                if short not in SHORT_RUNE_NAMES:
                    sp = re.compile(r'\b' + re.escape(short) + r'\b')
                    sm = sp.findall(text_lower)
                    if sm:
                        found[item_id] += len(sm)
            continue
        # Other single-word items with word boundary
        pattern = re.compile(r'\b' + re.escape(cname) + r'\b')
        matches = pattern.findall(text_lower)
        if matches:
            item = item_lookup.get(item_id, {})
            cat = item.get("category", "")
            if cat in SIGNIFICANT_CATEGORIES:
                found[item_id] += len(matches)
            else:
                generic[item_id] += len(matches)

    # 4. Short rune name extraction (context-aware)
    pattern_short = re.compile(r'\b([a-z]{2,5})\s+rune\b')
    for match in pattern_short.finditer(text_lower):
        short = match.group(1)
        if short in SHORT_RUNE_NAMES:
            cname_lookup = short + " rune"
            if cname_lookup in canonical_map:
                item_id = canonical_map[cname_lookup]
                if item_id in found:
                    found[item_id] += 1
                else:
                    found[item_id] = 1
            else:
                unresolved[short] += 1

    return found, unresolved, generic


def run(input_jsonl_paths, min_unresolved_freq=3):
    items, aliases, canonical_map, alias_map, item_lookup = load_registry()
    posts = load_submissions(input_jsonl_paths)

    print(f"Loaded {len(posts)} posts from {len(input_jsonl_paths)} files")
    print(f"Registry: {len(item_lookup)} canonical items, {len(alias_map)} aliases")
    print()

    total_found = Counter()
    total_unresolved = Counter()
    total_generic = Counter()
    per_subreddit = {}

    for post in posts:
        sub = post.get("subreddit_name", "unknown")
        text = ((post.get("title") or "") + " " + (post.get("selftext") or ""))
        found, unresolved, generic = extract_terms(text, canonical_map, alias_map, item_lookup)

        per_subreddit.setdefault(sub, {"found": Counter(), "unresolved": Counter(), "generic": Counter()})
        per_subreddit[sub]["found"] += found
        per_subreddit[sub]["unresolved"] += unresolved
        per_subreddit[sub]["generic"] += generic
        total_found += found
        total_unresolved += unresolved
        total_generic += generic

    # Report
    print("=" * 60)
    print("REGISTRY-MATCHED ITEM COUNTS")
    print("=" * 60)
    print(f"{'Item':45s} {'Count':>6}")
    print("-" * 52)
    for item_id, count in total_found.most_common(40):
        item = item_lookup.get(item_id, {})
        name = item.get("canonical_name", item_id)[:44]
        print(f"  {name:43s} {count:>5d}")

    print()
    print("=" * 60)
    print("GENERIC / BASE TYPE TERMS (excluded from significant counts)")
    print("=" * 60)
    print(f"{'Term':45s} {'Count':>6}")
    print("-" * 52)
    for item_id, count in total_generic.most_common(15):
        item = item_lookup.get(item_id, {})
        name = item.get("canonical_name", item_id)[:44]
        cat = item.get("category", "?")
        print(f"  {name:35s} ({cat:12s}) {count:>5d}")

    print()
    print("=" * 60)
    print("UNRESOLVED HIGH-FREQUENCY TERMS")
    print("=" * 60)
    print(f"(terms with >= {min_unresolved_freq} mentions not matched by registry)")
    print()
    print(f"{'Term':30s} {'Count':>6}")
    print("-" * 38)
    for term, count in sorted(total_unresolved.items(), key=lambda x: -x[1]):
        if count >= min_unresolved_freq:
            print(f"  {term:28s} {count:>5d}")
    print()

    # Per-subreddit breakdown
    print("=" * 60)
    print("PER-SUBREDDIT BREAKDOWN")
    print("=" * 60)
    for sub, data in sorted(per_subreddit.items()):
        top5 = data["found"].most_common(5)
        unresolved_count = len(data["unresolved"])
        print(f"\n  r/{sub}:")
        print(f"    Matched items: {len(data['found'])} unique")
        print(f"    Unresolved terms: {sum(data['unresolved'].values())} occurrences ({unresolved_count} unique)")
        if top5:
            print(f"    Top 5 matched:")
            for item_id, count in top5:
                name = item_lookup.get(item_id, {}).get("canonical_name", item_id)
                print(f"      {name:40s} {count:>4d}")

    # Summary
    total_raw = sum(total_found.values())
    total_gen = sum(total_generic.values())
    total_unres = sum(total_unresolved.values())
    total_all = total_raw + total_gen + total_unres
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Significant item mentions (registry-matched): {total_raw}")
    print(f"  Generic/base type mentions (excluded):       {total_gen}")
    print(f"  Unresolved (needs review):                   {total_unres}")
    print(f"  Total matched:                               {total_raw + total_gen} / {total_all} ({ (total_raw + total_gen) / total_all * 100:.1f}% )" if total_all > 0 else "")
    print()


if __name__ == "__main__":
    import glob
    paths = sorted(glob.glob(str(ROOT_DIR / "research" / "reddit" / "raw" / "*.jsonl")))
    if not paths:
        print("No research/reddit/raw/*.jsonl files found.")
        sys.exit(1)
    run(paths)
