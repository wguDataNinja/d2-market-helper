# Diablo2.io Parser Validation Plan

Date: 2026-06-20
Fixture: Jah sold search (7 sold rows)

## Clean Rows Eligible for Future Model Review

### Acceptable parse_classes

| parse_class | Eligible? | Count in fixture |
|---|---|---|
| `clean_single_rune` | Yes | 1 (Row 0) |
| `clean_multi_rune` | Yes | 4 (Rows 1, 4, 5, 6) |
| `quantity_bundle` | Yes, with normalization | 1 (Row 3) |

### Eligible row indices and key attributes

| Row | parse_class | Jah Qty | Consideration | Buyer present | Side |
|---|---|---|---|---|---|
| 0 | clean_single_rune | 1 | 11 Ist | yes (varangium) | WTB |
| 1 | clean_multi_rune | 1 | 1 Cham + 1 Ist | yes (varangium) | WTS |
| 3 | quantity_bundle | 2 | 2 Ber | yes (LyonCZ) | WTS |
| 4 | clean_multi_rune | 1 | 1 Sur + 1 Lo | yes (Zampag) | WTS |
| 5 | clean_multi_rune | 1 | 2 Sur + 1 Ohm | yes (Johnny-23) | WTS |
| 6 | clean_multi_rune | 1 | 2 Vex + 2 Gul + 2 Mal | yes (LyonCZ) | WTS |

### Thresholds for model-readiness

1. **Buyer must be confirmed** — a named `buyer` in the sale line is the strongest signal of a completed two-party trade.
2. **Consideration must be structured** (not inferred from description) — the `for <qty> <item>` chain in the HTML deets block is reliable; description text is not.
3. **All consideration items must be runes** — non-rune prices would need a different pricing model and are currently excluded.
4. **Target item icon matches the searched item** — confirms the row is actually about Jah, not a miscategorized post.
5. **Side must be clearly WTS or WTB** — both are usable but interpreted differently (see WTS vs WTB section).
6. **Segment must have at least medium confidence** (3+ known dimensions).

Rows meeting all 6 thresholds: **0, 1, 3, 4, 5, 6** (6 of 7).

## Excluded Rows and Why

### description_only_consideration (Row 2)

- **Row:** ZET-U, "O: Jah N: Ber", no buyer, no structured `for ...` clause
- **Why excluded:** The description `"O: Jah N: Ber"` suggests an offer (Offer/Negotiate) format, not a confirmed consideration. Without a structured `for <qty> <item>` in the sale-line deets block, we cannot confirm what consideration was actually accepted. The raw description is free text entered by the poster and may reflect an asking price, wish list, or negotiation history — not the final trade terms. 0 offers further suggests no binding agreement was reached in-thread.
- **Verdict:** Not usable for pricing until we can verify the actual accepted offer (requires scraping the individual trade page).

### missing_consideration

- **Not present in this fixture**, but the parser supports it via the `classify_parse` fallthrough when both consideration and description are empty.
- **Why excluded:** No structured `for ...` clause means no machine-readable price. The parser cannot distinguish between "the sale line was truncated" and "the trade had no itemized consideration."

### ambiguous_direction

- **Not present in this fixture.** Would apply if the HTML showed both WTS and WTB badges, or if the side could not be determined from the `z-trusty-wtbs` class/title.

### non_rune_price

- **Not present in this fixture.** Would apply if consideration includes non-rune items (e.g., "3 Ist + Shako"). Non-rune items lack a standardized value in the rune-pricing model and would need external valuation.

### parse_failed

- **Not present in this fixture.** Catch-all for rows where `classify_parse` reaches no known branch (should not happen with the current logic).

## WTS vs WTB Handling

### How Diablo2.io marks side

The side is embedded in the `span.z-trusty-wtbs` element's `title` attribute:
- `title="Want to Buy"` → WTB (buyer is posting they want to purchase)
- `title="Want to Sell"` → WTS (seller is posting they want to sell)

When marked SOLD by the seller, the seller's original intent is preserved.

### WTB SOLD interpretation (Row 0)

**Example:** "WTB SOLD Jah ... for 11 Ist" — Ctaylorheck posted WTB Jah for 11 Ist, then marked it sold.

