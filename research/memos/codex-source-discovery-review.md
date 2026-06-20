# Codex Source Discovery Review

Generated: 2026-06-20

## Scope

This review covers the current Traderie completed-trade pipeline, the downloaded source artifacts under `research/sources/downloads/rune_sources_2026-06-20/`, and the existing source-discovery notes. No live sites were crawled, no Reddit comments were fetched, and no pricing model changes were made.

## Current Traderie Collection Summary

The active pipeline uses Traderie's listings surface as the primary completed-player-trade source:

```text
GET https://traderie.com/api/diablo2resurrected/listings
  completed=true
  auction=false
  prop_Platform=PC
  prop_Mode={softcore|hardcore}
  prop_Ladder={true|false}
  item={traderie_item_id}
```

The four enabled PC segment configs are:

| Segment | Platform | Mode | Ladder | Hardcore |
|---|---|---|---|---|
| `pc_sc_nl` | PC | softcore | false | false |
| `pc_sc_l` | PC | softcore | true | false |
| `pc_hc_nl` | PC | hardcore | false | true |
| `pc_hc_l` | PC | hardcore | true | true |

`scripts/fetch_completed_trades.py` loads `server_configs.json` and `data/item_ids.json`, loops segment -> category -> item, calls the endpoint with `cloudscraper`, and writes `data/raw/raw_trades_{segment}.json`. It currently fetches all categories in `data/item_ids.json`, not just runes: `Runes`, `Gems`, and `Misc`.

The current raw files are sanitized before storage. Each listing is reduced to:

```json
{
  "seller": "seller username",
  "quantity": 1,
  "updated_at": "timestamp",
  "price": [
    {"name": "requested item name", "quantity": 1}
  ]
}
```

Older saved Traderie payloads show that the API can return richer fields that the current sanitizer drops:

| Field group | Available in older payload | Currently used? |
|---|---|---|
| Listing identity | `id`, `item_id`, `variant_id`, `wishlist_id`, `offer_wishlist_id` | No |
| Trade status | `completed`, `active`, `selling`, `make_offer`, `accept_listing_price`, `standing`, `stock` | Only implied by request params |
| Quantities/time | `amount`, `updated_at`, `total_offers` | `amount` and `updated_at` only |
| Requested price items | `prices[].id`, `name`, `type`, `group`, `item_id`, `quantity`, `properties`, `variant_id`, images | Only `name` and `quantity` |
| Segment metadata | `properties[]` for `Mode`, `Region`, `Ladder`, `Platform` | Not persisted; segment inferred from output file |
| Seller metadata | seller id, username, battle.net tag, status, rating, score, reviews, timezone, languages, profile image | Only username |

The current extraction stage, `scripts/extract_rune_trades.py`, reads only the `Runes` category from each raw file. It discards listings whose requested price contains any non-rune, discards empty/invalid prices, discards self-trades, and writes `data/extracted/extracted_trades_{segment}.csv` with:

```text
TradeID, Offered, Requested
```

`TradeID` is `{offer_rune}_{updated_at}`. `Offered` is `Rune:qty`; `Requested` is a semicolon-delimited set of `Rune:qty`.

`scripts/calculate_rune_prices.py` then prices each segment independently. It uses only single-request trades where one side is `Ist Rune`, removes ratios outside `0.5` to `50.0` Ist per rune, computes bid and ask VWAP, and writes `data/prices/rune_prices_{segment}.csv`.

## Traderie Risks And Gaps

The method is useful and already supports the core in-game rune-ratio product, but it should be stabilized before public website data products depend on it.

Key risks:

| Risk | Current state | Impact |
|---|---|---|
| Unofficial API dependency | Uses Traderie site API through `cloudscraper`, not an official public data product | Cloudflare, rate limits, or schema changes can break collection |
| No pagination/window control | The fetcher sends no `page`, `limit`, cursor, or date-window params | If the API returns only a recent/default window, a long gap between fetches can miss completed trades |
| Dedupe by timestamp only | Dedupe uses `updated_at` per category/item | Same-timestamp listings can collide; changed listings can duplicate if `updated_at` changes; listing `id` is not available after sanitization |
| Segment metadata not persisted | Segment is inferred from filename; API `properties[]` are discarded | Harder to audit bad filters, migrated configs, or cross-platform expansion |
| Useful fields dropped | Listing id, item ids, region, total offers, seller score/reviews/status, price item ids, variant/properties are ignored | Limits confidence scoring, dedupe quality, source auditing, and future non-rune item modeling |
| Completed semantics depend on Traderie | Query asks `completed=true`, but older payload examples still include `active=true` | Need validation rules that document how Traderie represents completed listings |
| No recency model | Raw timestamps are kept, but extracted/priced outputs omit observed/completed windows | Website cannot honestly label freshness without additional metadata |
| AND trades excluded from pricing | Extracted but not modeled by `calculate_rune_prices.py` | Leaves useful trade evidence unused, especially multi-rune asks |

