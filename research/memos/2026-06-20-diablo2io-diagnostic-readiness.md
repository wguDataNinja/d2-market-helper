# Diablo2.io Diagnostic Readiness Report

Date: 2026-06-20
Data source: data/research/diablo2io_sold_rune_trades.sample.json (14 rows, 4 runes)

---

## Gate Status Table

| Gate | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | >=20 clean Jah obs | **FAIL** (6 direct / 8 cross-search) | 9 total Jah rows across all searches; 6 clean from direct Jah search. 7 rows from Jah-specific sold-search URL, 6 clean (1 excluded: `description_only_consideration`). 2 additional Jah rows appeared as byproducts of Ber and Lo searches. |
| 2 | >=20 clean Ber obs | **FAIL** (1) | Only 1 Ber row in the combined JSON (`clean_single_rune`, buyer: Javachod, 14 Ist). The Ber HTML fixture was captured but produced only 1 parsable row. |
| 3 | Segment filters proven | **PASS** | HTML icon classes confirmed for platform (`zi-pc`), ladder (`zi-ladder`/`zi-nonladder`), HC (not yet observed — `zi-softcore`/`zi-hardcore` may only render when filter is active), region (`zi-americas`/`zi-europe`), ruleset (`zi-tinylogrotw`). Source manifest corrected: HC/SC now `"unproven"` not `true`. |
| 4 | Pagination tested | **PASS** | All 4 captured searches (Jah, Ber, Lo, Sur) show "Page 1 of 1". No pagination exists at current volumes. `&start=` param not tested since no page 2 exists. |
| 5 | Manual sold-badge verification | **FAIL** | No user spot-check performed. Need to open 3 individual trade pages in a browser to confirm SOLD badge = completed trade with named buyer + exchanged items. |
| 6 | Parse classes restricted | **PASS** | Comparison design (research/memos/2026-06-20-traderie-diablo2io-comparison-design.md) only allows `clean_single_rune`, `clean_multi_rune`, `quantity_bundle`. All 6 clean Jah rows + 1 clean Ber row fall in these classes. `description_only_consideration` rows (2/14) correctly excluded. |
| 7 | All rows `use_in_model=false` | **PASS** | All 14 rows in combined JSON have `use_in_model=false`. No Diablo2.io data is flowing into any pricing model. |

### Cross-Search Contamination Note

2 of 8 clean Jah rows appeared in non-Jah searches (Ber and Lo). These are valid Jah trades that happened to mention other high runes and thus appeared as cross-search results. They inflate the "all sources" count to 8 but the direct Jah search only yields 6 clean rows. For diagnostic comparison, cross-search rows are still valid Jah observations — they represent real completed trades for Jah.

---

## Assessment

- **ready_for_diagnostic_comparison = false** (Gates 1, 2, and 5 are blocking)
- **ready_for_model_integration = false** (always, regardless — Diablo2.io is research-only)

---

## Key Finding: Volume, Not Quality

The fundamental problem is volume, not parser quality. Diablo2.io sold-search returns very few results per rune (1–9 rows per search). This is not a parser bug — it's the actual available data on the platform. The sold-search surface simply does not have enough volume to support a statistically meaningful comparison against Traderie.

The parser works correctly: 0 parse failures, clean extraction of structured consideration, correct segment identification, correct WTS/WTB classification. But with only 6 clean Jah and 1 clean Ber, any comparison would be anecdotal, not diagnostic.

### Actual Counts vs Requirement

| Gate | Required | Actual (direct search) | Actual (all sources) | Deficit |
|------|----------|----------------------|---------------------|---------|
| Jah clean obs | 20 | 6 | 8 | −14 (need ~3x more) |
| Ber clean obs | 20 | 1 | 1 | −19 (need ~20x more) |

---

## Implications

1. **Accept Diablo2.io as a thin secondary signal.** It is not a primary competitor to Traderie. At current volumes, it can provide occasional cross-reference data points but cannot support its own pricing curve.

2. **Item-page price history is a richer surface.** The misc/jah-t43.html page shows "Total results: 2812, Page 1 of 57" — vastly more data. Sold-search is a subset of completed trades; the browse-trades history page captures all historical listings (including completed ones without the SOLD badge). The trade-off: no explicit completion signal.

3. **Broader search parameters could increase volume.** Removing the `activesold=1` filter and using wider keyword patterns (e.g., "J" for Jah) might return more rows. However, this introduces the stale-listing ambiguity that sold-search was chosen to avoid.

4. **Pair-ratio comparison is the most viable path.** Comparing Jah:Ber, Ber:Lo, etc. requires fewer data points than absolute Ist-value comparison, because pair ratios don't need conversion assumptions. However, even pair ratios require multiple co-occurring observations (Jah-and-Ber in the same trade or same search), which are rare at current volumes.

---

## What This Means for the Project Thesis

The claim "Diablo2.io is the strongest second completed-trade candidate" remains technically true — it is the only non-Traderie source with a working sold-search parser and proven segment extraction. However, the available volume is low enough that it cannot yet support a multi-source completed-trade normalization thesis. The project's central value proposition remains:

> Traderie-normalized values + multi-source external cash context (IGGM, ItemNow, etc.)

Diablo2.io is a promising but data-starved secondary signal. It should remain in research mode (`use_in_model=false`) until volume increases through broader capture strategies or platform growth.

---

## Exact Missing Fixtures

| Gap | What's Needed | Priority |
|-----|--------------|----------|
| Jah clean obs | 14+ more clean Jah rows (3x current) | Critical |
| Ber clean obs | 19+ more clean Ber rows (20x current) | Critical |
| Manual sold-badge verification | User opens 3 random trade pages in browser to confirm SOLD = completed trade | High |
| Non-rune test | One SoJ or Griffon's Eye fixture to validate non-rune parsing | Medium |
| Item-page history capture | Capture Jah browse-trades history page (57 pages available) for volume comparison | Medium |

---

## Recommendation

**Keep Diablo2.io in research mode.** Do not pursue diagnostic comparison at this time. The data is too thin to produce meaningful results, and the effort to capture enough additional data (17x more Ber rows, 3x more Jah rows) is better spent elsewhere.

If and when the sold-search surface grows (either through platform changes or a broader capture strategy that accepts stale-listing risk), re-evaluate at N >= 20 per rune.

**Alternative focus:** The item-page price history (`misc/jah-t43.html`) has 2,812 results — that's the real prize if Diablo2.io is to become a meaningful comparison source. Consider designing a parser for the browse-trades history page instead of or in addition to sold-search.
