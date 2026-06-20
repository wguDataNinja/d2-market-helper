# Downloaded Site Discovery — Pass 1

Generated: 2026-06-20

## Scope

10 HTML files downloaded from cash/RMT marketplace sites for D2R runes and items. Files were copied into `research/sources/downloads/rune_sources_2026-06-20/` and inspected.

## Sources Inspected

| Source | Size | Type | Rune Prices | Items |
|---|---|---|---|---|
| Traderie (web) | 7 KB | Trade platform | Dynamic shell | None |
| PlayerAuctions | 841 KB | Cash market | Yes (structured listings) | Yes |
| Odealo | 257 KB | Cash market | Dynamic (React) | None |
| YesGamers | 884 KB | Cash market | Dynamic | Annihilus, Torch, Shako |
| IGGM | 269 KB | Cash market | Dynamic | Annihilus, Torch |
| items7 | 84 KB | Cash market | **Static ($0.15-$2.85)** | None |
| AOEAH | 101 KB | Cash market | Partial | None |
| d2items_for_sale | 50 KB | WordPress/RMT | Partial (WP API) | None |
| G2G | 9 KB | Cash market | Dynamic shell | None |
| Chicks Gold | 6 KB | Cash market | Dynamic shell | None |

## Key Findings

### Rune Prices Found

Only **items7** and **PlayerAuctions** had extractable cash prices in static HTML:

- **items7**: 21 dollar amounts visible. Values: $0.15, $0.25, $0.35, $0.45, $1.45, $2.25, $2.85. Per-unit rune pricing.
- **PlayerAuctions**: 60 dollar amounts. Range: $27.54 to $1,999.00. Per-listing pricing with structured `data-bind` attributes identifying the exact rune and segment.

### Structured Listing Data (Most Promising Discovery)

**PlayerAuctions** uses a `data-bind` attribute pattern that contains parseable listing metadata:

```
290440467i!pc--rotw--ladder-s14--sc--runes--runes30-ber/?quantity=1
```

This encodes: Listing ID | Platform--Expansion--Mode--Season--Hardcore--Category--Subcategory--Item

This is the most structured cash-market data discovered. It could enable automated cross-referencing of cash prices vs Traderie-derived rune ratios.

### Selected Item Prices

Only **PlayerAuctions** had item-level listing data in the download:
- Enigma runeset (Jah + Ber)
- Fortitude runes
- Infinity runes
- Harlequin Crest (Shako)
- Wisp Projector

Other sources mentioned item names in page text but did not show prices in the static HTML.

### Segmentation Support

Sources with excellent segmentation (ladder/non-ladder, softcore/hardcore, platform, season):

| Source | Segments |
|---|---|
| PlayerAuctions | `pc--rotw--ladder-s14--sc` encoded in listing paths |
| Odealo | Full filter UI with platform + ladder + hc + season dropdowns |
| YesGamers | Interactive UI: ladder toggle, SC/HC toggle, ROTW checkbox |
| IGGM | Described as "ladder/non-ladder (rotw) softcore/hardcore" |
| items7 | ROTW ladder/non-ladder navigation |

### API Endpoints Discovered

- `https://user-api.playerauctions.com/` — potential listing data source
- `https://public-api.playerauctions.com/` — potential listing data source
- `https://itemnow.com/wp-json/wp/v2/` — WordPress REST API (may expose product data with prices)

### Modeling Rule

Direct in-game completed trades (Traderie API) are the source of truth for relative rune ratios. Cash/RMT sites are for cross-site price comparison and divergence analysis only. Do not blend cash prices into the relative rune model.

## What Was NOT Found

- No second structured trade-data source comparable to Traderie's completed trades API
- No per-roll pricing for Annihilus or Hellfire Torch on any static HTML
- No diablo2.io data — this source needs separate investigation
- No d2jsp forum data — this source requires forum scraping or API (different approach)

## Recommended Source Priority

| Priority | Source | Rationale |
|---|---|---|
| 1 | **Traderie API** | Already integrated. Primary pricing source. |
| 2 | **PlayerAuctions** | Best structured cash-market data. Parseable `data-bind` format. |
| 3 | **Odealo** | Middleware/API discovery candidate. Excellent segmentation. |
| 4 | **items7** | Simplest static cash pricing. Easy to extract per-rune. |
| 5 | **itemnow.com (WP API)** | WordPress REST API may expose prices without JS. |

## Recommended Next Downloads

1. **PlayerAuctions** — Search results for "ber rune" or "jah rune" to see rendered listing prices (the `data-bind` attributes may not include price — need to see the rendered listing)
2. **Odealo** — Individual rune product pages (may have server-rendered prices even if the category page is React-dynamic)
3. **items7** — Individual rune pages to map price to rune name
4. **itemnow.com** — `https://itemnow.com/wp-json/` REST API root
5. **IGGM** — Individual rune pages (best segment descriptions)

## Artifacts

| File | Purpose |
|---|---|
| `research/sources/downloads/rune_sources_2026-06-20/` | Raw HTML downloads (10 files) |
| `research/sources/traderie.md` | Traderie web page assessment |
| `research/sources/playerauctions.md` | PlayerAuctions listing data assessment |
| `research/sources/odealo.md` | Odealo marketplace assessment |
| `research/sources/items7.md` | items7 rune prices assessment |
| `research/sources/iggm.md` | IGGM marketplace assessment |
| `research/sources/aoeah.md` | AOEAH marketplace assessment |
| `research/sources/yesgamers.md` | YesGamers marketplace assessment |
| `research/sources/d2items_for_sale.md` | itemnow.com WordPress assessment |
| `research/sources/g2g.md` (future) | G2G marketplace assessment |
| `research/sources/chicks_gold.md` (future) | Chicks Gold assessment |
| `docs/SOURCE_DISCOVERY.md` | Source comparison table and priority |