- The poster (Ctaylorheck) is the **buyer** in the original WTB intent.
- The "seller" field in the sale line (`by Ctaylorheck`) is the **poster**, not the direction of the trade. The SOLD badge means the poster (buyer) found their item.
- "Sold by Ctaylorheck to varangium for 11 Ist" means Ctaylorheck (the WTB poster, acting as buyer) paid 11 Ist to varangium (the seller).
- **Interpretation:** The consideration (11 Ist) is what the WTB poster paid. This is the same economic reality as a WTS row where the seller receives the consideration — the good flows opposite to the runes. But the numeric price (11 Ist for 1 Jah) is the same.

### Recommendation for WTB in a future model

1. **Do NOT invert the consideration.** Whether WTB or WTS, the consideration listed in the structured `for ...` block is the set of items that changed hands from buyer to seller. The economic price of Jah is the same regardless of which side posted the thread.
2. **Normalize the `trade_side` field** but keep the original value for traceability. A future model should have a field like `payer_is_poster: true` for WTB rows to flag the inversion.
3. **WTB rows are valid price signals** and should not be excluded solely on side.
4. **Confidence adjustment:** WTB rows may have slightly lower confidence because the poster (buyer) may have accepted a different price than their original offer — but this is equally true of WTS rows where the seller may have accepted less than asking.

## Quantity Bundle Handling

### Row 3: 2 Jah for 2 Ber

**How to normalize:**

The simplest and most transparent normalization:
- Divide both quantities by the Jah quantity: `2 Ber / 2 Jah = 1 Ber per Jah`
- The ratio is Jah:Ber = 1.0 (1 Jah = 1 Ber)
- This is a clean 1:1 swap and can be treated as a single-unit trade after normalization.

**Alternative:** Keep as a bundle and weight it differently. Rationale: bulk trades may get better rates. However, 2:2 is already at parity, so no discount/premium is observable.

### Weighting consideration

- **Preferred approach:** Normalize to per-unit (divide consideration by target_quantity). This maximizes comparability with single-quantity rows.
- **If bundling discount is suspected:** Track both raw and normalized values. A future model could test for a quantity discount signal.
- **Weight in aggregation:** Quantity-bundle rows could be given lower weight in a model to account for the possibility of bulk pricing effects, but with only 1 of 7 rows in this fixture, the impact is minimal.

### When NOT to normalize

If the bundle contains heterogeneous items (e.g., 2 Jah for 1 Ber + 1 Sur), per-unit normalization is ambiguous. Only normalize when consideration items are divisible and identical across units.

## Missing Buyer / Missing "for ..." Handling

### Rows without explicit "to <buyer>" (Row 2)

- **Are they still valid completed trades?** The SOLD badge alone is not sufficient. The seller manually marks the thread as sold, which could happen for reasons other than a completed trade (e.g., item traded elsewhere, no longer for sale, accidental).
- **Confidence rule:** Buyer presence significantly increases confidence. Without a named buyer, the evidence is weaker.

### Rows without "for <consideration>" (Row 2)

- **Can consideration be inferred from description?** Possibly, but risky. The description "O: Jah N: Ber" suggests Ber was offered, but this is user-generated text with no standardized format. Different users write "O: X N: Y", "LF X", "FT: X ISO: Y", etc. Parsing all variants is unreliable.
- **Recommendation:** Do not infer consideration from description in the offline parser. Description inference should be a separate, higher-risk parse_class (already captured as `description_only_consideration`).

### Confidence rules for incomplete rows

| Criteria | Confidence tier | Example rows |
|---|---|---|
| Has buyer + structured consideration | high | 0, 1, 3, 4, 5, 6 |
| Has structured consideration, no buyer | medium | (none in fixture) |
| Has buyer, no structured consideration | low | (none in fixture) |
| Has neither buyer nor structured consideration | very low | Row 2 |

## Segment Fields Proven vs Unknown

### Proven dimensions (from fixture HTML)