The current method can support future website data products if the output layer is made schema-versioned and auditable. The next version should retain listing ID, item ID, source segment properties, raw observed timestamp, fetch metadata, and source query params in a normalized intermediate file while still avoiding public release of raw Traderie payloads.

## Downloaded Source Artifact Findings

### Traderie

The downloaded web page is only a React shell. Static HTML is not useful for extraction. The existing API collector is the correct source for Traderie. Evidence class: `completed_player_trades`.

### PlayerAuctions / `warlock_gear_sets.html`

Best cash-market artifact. It contains parseable listing blocks such as:

```text
data-bind="290440467i!pc--rotw--ladder-s14--sc--runes--runes30-ber/?quantity=1"
```

It also contains a JavaScript price table keyed by listing id, with fields such as `pricePerUnit`, `minValue`, `maxValue`, `currencyPerUnit`, and volume-discount details. The HTML exposes rune listings, runeword/runeset listings, Harlequin Crest/Shako, Wisp Projector, Hellfire Torch, charms, and other selected high-value items.

Segment quality is strong. The listing path/title encodes platform, ROTW/season, ladder/non-ladder, softcore/hardcore, category, and item. This is suitable for an offline parser prototype from saved HTML. Evidence class: `cash_market_listings`; do not mix with in-game ratios.

### items7

The saved page has static item cards with product names, product URLs, `ProID`, and visible `<em class="price">$ ...</em>` values. Examples include Ber, Jah, Ist, and other rune cards. This is a low-risk offline parser target for per-rune cash prices.

Segmentation is weaker than PlayerAuctions. The page appears ROTW-oriented and has ladder/non-ladder navigation, but not full platform/hardcore/softcore specificity in the downloaded page. Evidence class: `cash_market_listings`.

### IGGM

The saved HTML is more extractable than the earlier source memo implies. It contains platform selectors for PC/Xbox/Switch, segment selectors for ladder/non-ladder and softcore/hardcore, and hidden price attributes near rune cards, e.g. `span class="price" lkr="7.9"` near Jah and `lkr="7.29"` near Ber in the downloaded PC ladder softcore context.

It also contains Annihilus and Hellfire Torch category labels. This could support an offline parser, but parser confidence is lower than PlayerAuctions/items7 until the product-card-to-selected-segment relationship is verified. Evidence class: `cash_market_listings`.

### Odealo

The saved page contains structured server options for PC/PlayStation/Xbox/Switch across ladder, non-ladder, hardcore ladder, and hardcore non-ladder. It also contains rendered listing titles/offer links for runes and JSON-LD `AggregateOffer` metadata. Numeric per-listing prices are not plainly present in the same way as PlayerAuctions or items7; price display appears partly dynamic/asset-driven.

Odealo is useful for source directory and future source discovery. It is a good candidate for deeper offline inspection of saved pages or approved browser/HAR capture, but not the first parser target. Evidence class: `cash_market_listings`.

### YesGamers

The saved HTML exposes strong UI clues: ladder/non-ladder, softcore/hardcore, platform controls, and endpoints in JavaScript such as `/d2r/product/get`, `/cart/product/add`, and product quick-view behavior. It mentions selected items including Annihilus, Hellfire Torch, Shako, and Harlequin Crest. Static price extraction is not straightforward from the saved page. Evidence class: source directory / possible future cash-market collector if approved.

### d2items_for_sale / itemnow.com

The saved page is a WooCommerce/WordPress product-category page. It exposes product links for runes, `server` URL filters for D2R ladder/non-ladder/hardcore ladder/hardcore non-ladder, WooCommerce AJAX config, and WP REST links such as `/wp-json/` and `/wp-json/wp/v2/product_cat/99`.

The category page shows prices as `Vary`, so individual product pages or approved WP endpoint discovery would be required for prices. Evidence class: source directory now; possible future cash-market collector.

### AOEAH

The page is mostly static and includes all runes plus platform/ladder UI clues, but dollar prices were not plainly extractable in the saved artifact. It is lower priority than PlayerAuctions, items7, IGGM, and Odealo. Evidence class: source directory / possible future cash-market collector.

### G2G And Chicks Gold

Both saved pages are dynamic shells with little extractable static pricing. They are low-priority source-directory entries unless a future approved browser/HAR pass identifies stable public endpoints. Evidence class: source directory / user navigation.

### Reddit

Reddit pass 1 is qualitative only. It supports venue discovery, player language, item candidates, and new-player pain points. It should not feed pricing calculations or public price claims.

