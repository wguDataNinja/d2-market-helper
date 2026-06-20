# Diablo2.io Sold-Search Semantic Validation Report

Date: 2026-06-20
Author: Automated research pipeline (Agent Q + Agent R)

---

## 1. Fixture Coverage

| Item | Pages Captured | Total Rows | Clean Rows | Excluded Rows | Parsed JSON |
|------|---------------|-----------|------------|---------------|-------------|
| Jah Rune | 1 (page 1 of 7 rows) | 7 | 6 | 1 | `diablo2io_sold_jah_trades.sample.json` |
| Ber Rune | 0 (HTML captured but not yet parsed) | — | — | — | `diablo2io_sold_ber_trades.sample.json` (placeholder: `not_captured`) |
| Combined | — | — | — | — | `diablo2io_sold_rune_trades.sample.json` (file does not exist) |

### Segment Evidence Found (Jah fixture, 7 rows)

| Segment | Evidence | Proven? |
|---------|----------|---------|
| Platform | `zi-pc` icon class (7/7 rows) | ✅ Confirmed — all PC |
| Ladder | `zi-nonladder` (6/7), `zi-ladder` (1/7) | ✅ Confirmed |
| Hardcore/SC | Neither `zi-softcore` nor `zi-hardcore` found (0/7) | ❌ Not confirmed — every row is softcore by default; class may only render when HC filter is active |
| Region | `zi-americas` (4/7), `zi-europe` (2/7), absent (1/7) | ✅ Confirmed when present |
| Ruleset | `zi-tinylogrotw` (7/7) | ✅ Confirmed — all RotW |
| Side (WTS/WTB) | `z-trusty-wtbs` title attribute | ✅ Confirmed — WTS (6/7), WTB (1/7) |
| Sold status | `activesold=1` URL param + explicit SOLD badge text | ✅ Confirmed — all rows are sold-search results |

**Segment confidence per row:** All 7 rows have 3–4 known dimensions (platform, ladder, ruleset + optional region). No row reaches 5 dimensions because hardcore/softcore is never explicitly shown.

---

## 2. Parse Quality

### Parse Class Distribution (Jah fixture, 7 rows)

| parse_class | Count | Eligible for model? |
|------------|-------|-------------------|
| `clean_single_rune` | 1 | Yes |
| `clean_multi_rune` | 4 | Yes |
| `quantity_bundle` | 1 | Yes (with normalization) |
| `description_only_consideration` | 1 | No |
| `missing_consideration` | 0 | No |
| `ambiguous_direction` | 0 | No |
| `non_rune_price` | 0 | No |
| `parse_failed` | 0 | No |

**Clean rows (eligible): 6 | Excluded rows: 1 | Total: 7**

### Excluded Row Detail

**Row 2 (index 2):** ZET-U, "WTS SOLD Jah", `description_only_consideration`
- No structured `for <qty> <item>` in sale line (sale line ends at "by ZET-U")
- No buyer (`buyer: null`)
- Description is free text ("O: Jah N: Ber") — Offer/Negotiate format, not a confirmed accepted price
- 0 offers on the thread further suggest no binding agreement
- **Verdict:** Correctly excluded. Cannot confirm consideration was actually accepted.

### Parse Edge Cases Observed

1. **`raw_sale_line` token duplication:** "for" is prepended per consideration item, producing "for 1 Sur for 1 Lo" instead of "for 1 Sur, 1 Lo". Cosmetic — the structured `consideration` array is correct (rows 1, 4, 5, 6).

2. **Quantity bundle (row 3):** "2 Jah for 2 Ber" — correct normalization divides both sides by 2 → 1 Jah = 1 Ber. Clean parse.

3. **WTB row (row 0):** "WTB SOLD Jah for 11 Ist" — parser correctly identifies the poster (Ctaylorheck) as the buyer. Consideration (11 Ist) is what the buyer paid. No inversion needed.

4. **Missing region (row 4):** Volarmis trade has no region icon class — segment shows `region: "unknown"`. Still gets `medium` confidence from 3 known dimensions (platform, ladder, ruleset).