| Segment | Classes found | Proven? |
|---|---|---|
| Ladder / Non-ladder | `zi-nonladder` (6 rows), `zi-ladder` (1 row) | **Confirmed** — visible icon class on each row |
| Platform | `zi-pc` (7 rows) | **Confirmed** — all rows are PC |
| Region | `zi-americas` (4 rows), `zi-europe` (2 rows), absent (1 row) | **Confirmed when present** — NA or EU icon visible; absence means unknown |
| Ruleset | `zi-tinylogrotw` (7 rows) | **Confirmed** — all rows are RotW |
| Hardcore / Softcore | Neither `zi-softcore` nor `zi-hardcore` found | **Not confirmed in current fixture** — every row is softcore (default) or hardcore is not shown on the search results page; need a fixture with explicit HC/SC filter |

### Confidence levels

| Known dimensions | Confidence | Count in fixture |
|---|---|---|
| 4+ | high | 0 |
| 3 | medium | 7 |
| 2 | low | 0 |
| 1 or 0 | very low | 0 |

All 7 rows have exactly 3 known dimensions (ladder, platform, ruleset) or 4 (ladder, platform, region, ruleset), earning `medium` confidence. To reach `high` (5 known), we need to confirm hardcore/softcore.

## Next Fixtures Required

| Priority | Fixture | Rationale |
|---|---|---|
| P0 | Ber rune sold search | Multi-item test; fills gaps in ITEM_NAME_MAP; checks if parser works for other rune icons |
| P1 | Sold search with explicit HC filter | Proves `zi-softcore`/`zi-hardcore` appear in HTML; closes the hardcore segment gap |
| P1 | Sold search with explicit SC filter | Confirms `zi-softcore` class exists in search results |
| P2 | Sold search page 2 (pagination) | Tests `extract_containers` pagination behavior; checks if page structure changes |
| P2 | Sold search with non-rune item (e.g., Griffon's) | Tests `non_rune_price` parse_class and ITEM_NAME_MAP extensibility |
| P3 | Sold search with explicit region+segment URL params | Tests if segment classes change when URL has `&region=2&hc=1` etc. |

### Why Ber is the best next target

Ber is the other T1 rune, directly comparable to Jah. The ITEM_NAME_MAP already has `runeBer_sicon`. Ber's fixture would double the evidence base and test the parser against a different search term without requiring code changes.

## Parser Improvements Needed

### Current issues

1. **raw_sale_line generation duplicates "for" tokens** (line 270-283): The `extract_raw_sale_line` function has dead code (empty `elif` on line 279-281). The "for" token is prepended per consideration item, producing strings like "Sold ... for 1 Cham for 1 Ist" instead of "Sold ... for 1 Cham, 1 Ist". This is cosmetic only — the structured `consideration` array is correct.

2. **No segment confidence for missing region** (line 222-246): Container 5 (ladder, no region) gets `medium` confidence with 3 known dimensions (ladder, platform, ruleset). This is acceptable but should be documented.

3. **Side extraction relies on title attribute** (line 96-104): If the `title` attribute is absent or renamed, the regex for `z-trusty-wtbs` still captures the class but returns "unknown". This is a safe fallthrough but could miss side.

4. **No validation that target_item matches searched uitemid** (line 121-131): The parser extracts whatever item icon is first in the container. If a post is miscategorized (e.g., a Ber post in a Jah search), the parser would extract Ber but still use the Jah URL. This should be validated in a future iteration.

5. **Missing `ambiguous_direction` trigger**: The parser never sets `ambiguous_direction` — if `extract_side` returns "unknown", the row goes into whichever parse_class fits, but the side is "unknown". There should be a pre-classify gate that sets parse_class to `ambiguous_direction` when side is unknown.

### Additional parse_classes needed

| parse_class | When to use | Priority |
|---|---|---|
| `side_unknown` | When `extract_side` returns "unknown" | Medium — didn't occur in fixture but should be handled |
| `description_inferred_consideration` | When consideration is inferred from description using a known format (e.g., "O: X N: Y") | Low — requires format-specific patterns |

### Validation rules before consideration can be trusted

1. Sale line must contain `for <qty> <item>` structured elements (not just description text).
2. Buyer must be a named user (not null, not "Guest").
3. Consideration items must all be known runes (in RUNE_NAMES).
4. Target item must match the searched item (uitemid parameter).
5. Side must not be "unknown".

## Key Rule Restated

**All Diablo2.io observations remain `use_in_model=false`.** This memo is a validation plan only — no data from this source enters pricing until a future review explicitly changes this flag.