### Diablo2.io And d2jsp

These were not included in the downloaded artifacts. They remain important future discovery targets: Diablo2.io as a possible player-trade/reference source, and d2jsp as a forum/FG economy reference. Neither should be treated as completed in-game trade data without a separate methodology review.

## Source Ranking By Usefulness

### Completed Player Trades

1. Traderie API: only production-quality completed-player-trade source currently integrated.
2. Diablo2.io: not evaluated; investigate separately.
3. d2jsp: forum/FG economy, not direct in-game completed trades.

### Active Player Listings

1. Traderie active-listings API surface: likely available but not part of the current model.
2. Diablo2.io: investigate for public listings/history.
3. d2jsp: useful forum listings, but FG-denominated and structurally different.

### Forum / Economic Reference

1. d2jsp: likely strongest for FG-denominated market reference if researched carefully.
2. Diablo2.io: possible price-check/trade-history reference.
3. Reddit: qualitative language and venue discovery only.

### Cash-Market Listings

1. PlayerAuctions: strongest structured saved HTML; listing IDs, paths, segment labels, and price table.
2. items7: simplest static per-rune cash prices; weaker segmentation.
3. IGGM: hidden static price attributes and strong segment controls; needs parser validation.
4. Odealo: excellent segmentation and listing titles; price extraction less direct.
5. itemnow.com: good WP/WooCommerce clues; category page prices are not concrete.
6. AOEAH: rune coverage and segment UI, but price extraction unclear.
7. YesGamers: rich controls and endpoint clues, but static price extraction not ready.
8. G2G / Chicks Gold: low-priority dynamic shells.

### Source Directory / User Navigation

All inspected sources are useful as directory entries if labeled correctly. The website should separate `completed_player_trades`, `cash_market_listings`, `forum_reference`, `community_discussion`, and `navigation_only`.

## What Not To Pursue Yet

- Do not build live scrapers for cash sites.
- Do not query PlayerAuctions, Odealo, IGGM, itemnow, or YesGamers endpoints without explicit approval.
- Do not publish raw Traderie payloads or raw Reddit data.
- Do not combine cash prices with in-game rune values.
- Do not merge PC segments into a blended price by default.
- Do not model d2jsp FG as equivalent to Ist without a separate conversion methodology.
- Do not prioritize runeword standalone pricing before rune component pricing and selected high-value item profiles are stable.

## Best Next Opportunities

1. Stabilize Traderie output into a schema-versioned public `in_game_rune_values.json`.
2. Preserve richer private Traderie normalized records for audit and dedupe, especially listing id, item ids, source properties, `updated_at`, and query metadata.
3. Build an offline PlayerAuctions parser from `warlock_gear_sets.html` that joins listing `data-bind` metadata to the JavaScript `pricePerUnit` table by listing id.
4. Build an offline items7 parser from `items7.html` that extracts rune name, product URL, product id, and price.
5. Add `source_directory.json` before frontend work so evidence labels and source caveats are available from the first website prototype.
6. Do a focused offline IGGM parser spike only after PlayerAuctions/items7 prove the `external_cash_prices.json` schema.

## Recommended Implementation Sequence

1. Define and generate `in_game_rune_values.json` from the existing per-segment CSVs. Include `schema_version`, `generated_at`, `pipeline_version`, `model`, segment metadata, trade counts, confidence from sample size, and model caveats.
2. Add a private normalized Traderie intermediate format for future fetches. Keep sanitized public output separate from raw/private data.
3. Create `source_directory.json` from docs and source memos. Include evidence class, segment support, extraction status, caveats, and last inspected date.
4. Prototype `external_cash_prices.json` with offline-only parsers for PlayerAuctions and items7 saved HTML. Label all observations as cash listing prices and include source page/artifact metadata.
5. Build the first website data views from stable JSON only: source directory, segment-specific rune table, evidence labels, and item profile navigation.
6. After the website/data contracts exist, investigate Diablo2.io and d2jsp with a written methodology proposal before collection.

## Specific Next Tasks

### Immediate Engineering Task

Create `scripts/generate_prices_json.py` that reads the existing `data/prices/rune_prices_{segment}.csv` files and emits schema-versioned `data/products/in_game_rune_values.json` without merging segments.

### Source-Discovery Task

Create an offline parser design note for PlayerAuctions and items7 saved HTML, including exact fields to extract, segment mapping rules, and failure cases. Then implement parser prototypes only against files already saved in `research/sources/downloads/`.

### Website / Product Task

Create `data/products/source_directory.json` and a prototype source-directory page that groups sources by evidence class and displays clear caveats: completed trades, active listings, cash listings, forum reference, community-only, and navigation-only.
