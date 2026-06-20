# Process Correction: Diablo2.io Sold-Trade Discovery

Date: 2026-06-20

## What Was Missed

Diablo2.io was initially classified as a `forum_reference` / qualitative source. Its explicit Sold trade-search surface (`activesold=1`) was not identified during initial source discovery.

## Why It Was Missed

- Initial evaluation only included a quick browse of the homepage and `browsetrades.php` (active listings).
- The Sold filter is not on the main navigation — it requires using the search page with `activesold=1` query parameter.
- The site's item page "Sold for" history was noted, but the dedicated Sold search was not investigated.
- No D2R-specific search terms (sold, completed, WTS SOLD, WTB SOLD) were used during initial discovery.

## How the Source Workflow Is Changing

1. A mandatory source surface checklist is being added to `docs/SOURCE_MANIFEST.md`.
2. A classification rule is being added to `research/memos/2026-06-20-source-discovery-workflow.md`: agents must explicitly search for sold/completed trade surfaces before classifying a source.
3. D2R-specific search terms are being added to the discovery workflow.
4. `data/source_manifest.json` now tracks `surfaces_checked` for each source.

## Why Diablo2.io Should Move to tier_1_candidate

- Diablo2.io has a sold-trade search surface that exposes structured completed-trade evidence.
- Rows include WTS/WTB side, seller, buyer (sometimes), accepted consideration, and relative sale time.
- Examples include clean rune-for-rune trades: 11 Ist, 2 Ber, 1 Sur 1 Lo, 2 Vex 2 Gul 2 Mal.
- This is the closest second completed-player-trade source to Traderie identified so far.
- It may provide an independent cross-validation source for rune pricing.

## Exact Parser Fixture to Build Next

Input:
- `research/sources/captures/diablo2io/2026-06-20_jah_sold_search/rendered.html`

Output:
- `data/research/diablo2io_sold_jah_trades.sample.json`

Parser: `scripts/parse_diablo2io_sold_search_offline.py`

Requirements:
- Fixture-only, no network.
- Extract SOLD rows.
- Preserve raw row text.
- Parse WTS/WTB, target quantity, target item, sold time, seller, buyer, consideration.
- Every row gets `use_in_model: false`.
- Output is research-only.

## Remaining Caveats

- Parser must validate that rows represent actual completed trades.
- Rows may lack buyer or structured consideration.
- Segment filters must be parsed, not assumed.
- Do not blend Diablo2.io with Traderie until source comparison is complete.