5. **Zero parse failures:** The `classify_parse` function handled all 7 rows without falling through to `parse_failed`.

---

## 3. Evidence Strength Assessment

### Why Sold-Search Rows Are Stronger Than Active Listings

| Attribute | Sold Search (`activesold=1`) | Active Listings (`browsetrades.php`) |
|-----------|-----------------------------|--------------------------------------|
| Completion signal | Explicit SOLD badge on the thread | No badge — listing may be stale, withdrawn, or still open |
| Accepted price | Structured `for <qty> <item>` parsed from HTML deets block | Asking price only — may not reflect final trade value |
| Buyer identity | Named buyer present in 6/7 rows (86%) | No buyer — no counterparty |
| Seller identity | Named seller in 7/7 rows (100%) | Poster identity only |
| Timestamp | Relative + absolute timestamp (e.g., "15 hours ago" + "Fri Jun 19, 2026 4:47 pm") | Listing creation time only — no completion time |
| Offers count | 0–4 offers visible per row | No completion data |

Sold-search rows represent **ex-post recorded trades** rather than ex-ante offers. The structured "for ..." clause in the HTML deets block is parsed from machine-readable spans, not free-text description — reducing the risk of misinterpreting asking prices as accepted prices.

### Remaining Ambiguity

**1. Is the sold badge reliable?**

A seller manually marks their thread as SOLD. Possible failure modes:
- **False sold:** A seller marks sold after trading elsewhere (the thread was a duplicate, or they sold on another platform). The badge would appear without an actual trade occurring through this thread.
- **No-show sold:** A seller marks sold because they gave up trying to trade, not because a trade completed.
- **Accidental sold:** Misclick or test click.

Mitigation: The presence of a named **buyer** in the sale line (6/7 rows) strongly suggests a two-party exchange actually happened. The platform records "Sold by X to Y for Z" — this is rendered server-side, not entered by the user. Absent a buyer (row 2), confidence drops sharply.

**2. Are rows with missing buyer or missing "for ..." still valid?**

- **Missing buyer (row 2):** Possible, but weak. The SOLD badge alone is not sufficient — seller may have marked sold for non-trade reasons. Recommendation: require a named buyer for model inclusion.
- **Missing "for ..." (row 2):** Cannot infer consideration from free-text description. Formats vary wildly ("O: X N: Y", "LF X", "FT: X ISO: Y", "N X", etc.). Structured HTML spans are the only reliable source.

**3. Does WTB SOLD mean the buyer is offering the consideration, or the seller?**

Interpretation confirmed: In a WTB SOLD row, the **poster** is the buyer. The sale line "Sold by [poster] to [counterparty] for [consideration]" means the poster (buyer) paid the consideration. The numeric price is identical to a WTS row — the good flows opposite to the runes, but the `consideration` array represents what the buyer paid, which is the correct economic value. WTB rows are valid price signals and should not be inverted.

---

## 4. Segment Validation

### Proven Segment Fields (from HTML icon classes)

| Dimension | HTML Class(es) | Status | Notes |
|-----------|---------------|--------|-------|
| Platform | `zi-pc`, `zi-switch`, `zi-xbox`, `zi-ps` | ✅ Proven | All 7 Jah rows are `zi-pc`. Probe confirms Switch/Xbox/PS classes exist on browsetrades page. |
| Ladder | `zi-ladder`, `zi-nonladder` | ✅ Proven | 6 non-ladder + 1 ladder in Jah fixture. |
| Hardcore | `zi-hardcore`, `zi-softcore` | ❌ Not observed | 0/7 rows have either class. Need a fixture with explicit HC filter active. Probe confirms HC filter (`hc=1`) reduces result count from 11 to 7. |
| Region | `zi-americas`, `zi-europe` | ✅ Proven when present | 4 americas, 2 europe, 1 absent. |
| Ruleset | `zi-tinylogrotw` | ✅ Proven | 7/7 rows are RotW. |
| Trade side | `z-trusty-wtbs` title attr | ✅ Proven | 6 WTS, 1 WTB. |
| Sold status | `activesold=1` param + sold_class div | ✅ Proven | All rows. |

