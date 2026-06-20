# External Cash Product Contract — Schema v0.2

Generated: 2026-06-20

## Schema Evolution: Single-Source → Multi-Source

### v0.1 (Initial)

- Single source: IGGM only (30 runes, confirmed PC Non-Ladder Softcore ROTW)
- `evidence_class: "cash_market_listing"` — generic naming
- No `use_in_model` field
- No `normalized_item_name`
- No `item_type` (used `item_category` directly)
- No `price_cents`
- No per-source caveats in observations
- Basic validator: checked 5 required fields, no `use_in_model` guard

### v0.2 (This Contract — Multi-Source Hardened)

- Three sources: IGGM (30), ItemNow (33), items7 (0)
- `evidence_class: "cash_listing"` — normalized, shorter, consistent
- `use_in_model: false` — hard requirement, enforced by validator
- `normalized_item_name` — trimmed item name for cross-source matching
- `item_type` — mapped from `item_category` to controlled vocabulary (`rune`, `bundle`, `item`, `unknown`)
- `price_cents` — integer cents derived from `price_usd`
- Per-source caveats — each observation carries source-specific caveats
- Expanded validator: 11 required fields, type checks, allowed value checks

## Key Fields and Their Purpose

| Field | Purpose |
|---|---|
| `source_slug` | Identifies origin source; must match `source_manifest.json` |
| `evidence_class` | Signal type — `"cash_listing"` distinguishes from in-game trade evidence |
| `normalized_item_name` | Clean item name for joining across sources (strip whitespace, normalize casing) |
| `item_type` | Controlled vocabulary for classifying observations (rune, bundle, item, unknown) |
| `price_usd` | Cash price in USD (float) for display and comparison |
| `price_cents` | Cash price in integer cents for exact arithmetic |
| `segment_confidence` | How confident we are in the segment metadata. Defaults to `"low"` unless confirmed. |
| `use_in_model` | **Must be false.** Cash observations are external comparison only, never in-model. |
| `captured_at` | When the observation was captured (not when the source was scraped) |
| `source_url` | Optional site-level URL to the source marketplace |
| `product_url` | Optional per-item deep-link URL to the specific listing |

## Per-Source Caveats

### IGGM

- **URL:** Page-level only (`https://www.iggm.com/d2-resurrected-items`). All runes are on a single listing page — no per-item deep links exist.
- **Segment:** Confirmed PC, Non-Ladder, Softcore, ROTW from browser capture metadata. `segment_confidence: high`.
- **Parser:** Uses `<p class="item-title">` for names and `<span class="price" lkr="...">` for prices. Matched by positional index.
- **Caveat:** Prices are per-unit asking prices from a single filter combination. Other filter combinations may yield different prices.

### ItemNow

- **URL:** Site-level (`https://itemnow.com/product-category/diablo-2/runes/`). Individual product pages exist (`/product/ber-rune/`) but not captured per-observation.
- **Segment:** Base prices from WooCommerce Store API — NOT segment-specific. All 4 D2R segments have the same base price. `segment_confidence: low`.
- **Parser:** Uses public WooCommerce Store API (`/wp-json/wc/store/v1/products?category=99`). Per-segment variation prices require WC v3 API authentication (deferred).
- **Coverage:** 33 rune products (30 standard + El, Eld, Tir which IGGM does not list separately).
- **Caveat:** Prices are minimum variation prices. Some products have `price_range` with higher max prices (e.g., Ber $0.45–$39.95 per quantity).

### items7

- **Status:** 0 observations. Static HTML does not contain per-rune prices. Browser capture required.
- **Caveat:** 21 dollar amounts visible in full page text but cannot be mapped to specific rune names from static HTML alone.

## Validation Rules

The validator (`scripts/validate_external_cash_prices.py`) enforces:

1. **File exists** and is valid JSON
2. **Schema version** is 0.2+ (warns if below)
3. **Product name** is `"external_cash_prices"`
4. **Observations** is a non-empty list
5. **All required fields** exist (`source_slug`, `evidence_class`, `item_name`, `normalized_item_name`, `item_type`, `price_usd`, `price_cents`, `currency`, `segment_confidence`, `use_in_model`, `captured_at`)
6. **`use_in_model` must be `false`** — hard error if `true`
7. **`source_slug` must be non-empty** — hard error if missing
8. **`item_name` must be non-empty** — hard error if missing
9. **`price_usd` must be non-null** — hard error if null/missing
10. **`evidence_class` must be `"cash_listing"`** — hard error for any other value
11. **`item_type` must be one of** `rune`, `bundle`, `item`, `unknown`
12. **`segment_confidence` must be one of** `low`, `medium`, `high`
13. **`normalized_item_name` must exist** — warns on unusual length
14. **`source_url` and `product_url` are optional** — no error if null/missing
15. **Source slug validated against `source_manifest.json`** — hard error if not found
16. **No cash files in `data/prices/`** — hard error if found
17. **`evidence_class` must not be `completed_player_trade`** — hard error

## Future Considerations

- **Per-segment pricing from ItemNow:** WC v3 API per-variation endpoint is 401-auth protected. If access is obtained, `segment_confidence` can be upgraded to `high` and per-segment prices can be extracted.
- **items7 browser capture:** Will unlock the third source. Currently blocked by Camoufox JS rendering issues on offer detail pages.
- **Product URLs:** For sources with per-item pages (ItemNow, PlayerAuctions), future parser improvements should capture `product_url` per observation.
- **New sources:** G2G, PlayerAuctions, Odealo, AOEAH are all candidates. Each will need a parser and per-source caveats added to the generator.
- **`price_cents` quality:** Currently derived from `price_usd * 100`. Future parsers should extract integer cents directly from source data where available.
