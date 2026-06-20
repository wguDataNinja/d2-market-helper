#!/usr/bin/env python3
"""
validate_source_manifest.py — Validate data/source_manifest.json.

Checks required fields, allowed values, uniqueness, and artifact paths.
"""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT_DIR / "data" / "source_manifest.json"

REQUIRED_FIELDS = [
    "source_slug", "display_name", "base_url", "category", "priority",
    "status", "evidence_classes", "known_urls", "supports_runes",
    "supports_selected_items", "segment_filters", "extraction",
    "current_artifacts", "caveats", "next_action", "last_reviewed_at",
]

REQUIRED_EXTRACTION_FIELDS = [
    "static_html", "rendered_html", "embedded_json", "api_observed",
    "browser_required", "manual_only",
]

ALLOWED_CATEGORIES = {
    "completed_player_trades", "active_player_marketplace",
    "forum_reference", "cash_market", "community_discussion",
    "source_directory_only",
}

ALLOWED_STATUSES = {
    "discovered", "captured_static", "captured_browser",
    "offline_parse_candidate", "parser_prototype_ready",
    "integrated", "deferred", "rejected",
}

ALLOWED_PRIORITIES = {"tier_1", "tier_2", "tier_3", "later"}

ALLOWED_SEGMENT_KEYS = {"platform", "ladder", "hardcore", "softcore", "season", "region"}


def validate():
    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found: {MANIFEST_PATH}")
        sys.exit(1)

    with open(MANIFEST_PATH, "r") as f:
        sources = json.load(f)

    if not isinstance(sources, list):
        print("ERROR: manifest must be a JSON array")
        sys.exit(1)

    errors = []
    warnings = []
    slugs = set()

    for i, s in enumerate(sources):
        idx = f"[{i}] {s.get('source_slug', '?')}"

        # Required top-level fields
        for field in REQUIRED_FIELDS:
            if field not in s:
                errors.append(f"{idx}: missing required field '{field}'")
            elif field in ["caveats", "current_artifacts", "known_urls", "evidence_classes"]:
                if not isinstance(s[field], list):
                    errors.append(f"{idx}: '{field}' must be a list")
            elif field in ["supports_runes", "supports_selected_items"]:
                if s[field] not in (True, False, "unknown", "partial (embedded in listing titles)"):
                    errors.append(f"{idx}: '{field}' must be true/false/unknown")

        # Slug uniqueness
        slug = s.get("source_slug", "")
        if slug:
            if slug in slugs:
                errors.append(f"{idx}: duplicate source_slug '{slug}'")
            slugs.add(slug)

        # Allowed values
        cat = s.get("category", "")
        if cat and cat not in ALLOWED_CATEGORIES:
            errors.append(f"{idx}: invalid category '{cat}' — allowed: {sorted(ALLOWED_CATEGORIES)}")

        status = s.get("status", "")
        if status and status not in ALLOWED_STATUSES:
            errors.append(f"{idx}: invalid status '{status}' — allowed: {sorted(ALLOWED_STATUSES)}")

        priority = s.get("priority", "")
        if priority and priority not in ALLOWED_PRIORITIES:
            errors.append(f"{idx}: invalid priority '{priority}' — allowed: {sorted(ALLOWED_PRIORITIES)}")

        # Extraction fields
        extraction = s.get("extraction", {})
        if not isinstance(extraction, dict):
            errors.append(f"{idx}: 'extraction' must be an object")
        else:
            for field in REQUIRED_EXTRACTION_FIELDS:
                if field not in extraction:
                    errors.append(f"{idx}: extraction missing '{field}'")
                elif extraction[field] not in (True, False):
                    errors.append(f"{idx}: extraction['{field}'] must be boolean")

        # Segment filter keys
        seg = s.get("segment_filters", {})
        if isinstance(seg, dict):
            for key in seg:
                if key not in ALLOWED_SEGMENT_KEYS:
                    warnings.append(f"{idx}: unknown segment filter key '{key}'")
        else:
            errors.append(f"{idx}: 'segment_filters' must be an object")

        # Source notes path
        notes_path = s.get("source_notes_path", "")
        if notes_path:
            full_path = ROOT_DIR / notes_path
            if not full_path.exists():
                warnings.append(f"{idx}: source_notes_path '{notes_path}' not found")

        # Caveats
        if not s.get("caveats"):
            warnings.append(f"{idx}: no caveats — add at least one caveat even if 'none identified'")

        # Artifacts
        for artifact in s.get("current_artifacts", []):
            full_path = ROOT_DIR / artifact
            if not full_path.exists():
                warnings.append(f"{idx}: artifact path '{artifact}' not found")

    # Report
    print(f"Source manifest validation: {len(sources)} sources")
    print()

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        print()

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  {w}")
        print()

    # Summary stats
    by_status = {}
    by_priority = {}
    by_category = {}
    for s in sources:
        by_status[s.get("status", "?")] = by_status.get(s.get("status", "?"), 0) + 1
        by_priority[s.get("priority", "?")] = by_priority.get(s.get("priority", "?"), 0) + 1
        by_category[s.get("category", "?")] = by_category.get(s.get("category", "?"), 0) + 1

    print("Status distribution:")
    for k in sorted(by_status):
        print(f"  {k}: {by_status[k]}")
    print()
    print("Priority distribution:")
    for k in sorted(by_priority):
        print(f"  {k}: {by_priority[k]}")
    print()
    print("Category distribution:")
    for k in sorted(by_category):
        print(f"  {k}: {by_category[k]}")

    if errors:
        sys.exit(1)

    print(f"\n✅ All {len(sources)} sources valid.")


if __name__ == "__main__":
    validate()