### Remaining Unknowns

1. **Whether prices differ by segment:** We have 6 clean rows but they span mixed segments (ladder/non-ladder, americas/europe). The sample is too small to compare prices across segments. Need same-item captures with different filter combinations (e.g., Jah ladder only vs Jah non-ladder only).

2. **Whether URL filters actually change results:** Probe confirms HC filter changes count (11 → 7). But the `sc=0` (ladder=off) parameter in the current Jah URL didn't fully filter — 1 ladder row appeared anyway. This suggests the search results may not fully respect all filter params when searching from the sold-search page (as opposed to the browse-trades page which has richer filter UI). Need side-by-side captured HTML to verify exact URL param → result correspondence.

---

## 5. Model Eligibility Gate

**Current status: `use_in_model=false` (research-only)**

### Blockers — detailed status

| # | Blocker | Requirement | Status | Passing? |
|---|---------|-------------|--------|----------|
| 1 | Minimum observations | N ≥ 20 clean observations per rune | Jah: 6 clean rows (fails). Ber: not captured (fails). | ❌ **Blocking** |
| 2 | Agreement vs Traderie | Diagnostic comparison report against Traderie completed trades | Not started. Requires both sources to have sufficient samples. | ❌ **Blocking** |
| 3 | Segment-specific captures | At least one alternate filter set captured and parsed (e.g., HC-only) | Ber HC HTML captured (171KB) but not parsed. No parsed segment-specific JSON. | ❌ **Blocking** |
| 4 | Sold badge verification | Manual spot-check of 3 rows to confirm "sold" = completed trade | Not performed. Need to open 3 individual trade pages and verify the thread shows completed trade evidence. | ❌ **Blocking** |
| 5 | Pagination depth | At least 3 pages for one item (to assess volume sufficiency) | Jah page 2 HTML captured (114KB) but not parsed. No page 3 captured. | ❌ **Blocking** |

**Blocker severity:** All 5 are blocking. Not even close on any.

---

## 6. Recommended Next Fixtures

Priority order:

1. **Parse the Ber HC fixture** (HTML already captured: `ber_sold_hc_filter.html`)
   - Rationale: Closes the HC segment gap. Proves `zi-softcore`/`zi-hardcore` appear when HC filter is active. Also adds Ber clean rows to the evidence base.

2. **Parse Jah page 2** (HTML already captured: `jah_sold_page2.html`)
   - Rationale: Tests pagination-based extraction. Adds rows (probe shows `sold_class=3` on page 2).

3. **Lo sold search** (new capture needed)
   - Rationale: Tests another mid-high rune. Lo is adjacent to Sur in the rune hierarchy and commonly traded. Validates the parser works for non-Jah/Ber search terms.

4. **Sur sold search** (new capture needed)
   - Rationale: Sur appears as consideration in Jah rows (rows 4, 5). Having a Sur direct-sold fixture would provide cross-reference data.

5. **Jah page 3** (new capture needed, `&start=100`)
   - Rationale: Would meet the 3-page depth requirement for blocker #5.

6. **SoJ or Griffon's Eye sold search** (new capture needed)
   - Rationale: Tests non-rune parsing. Validates `non_rune_price` detection and ITEM_NAME_MAP for unique items.

---

## Decision Statement

**Status: `parser_prototype_ready` but not integrated.** Diablo2.io sold-search is a promising completed-trade source with strong structural advantages over active listings. The Jah fixture proves the parser works correctly on 7 rows with 0 parse failures and 6 clean rows. However, the evidence base is far too thin for any model integration — only one item (Jah) has been parsed, Ber is uncaptured, no segment comparisons exist, and the sold badge's reliability is unverified. Candidate for source comparison against Traderie after at least 3 more fixtures are captured, parsed, and validated.
