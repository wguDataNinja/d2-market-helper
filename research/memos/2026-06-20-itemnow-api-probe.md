# ItemNow API Probe — 2026-06-20

## Endpoints Checked

| # | Endpoint | HTTP | Size | Notes |
|---|----------|------|------|-------|
| 1 | `/product-category/diablo-2/runes/` | 200 | 51 KB | Static HTML, 42 runes listed, prices show "Vary" (AJAX-loaded) |
| 2 | `/wp-json/wp/v2/` | 200 | 218 KB | WP REST API root — 80+ routes including `product`, `product_cat` |
| 3 | `/wp-json/wp/v2/product` | 200 | 21 KB | Returns products but **no WooCommerce price fields** |
| 4 | `/?s=Jah&post_type=product` | 200 | 34 KB | WP search results page |
| 5 | `/product-category/diablo-2/runes/jah-rune/` | 404 | 26 KB | Invalid URL — individual runes have different path |
| 6 | `/wp-sitemap.xml` | 200 | 3.2 KB | 23 sitemap indexes, 20 product sitemaps |
| **Bonus** | `/wp-json/wc/store/v1/products?category=99&per_page=100` | **200** | **160 KB** | **Store API returns structured product data with prices!** |
| **Bonus** | `/wp-json/wc/store/v1/products?slug=ber-rune` | **200** | **3.8 KB** | **Per-product detail with attributes and variation IDs** |
| **Bonus** | `/wp-json/wp/v2/product_cat/99` | 200 | 803 B | Cat ID 99 = "Runes" (parent=6=D2R, count=42) |
| **Bonus** | `/wp-json/wp/v2/product/12149` | 200 | 2 KB | Ber Rune via WP API — no prices, but shows `pa_server-*` classes |
| **Bonus** | `/wp-json/wc/v3/` | 200 | 228 KB | WC REST API v3 root — `/wc/v3/products` route exists but **401 auth required** |
| **Bonus** | `/product/ber-rune/` | 200 | 47 KB | Product detail page has JSON-LD with AggregateOffer |

## Key Findings

### Structured Product Data Found ✅

The **WooCommerce Store API** (`/wp-json/wc/store/v1/products`) is fully public and returns:

- **42 rune products** (30 individual runes + 12 bundle packages)
- **Per-product prices in USD cents** (e.g., Jal Rune base price = 55¢, Ber = 45¢, Zod = 45¢, Ohm = 35¢)
- **Price ranges** (e.g., Ber Rune min $0.45, max $39.95 per quantity)
- **Product names**, slugs, SKUs, categories, stock status
- **Segment/attribute data** — all products have a `server` attribute with 14 terms

### Segment Filters

Confirmed via HTML `realms-widget` and product attributes:

| Segment | Slug | Available |
|---------|------|-----------|
| D2R Ladder | `d2r-ladder` | ✅ |
| D2R Non-Ladder | `d2r-non-ladder` | ✅ |
| D2R HC Ladder | `d2r-hc-ladder` | ✅ |
| D2R HC Non-Ladder | `d2r-hc-non-ladder` | ✅ |
| Legacy East/West/Euro Ladder | `east-ladder` etc. | ✅ (14 terms total) |

Segment selection via `?server=` URL parameter. All runes are **variable products** with variations per server.

### Are Prices Cash/RMT Only?

**Yes.** All prices are in USD. No in-game barter prices. This is a cash/RMT marketplace.

### Do Rune Pages Have Structured Product Data?

**Yes.** Two sources of structured data:

1. **WooCommerce Store API** (`/wp-json/wc/store/v1/products`) — returns full JSON with names, prices, categories, attributes, stock status, variation IDs. Fully public, no auth required.
2. **JSON-LD on product pages** — each product page has `AggregateOffer` with `lowPrice`, `highPrice`, `offerCount`, currency.

### Does Sold/Completed/History Surface Exist?

**No.** There is no sold/completed/history surface. ItemNow is a live cash marketplace with asking prices only. No completed trade history, no price history, no sold listings.

### WC v3 API (401 Auth Required)

The WooCommerce v3 API (`/wp-json/wc/v3/products`) has richer endpoints (variations, categories, batch updates) but requires authentication. The Store API is the public-facing consumer API and provides sufficient data.

## Run Price Data (Store API Extract)

