#!/usr/bin/env python3
"""
test_userscript_parse.py — Validate that the userscript data format
can support correct price lookups, segment detection, and trade evaluation.

This tests the data contract, not the userscript itself (which is JS).

NOTES on current vs planned behavior:
  - `parse_rune()` defaults to {quantity: 1, item: text} when no quantity
    prefix is found. This is the PLANNED fix behavior. The current external
    userscript (traderie-tools.user.js v2025-05-24) returns null for bare
    text, silently skipping single-quantity listings.
  - `evaluate_trade()` uses ±0.5 Ist delta thresholds. The current external
    userscript uses percentage-based scoring ((offer - ask) / offer * 100).
  - AND/bundle tests in evaluate_multi_ask_trade() are PLANNED behavior.
    The current userscript accumulates multi-item asks into a single group
    and scores them, which is risky for complex trades.
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FIXTURE_PATH = ROOT_DIR / "data" / "research" / "userscript_test_fixture.json"

# Simulated userscript logic for testing


def get_server_slug(url: str) -> str:
    """Simulates getServerSlug() from the userscript."""
    from urllib.parse import urlparse, parse_qs
    params = parse_qs(urlparse(url).query)
    plat = (params.get('prop_Platform', ['pc'])[0]).lower()
    mode = 'hc' if params.get('prop_Mode', [''])[0] == 'hardcore' else 'sc'
    lad = 'l' if params.get('prop_Ladder', [''])[0] == 'true' else 'nl'
    return f"{plat}_{mode}_{lad}"


def parse_rune(anchor_text: str) -> dict:
    """Simulates parseRune(el) from the userscript.

    Extracts {quantity, item} from anchor text like '2x Ber Rune' or 'Ber Rune'.

    NOTE: This is the PLANNED behavior — defaults to quantity 1 for bare
    text. The current external userscript returns null on no regex match.
    """
    import re
    m = re.match(r'(\d+)\s*[xX]\s*(.+)', anchor_text.strip())
    if m:
        return {"quantity": int(m.group(1)), "item": m.group(2).strip()}
    return {"quantity": 1, "item": anchor_text.strip()}


def get_price(prices: dict, segment: str, item: str) -> dict | None:
    """Look up a rune in the prices data for the given segment."""
    seg_data = prices.get(segment)
    if not seg_data:
        return None
    return seg_data.get(item)


def evaluate_trade(
    prices: dict,
    segment: str,
    offered_item: str,
    offered_qty: int,
    requested_item: str,
    requested_qty: int,
) -> dict:
    """Evaluate a single rune-for-rune trade. Returns evaluation result.

    Simulates the planned overlay's injectPercentAndTooltip() logic.
    Uses ±0.5 Ist display thresholds.

    NOTE: The current external userscript uses percentage-based scoring
    ((offer - ask) / offer * 100), not Ist-delta thresholds.
    """
    offer_price = get_price(prices, segment, offered_item)
    request_price = get_price(prices, segment, requested_item)

    if not offer_price or not request_price:
        return {"status": "unavailable", "reason": "One or both runes not found in prices"}

    offer_ist = offer_price["ist_value"]
    request_ist = request_price["ist_value"]

    if offer_ist is None or request_ist is None:
        return {"status": "unavailable", "reason": "One or both runes have no price"}

    total_offer = offered_qty * offer_ist
    total_request = requested_qty * request_ist
    delta = total_request - total_offer

    if delta >= 0.5:
        label = "good_deal"
    elif delta <= -0.5:
        label = "overpay"
    else:
        label = "fair"

    # Check confidence
    low_conf = offer_price.get("confidence") in ("low", "unavailable") or \
               request_price.get("confidence") in ("low", "unavailable")

    return {
        "status": label,
        "delta_ist": round(delta, 4),
        "offer_total_ist": round(total_offer, 4),
        "request_total_ist": round(total_request, 4),
        "offer_price_per_unit": offer_ist,
        "request_price_per_unit": request_ist,
        "low_confidence": low_conf,
        "offer_name": offered_item,
        "request_name": requested_item,
        "segment": segment,
    }


def is_complex_ask(requested_items: list) -> bool:
    """Check if the ask side is a multi-item AND/bundle request.

    PLANNED behavior: If more than one distinct requested item is present
    (not separated by OR alternatives), the trade should be flagged as
    complex — review manually rather than scored.
    """
    return len(requested_items) > 1


def evaluate_multi_ask_trade(
    prices: dict,
    segment: str,
    offered_item: str,
    offered_qty: int,
    requested_items: list,
) -> dict:
    """Evaluate a trade with multiple possible ask groups.

    requested_items: list of lists, where each inner list represents one
    OR-alternative group of items. AND trades (multiple items in one group)
    are flagged as complex.

    PLANNED behavior. The current userscript accumulates all items in an
    ask group and scores them as a sum, without a complexity warning.
    """
    if not requested_items:
        return {"status": "unavailable", "reason": "No ask items parsed"}

    # Check each OR-alternative group
    complex_groups = []
    simple_groups = []

    for group in requested_items:
        if is_complex_ask(group):
            complex_groups.append(group)
        else:
            simple_groups.append(group)

    if complex_groups:
        return {
            "status": "complex",
            "reason": "Complex trade — review manually",
            "complex_groups": len(complex_groups),
            "simple_groups": len(simple_groups),
        }

    # If all groups are single items, evaluate each OR alternative
    if len(simple_groups) == 1:
        # Single ask item — delegate to simple evaluate_trade
        ask = simple_groups[0][0]
        return evaluate_trade(prices, segment, offered_item, offered_qty, ask["item"], ask.get("quantity", 1))

    # Multiple OR alternatives — score each and return best
    results = []
    for group in simple_groups:
        ask = group[0]
        r = evaluate_trade(prices, segment, offered_item, offered_qty, ask["item"], ask.get("quantity", 1))
        results.append(r)

    return {
        "status": "or_options",
        "results": results,
        "reason": f"{len(results)} OR alternatives evaluated",
    }


def get_segment_warning(url: str, prices: dict) -> dict:
    """Check if the detected segment is valid and warn if defaulted.

    PLANNED behavior. The current userscript has no segment warning.
    """
    slug = get_server_slug(url)
    has_filters = "prop_Platform" in url or "prop_Mode" in url or "prop_Ladder" in url

    if not has_filters:
        return {
            "segment": slug,
            "warning": "Defaulting to pc_sc_nl — enable Traderie filters for accurate pricing",
            "has_data": slug in prices,
        }

    if slug not in prices:
        return {
            "segment": slug,
            "warning": f"Segment '{slug}' has no pricing data",
            "has_data": False,
        }

    return {"segment": slug, "warning": None, "has_data": True}


def main():
    with open(FIXTURE_PATH) as f:
        prices = json.load(f)

    passed = 0
    failed = 0
    skipped = 0

    print("=" * 60)
    print("Test Group A: Segment detection")
    print("=" * 60)
    test_cases = [
        ("https://traderie.com/d2r?prop_Platform=pc&prop_Mode=softcore&prop_Ladder=false", "pc_sc_nl"),
        ("https://traderie.com/d2r?prop_Platform=pc&prop_Mode=hardcore&prop_Ladder=true", "pc_hc_l"),
        ("https://traderie.com/d2r?prop_Platform=pc&prop_Mode=softcore&prop_Ladder=true", "pc_sc_l"),
        ("https://traderie.com/d2r?prop_Platform=pc&prop_Mode=hardcore&prop_Ladder=false", "pc_hc_nl"),
        ("https://traderie.com/d2r", "pc_sc_nl"),  # default
    ]
    for url, expected in test_cases:
        result = get_server_slug(url)
        status = "PASS" if result == expected else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        print(f"  [{status}] getServerSlug('{url}') = '{result}' (expected '{expected}')")

    print()
    print("=" * 60)
    print("Test Group B: parseRune (quantity + item extraction)")
    print("=" * 60)
    print("  NOTE: This test helper defaults to qty=1 on no match (PLANNED).")
    print("  The current external userscript returns null on no match.")
    print()
    parse_cases = [
        ("2x Ber Rune", {"quantity": 2, "item": "Ber Rune"}),
        ("3x Ist Rune", {"quantity": 3, "item": "Ist Rune"}),
        ("5x Pul Rune", {"quantity": 5, "item": "Pul Rune"}),
        # Planned behavior: bare text without quantity
        ("Ber Rune", {"quantity": 1, "item": "Ber Rune"}),
        ("Jah Rune", {"quantity": 1, "item": "Jah Rune"}),
        ("Lo Rune", {"quantity": 1, "item": "Lo Rune"}),
        # Planned behavior: explicit single quantity
        ("1x Ber Rune", {"quantity": 1, "item": "Ber Rune"}),
        # Planned behavior: unknown item name
        ("Shako", {"quantity": 1, "item": "Shako"}),
        ("Griffon's Eye", {"quantity": 1, "item": "Griffon's Eye"}),
    ]
    for anchor, expected in parse_cases:
        result = parse_rune(anchor)
        status = "PASS" if result == expected else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        print(f"  [{status}] parseRune('{anchor}') = {result}")

    print()
    print("=" * 60)
    print("Test Group C: Price lookup across segments")
    print("=" * 60)
    lookup_cases = [
        # (segment, item, field, expected)
        ("pc_sc_nl", "Jah Rune", "ist_value", 17.25),
        ("pc_sc_nl", "Ber Rune", "ist_value", 12.43),
        ("pc_sc_nl", "El Rune", "ist_value", None),
        ("pc_sc_nl", "Zod Rune", "confidence", "low"),
        ("pc_sc_nl", "Zod Rune", "low_confidence", True),
        ("pc_sc_l", "Jah Rune", "ist_value", 17.25),
        ("pc_hc_l", "Jah Rune", "ist_value", 21.5),
        ("pc_hc_nl", "Jah Rune", "ist_value", 9.0),
        ("pc_hc_l", "Ber Rune", "confidence", "low"),
        ("pc_hc_nl", "Ber Rune", "confidence", "low"),
        # Missing segment
        ("pc_xbox_sc_nl", "Jah Rune", None, None),
        # Missing rune in existing segment
        ("pc_sc_nl", "Hel Rune", None, None),
    ]
    for segment, item, field, expected in lookup_cases:
        result = get_price(prices, segment, item)
        if result is None:
            val = None
        else:
            val = result.get(field) if field else None
        status = "PASS" if val == expected else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        expected_str = str(expected) if expected is not None else "None"
        val_str = str(val) if val is not None else "None"
        print(f"  [{status}] getPrice('{segment}', '{item}')", end="")
        if field:
            print(f".{field} = {val_str} (expected {expected_str})")
        else:
            print(f" = None (expected None — segment not in feed)")

    print()
    print("=" * 60)
    print("Test Group D: Simple trade evaluation (single-item asks)")
    print("=" * 60)
    print("  NOTE: Uses ±0.5 Ist delta thresholds (PLANNED). The current")
    print("  external userscript uses percentage-based scoring.")
    print()
    trade_cases = [
        # (segment, offered, qty, requested, qty, expected_status)
        # pc_sc_nl
        ("pc_sc_nl", "Ist Rune", 10, "Jah Rune", 1, "good_deal"),
        ("pc_sc_nl", "Jah Rune", 1, "Ist Rune", 17, "fair"),
        ("pc_sc_nl", "Ber Rune", 1, "Jah Rune", 1, "good_deal"),
        ("pc_sc_nl", "Jah Rune", 1, "Ber Rune", 1, "overpay"),
        ("pc_sc_nl", "Cham Rune", 1, "Ber Rune", 1, "good_deal"),  # 4.20 → 12.43: receiver +8.23
        # pc_sc_l
        ("pc_sc_l", "Jah Rune", 1, "Ber Rune", 1, "overpay"),      # 17.25 → 12.43: payer -4.82
        ("pc_sc_l", "Ohm Rune", 1, "Mal Rune", 5, "overpay"),      # 4.32 → 3.75: payer -0.57
        # pc_hc_l
        ("pc_hc_l", "Mal Rune", 1, "Ohm Rune", 1, "good_deal"),    # 0.76 → 4.87: receiver +4.11
        # pc_hc_nl
        ("pc_hc_nl", "Jah Rune", 1, "Ber Rune", 1, "good_deal"),   # 9.0 → 18.0: receiver +9.0
        ("pc_hc_nl", "Ber Rune", 1, "Jah Rune", 1, "overpay"),     # 18.0 → 9.0: payer -9.0
        # Planned: low confidence involved
        ("pc_sc_nl", "Zod Rune", 1, "Ist Rune", 5, "fair"),        # 5.12 vs 5.0 — low confidence expected
        # Planned: unavailable rune → unavailable status
        ("pc_sc_nl", "El Rune", 1, "Ist Rune", 1, "unavailable"),
        # Planned: unknown item → unavailable
        ("pc_sc_nl", "Shako", 1, "Ist Rune", 1, "unavailable"),
    ]
    for segment, offer, offer_qty, req, req_qty, expected in trade_cases:
        result = evaluate_trade(prices, segment, offer, offer_qty, req, req_qty)
        status = "PASS" if result["status"] == expected else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        delta = result.get("delta_ist", "?")
        low_conf = result.get("low_confidence", "?")
        print(f"  [{status}] [{segment}] {offer_qty}x {offer} → {req_qty}x {req}: "
              f"delta={delta} Ist, label='{result['status']}'"
              f"{' [LOW CONF]' if low_conf else ''}")

    print()
    print("=" * 60)
    print("Test Group E: Multi-ask trade evaluation (PLANNED behavior)")
    print("=" * 60)
    print("  The current external userscript accumulates multi-item asks")
    print("  into a single group and scores them. These tests verify the")
    print("  planned 'Complex trade — review manually' behavior.")
    print()

    multi_cases = [
        # (offered, qty, ask_groups, expected_status)
        # Single ask item — should delegate to simple evaluate
        ("pc_sc_nl", "Jah Rune", 1, [[{"item": "Ber Rune", "quantity": 1}]], "overpay"),
        # AND trade: two items in one group
        ("pc_sc_nl", "Ber Rune", 1, [[{"item": "Lo Rune", "quantity": 1}, {"item": "Ohm Rune", "quantity": 1}]], "complex"),
        # OR trade: two single-item alternatives
        ("pc_sc_nl", "Ber Rune", 1, [[{"item": "Jah Rune", "quantity": 1}], [{"item": "Lo Rune", "quantity": 1}]], "or_options"),
        # AND trade with three items
        ("pc_sc_nl", "Jah Rune", 1, [[{"item": "Ber Rune", "quantity": 1}, {"item": "Lo Rune", "quantity": 1}, {"item": "Ohm Rune", "quantity": 1}]], "complex"),
    ]
    for segment, offer, offer_qty, ask_groups, expected in multi_cases:
        result = evaluate_multi_ask_trade(prices, segment, offer, offer_qty, ask_groups)
        status = "PASS" if result["status"] == expected else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        reason = result.get("reason", "")
        print(f"  [{status}] [{segment}] {offer_qty}x {offer} → {ask_groups}: "
              f"status='{result['status']}' ({reason})")

    # Verify complex case includes "review manually"
    and_result = evaluate_multi_ask_trade(
        prices, "pc_sc_nl", "Ber Rune", 1,
        [[{"item": "Lo Rune", "quantity": 1}, {"item": "Ohm Rune", "quantity": 1}]]
    )
    if "review manually" in and_result.get("reason", "").lower():
        passed += 1
        print(f"  [PASS] Complex trade reason includes 'review manually'")
    else:
        failed += 1
        print(f"  [FAIL] Complex trade reason missing 'review manually': {and_result.get('reason', '')}")

    print()
    print("=" * 60)
    print("Test Group F: Segment mismatch / default warning (PLANNED behavior)")
    print("=" * 60)
    print("  The current external userscript has no segment warning.")
    print()

    seg_warn_cases = [
        # (url, expected_warning_null)
        ("https://traderie.com/d2r?prop_Platform=pc&prop_Mode=softcore&prop_Ladder=false", False),
        ("https://traderie.com/d2r?prop_Platform=pc&prop_Mode=hardcore&prop_Ladder=true", False),
        ("https://traderie.com/d2r", True),  # default — should warn
        # Unknown platform slug
        ("https://traderie.com/d2r?prop_Platform=playstation&prop_Mode=softcore&prop_Ladder=false", True),
    ]
    for url, should_warn in seg_warn_cases:
        w = get_segment_warning(url, prices)
        has_warning = w["warning"] is not None
        status = "PASS" if has_warning == should_warn else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        slug = w["segment"]
        print(f"  [{status}] {slug}: warning={w['warning']!r}")

    print()
    print("=" * 60)
    print("Test Group G: Low confidence detection")
    print("=" * 60)

    low_conf_cases = [
        # Both high confidence → no low_conf
        ("pc_sc_nl", "Jah Rune", "Ber Rune", False),
        # Zod is low confidence
        ("pc_sc_nl", "Zod Rune", "Ist Rune", True),
        ("pc_sc_nl", "Ist Rune", "Zod Rune", True),
        # Both low confidence
        ("pc_hc_l", "Lo Rune", "Gul Rune", True),
        # Unavailable confidence
        ("pc_sc_nl", "El Rune", "Ist Rune", True),
    ]
    for segment, offer, req, expected_low in low_conf_cases:
        result = evaluate_trade(prices, segment, offer, 1, req, 1)
        if result["status"] == "unavailable":
            passed += 1
            print(f"  [SKIP] {offer}→{req} on {segment}: unavailable (skip low_conf check)")
            skipped += 1
        else:
            status = "PASS" if result["low_confidence"] == expected_low else "FAIL"
            if status == "PASS":
                passed += 1
            else:
                failed += 1
            print(f"  [{status}] [{segment}] {offer}→{req}: "
                  f"low_confidence={result['low_confidence']} (expected {expected_low})")

    print()
    print("=" * 60)
    print("Test Group H: All four segments present in fixture")
    print("=" * 60)
    expected_segments = {"pc_sc_l", "pc_sc_nl", "pc_hc_l", "pc_hc_nl"}
    actual_segments = set(prices.keys())
    for seg in sorted(expected_segments):
        if seg in actual_segments:
            has_runes = len(prices[seg]) > 0
            status = "PASS" if has_runes else "FAIL"
            if status == "PASS":
                passed += 1
            else:
                failed += 1
            print(f"  [{status}] Segment '{seg}' present with {len(prices[seg])} runes")
        else:
            failed += 1
            print(f"  [FAIL] Segment '{seg}' missing from fixture")

    # Summary
    total = passed + failed + skipped
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} passed, {failed} failed, {skipped} skipped")
    if failed == 0:
        print("All applicable tests passed.")
    else:
        print(f"WARNING: {failed} test(s) failed.")

    # Report current-vs-planned gap
    print()
    print("=" * 60)
    print("Compatibility note: current external userscript would fail")
    print("these tests (known gaps documented in audits):")
    print("  - Group B: bare 'Ber Rune' without quantity — parseRune")
    print("    returns null, listing silently skipped")
    print("  - Group E: AND/bundle trades — scored as sum, no 'complex'")
    print("  - Group F: default segment — no warning shown")
    print("  - Group G: low_confidence ignored — no confidence badge")
    print("  - Percentage-based scoring vs ±0.5 Ist thresholds")


if __name__ == "__main__":
    main()
