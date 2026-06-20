# External Cash Prices Prototype — v0

Generated: 2026-06-20

## Artifacts Parsed

| Source | Artifact | Method | Result |
|---|---|---|---|
| IGGM | `captures/iggm_2026-06-20_browser-smoke/page.html` | Offline parser from browser-captured rendered HTML | 30 rune prices extracted |
| items7 | `downloads/rune_sources_2026-06-20/items7.html` | Static HTML inspection | 0 prices — static HTML lacks per-rune data |

## Rows Extracted

**IGGM: 30 rows** — all 30 D2R runes with prices:

| High Runes | Mid Runes | Low Runes |
|---|---|---|
| Zod $8.99 | Vex $0.89 | Lem $0.12 |
| Cham $4.99 | Gul $0.39 | Ko $0.12 |
| Jah $7.90 | Ist $0.49 | Fal $0.12 |
| Ber $7.29 | Mal $0.29 | Lum $0.12 |
| Sur $4.29 | Um $0.19 | Hel/Dol/Shael/Sol/etc $0.09 |
| Lo $2.79 | Pul $0.22 | |
| Ohm $1.79 | | |

**items7: 0 rows** — static capture does not contain per-rune prices.

## Sample Observations

```json
{
  "source_slug": "iggm",
  "evidence_class": "cash_market_listing",
  "item_name": "Jah",
  "item_slug": "jah_rune",
  "price": 7.90,
  "currency": "USD",
  "platform": "pc",
  "segment_confidence": "low",
  "raw_text": "Jah – #31",
  "parser_notes": "Price from IGGM browser-captured rendered HTML..."
}
```

## Segment Context (Updated)

After focus capture: **PC, Non-Ladder, Softcore, ROTW** detected from page content.

Segment confidence improved from `low` to `high` — all four dimensions (platform, ladder, hardcore, season) were detected from the focused capture metadata.

30 rune prices re-parsed from focused capture with `segment_confidence: high`. No price changes between the two captures — prices are consistent regardless of which page view was used.

## Known Caveats

1. ~~Segment ambiguity~~ **Resolved.** Segment context confirmed: PC, Non-Ladder, Softcore, ROTW. All 30 prices tagged `segment_confidence: high`.
2. **Asking prices only**: These are seller listing prices, not completed transaction prices.
3. **Single segment**: Only one filter combination was captured. Prices may differ for Ladder, Hardcore, or other platforms.
4. **items7 incomplete**: Static capture was insufficient. Needs a browser capture to render per-rune prices.

## Parser Reliability for v0

| Source | Ready for v0? | Why |
|---|---|---|
| IGGM | **Yes** | Clean `lkr` attribute extraction. 30/30 runes with prices. Segment context confirmed. Parser supports `--input-dir`. |
| items7 | No | Per-rune prices not available in static HTML. Needs browser capture. |

## Parser Implementation Notes

- IGGM parser uses `<p class="item-title">` for rune names and `<span class="price" lkr="...">` for numeric prices.
- Both elements appear sequentially in the DOM — matching by positional index works.
- The `lkr` attribute is the raw numeric price (no formatting or currency symbol).
- Rune names are extracted from the title text (e.g. "Zod – #33" -> "Zod").
- Parser now accepts `--input-dir` to point at any IGGM capture directory.

## Recommended Next Source to Add

**items7 browser capture** — to get per-rune prices from their rendered DOM. This is the last remaining hole in the external cash price v0.


## Files Created

| File | Description |
|---|---|
| `scripts/parse_iggm_offline.py` | IGGM rendered HTML parser |
| `scripts/parse_items7_offline.py` | items7 static HTML parser (notes limitation) |
| `scripts/generate_external_cash_prices.py` | Merges per-source outputs into product schema |
| `scripts/validate_external_cash_prices.py` | Validates product file |
| `data/external/iggm_cash_prices.json` | 30 IGGM rune prices |
| `data/external/items7_cash_prices.json` | 0 prices (documents limitation) |
| `data/products/external_cash_prices.sample.json` | Normalized product file |