| Rune | Base Price (USD) | Max Price (USD) | Variations |
|------|------------------|-----------------|------------|
| El | $0.05 | — | 14 |
| Eld | $0.05 | — | 14 |
| Tir | $0.05 | — | 14 |
| Nef | $0.05 | — | 14 |
| Eth | $0.05 | — | 14 |
| Ith | $0.05 | — | 14 |
| Tal | $0.05 | — | 14 |
| Ral | $0.05 | — | 14 |
| Ort | $0.05 | — | 14 |
| Thul | $0.05 | — | 14 |
| Amn | $0.05 | — | 14 |
| Sol | $0.05 | — | 14 |
| Shael | $0.05 | — | 14 |
| Dol | $0.05 | — | 14 |
| Io | $0.05 | — | 14 |
| Lum | $0.05 | — | 14 |
| Ko | $0.05 | — | 14 |
| Fal | $0.05 | — | 14 |
| Lem | $0.05 | — | 14 |
| Pul | $0.05 | — | 14 |
| Um | $0.05 | — | 14 |
| Mal | $0.05 | — | 14 |
| Ist | $0.05 | — | 14 |
| Gul | $0.05 | — | 14 |
| Vex | $0.23 | — | 14 |
| Ohm | $0.35 | — | 14 |
| Lo | $0.35 | — | 14 |
| Sur | $0.35 | — | 14 |
| Ber | $0.45 | $39.95 | 14 |
| Jah | $0.55 | $59.95 | 14 |
| Cham | $0.35 | $16.95 | 14 |
| Zod | $0.45 | — | 14 |

## Feasibility Scoring (10 Dimensions)

Based on the probe protocol:

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Public access** | 10/10 | No auth, no login wall, no browser required |
| **Structured data** | 9/10 | JSON API with typed fields. Variable products with attribute taxonomy |
| **Per-segment prices** | 5/10 | Base prices available. Per-segment variation prices need individual variation API calls (WC v3 is 401 auth; Store API returns base min) |
| **Item coverage** | 8/10 | All 30 D2R runes + bundles. WP has 18K+ products across D2R |
| **Price freshness** | 8/10 | Real-time via API (same as live site) |
| **Price type** | 10/10 | USD cash prices, clearly labeled, in minor units |
| **Sold/completed history** | 0/10 | No history surface exists |
| **Segment filters** | 8/10 | 4 D2R segments confirmed via `server` attribute. 14 total server terms |
| **Parseability** | 9/10 | Clean JSON, no JS rendering needed, no pagination complexity |
| **Documentation** | 2/10 | Undocumented WordPress/WooCommerce Store API — but stable WP API |

**Composite: 6.9/10** (weighted toward parseability, structure, and pricing; penalized by no history and per-variation price access)

## Next Parser Task

**Write a parser for the WooCommerce Store API.**

### Parser Spec

- **Input:** Query `/wp-json/wc/store/v1/products?category=99&per_page=100`
- **Output:** Array of rune products with: `name`, `slug`, `price_cents`, `price_usd`, `currency`, `segment_attributes` (from `pa_server` taxonomy), `is_in_stock`, `sku`
- **Segment extraction:** Extract attribute `terms` from the `attributes[0].terms` array; map slug to D2R segment
- **Multi-segment pricing:** Per-variation prices require accessing `/wp-json/wc/v3/products/{id}/variations` (auth required) OR scraping individual product page HTML for variation prices. **Deferred — base price is sufficient for cash comparison.**
- **Refresh cadence:** Real-time (no rate limits observed)
- **Output schema:** Follow existing `cash_market_listings` pattern from `iggm_cash_prices.json`

### Caveats

- Per-segment pricing (D2R Ladder vs Non-Ladder vs HC Ladder vs HC Non-Ladder) **not available** from the Store API base price field. May be same across segments (cash marketplace, not segment-elastic).
- The `price` field is the minimum variation price. Some products have `price_range` showing min-max.
- WC v3 API (`/wc/v3/products`) offers richer data (variations, categories, attributes) but requires authentication.

## File Paths Created

- `data/research/itemnow_api_probe.sample.json` — 42 rune products with prices
- `research/sources/captures/itemnow/2026-06-20_api_probe/` — 16 capture files
- `research/memos/2026-06-20-itemnow-api-probe.md` — this memo
