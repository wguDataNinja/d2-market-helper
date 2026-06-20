# ItemNow Cash Parser — 2026-06-20

## Parser Approach

`scripts/parse_itemnow_api.py` uses the **public WooCommerce Store API** at:

```
https://itemnow.com/wp-json/wc/store/v1/products?category=99&per_page=100
```

No authentication required. Returns JSON with all products in the "Runes" category.

## Key Design Decisions

### Store API Only
- Uses only the public `/wp-json/wc/store/v1/products` endpoint.
- No WooCommerce v3 admin API (requires auth).
- No HTML scraping or browser rendering.

### Rune Name Normalization
- Product names parsed via regex `^([A-Z][a-z]+) Rune$` → extract short name (e.g., "Cham" from "Cham Rune").
- Short name lowercased → looked up in `data/rune_registry.json`.
- Registry provides: `normalized_item_name`, `rune_order`, `item_name`, `item_slug`.
- All 33 runes matched successfully (Hel Rune included at rune_order=15).

### Bundle Handling
- Products with "Multiple Rune Package" in name tagged as `item_category: "bundle"`.
- Bundles preserved in output but marked `use_in_model: false`.
- 9 bundles detected (5×, 10×, 20×, 40×, 88×, 176×, 352× "Any Runes" packs + 2 specific Jah/Ber packs).

### Segment Handling
- All products have a `server` attribute with multiple `terms` (14 terms for runes, 7 for bundles).
- D2R Ladder, D2R Non-Ladder, D2R HC Ladder, D2R HC Non-Ladder confirmed in attribute terms.
- **Segment confidence: "low"** — Store API returns only the base price (minimum variation price).
- Per-segment prices require WooCommerce v3 API variation access (auth-locked) or individual product page scraping.
- `segment_confidence: "low"`, `base_price_scope: "unknown"`.
- Do NOT invent PC/Ladder/Softcore/Hardcore — not proven by the response.

### Price Handling
- `prices.price` is in USD cents (string). Converted to dollars by dividing by 100.
- `prices.price_range` provides `min_amount` and `max_amount` for the product's variations.
- Most runes have a wide range (e.g., Cham $0.35–$16.95) reflecting quantity scaling.
- Base price `price` field is used as the floor.

## Output

**File:** `data/external/itemnow_cash_prices.json`

Follows same schema shape as `iggm_cash_prices.json`:

```
schema: {
  schema_version, product, source_slug, generated_at,
  artifact_path, total_products, rune_count, bundle_count,
  observation_count, observations: [...]
}
```

Each observation includes:

| Field | Description |
|-------|-------------|
| `source_slug` | `"itemnow"` |
| `evidence_class` | `"cash_market_listing"` |
| `item_name` | Rune short name (e.g., "Cham") |
| `item_slug` | e.g., `cham_rune` |
| `item_category` | `"rune"` or `"bundle"` |
| `normalized_item_name` | Full name from rune_registry |
| `rune_order` | Rune number (1-33) |
| `product_id` | WooCommerce product ID |
| `product_slug` | WC product slug |
| `price` | Base price in USD (minimum variation) |
| `price_min_usd` | Price range minimum |
| `price_max_usd` | Price range maximum |
| `currency` | `"USD"` |
| `stock_status` | `"in_stock"` or `"out_of_stock"` |
| `is_in_stock` | Boolean |
| `segment_terms` | Array of {slug, name} from server attribute |
| `segment_confidence` | `"low"` (base price only) |
| `base_price_scope` | `"unknown"` |
| `use_in_model` | `false` |
| `caveats` | List of caveat strings |
| `parser_notes` | Description of extraction method |

## Observations Count

| Type | Count |
|------|-------|
| Individual runes | 33 |
| Bundles | 9 |
| **Total** | **42** |

All 33 runes from `rune_registry.json` are present in the ItemNow catalog.

## Caveats

1. **Base prices only**: The Store API returns the minimum variation price. Per-segment prices (D2R Ladder, Non-Ladder, HC, etc.) are set per variation and require auth-locked API access or product page scraping.
2. **Price range ≠ segment variation**: The min-max range reflects quantity pricing, not segment differences. Both $0.05 and $1.35 may apply to the same segment at different quantities.
3. **No completed/sold history**: ItemNow is a live cash marketplace. All prices are asking prices.
4. **All products are "variable"**: There are no simple products — all 42 have the `variable` type with server attribute variations.
5. **Low-value floor**: Many low-tier runes show $0.05 base price, likely a minimum floor rather than actual market price.
6. **Segment terms broad**: Beyond 4 D2R segments, legacy server terms (East/Euro/West Ladder, HC, Non-Ladder) are also present but their prices may differ.
7. **Not integrated into in-game model**: `use_in_model: false` — this is cash/RMT comparison only.

## Files Created

- `scripts/parse_itemnow_api.py` — parser script
- `data/external/itemnow_cash_prices.json` — parsed output (42 observations)
- `research/sources/captures/itemnow/2026-06-20_api_probe/fresh_api_response.json` — fresh API response capture

## Files Modified

- `scripts/generate_external_cash_prices.py` — added itemnow to INPUT sources
- `data/source_manifest.json` — updated itemnow status to `parser_prototype_ready`, added artifacts & known URLs
- `data/products/external_cash_prices.sample.json` — regenerated with 72 observations (30 iggm + 0 items7 + 42 itemnow)

## Validation

`python3 scripts/validate_external_cash_prices.py` — **All checks passed.**
