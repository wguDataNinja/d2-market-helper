# Zero-Artifact Cash/Storefront Source Probes — 2026-06-20

## Summary

Probed all 6 sources with zero `current_artifacts` in source_manifest.json. Results:

| Source | Active Listings | Sold/Completed | Cash vs Barter | Segment Filters | Rune Pages | Parseability | Score | Next Action |
|--------|----------------|----------------|----------------|----------------|------------|--------------|-------|-------------|
| **MuleFactory** | yes | no | cash | partial (server select via JS, item category static) | yes — static microdata | **static** (Schema.org microdata + AJAX pagination) | 8 | Extract from static HTML /build parser |
| **D2Stock** | yes | no | cash | yes — in RSS titles (SC/HC, Ladder/NL, RotW/LoD) | yes — via RSS feed | **API** (Google Shopping RSS feed) | 9 | Build RSS feed parser |
| **Eldorado** | yes | no | cash | yes — embedded in listing titles (Ladder HC, NonLadder SC, RotW/LoD) | yes — via browser capture | **rendered** (Angular SPA, Camoufox OK) | 6 | Build rendered-HTML parser |
| **MMOPixel** | yes | no | cash | partial (platform selector visible) | not directly — items page shows modifiers | **rendered** (Camoufox OK) | 5 | Capture rune-specific URL |
| **RPGStash** | blocked (JS) | no | cash | unknown | product pages exist but JS-rendered | **blocked** (Cloudflare + JS app) | 2 | Requires Camoufox fix or manual capture |
| **eBay** | blocked | **yes** (sold filter exists) | cash | no | search page blocked | **blocked** (ebay anti-bot) | 1 | Manual capture only |

## Per-Source Details

### MuleFactory (mulefactory.com) ⭐
- **Correct game slug**: `diablo_2_remaster_items_for_sale/`
- **Rune category URL**: `https://www.mulefactory.com/buy_diablo_2_remaster_rune/`
- **Status**: `captured_static` — fully parseable
- **Data**: 24 runes on page 1 (72 total via AJAX "More items" button) with Schema.org microdata including `itemprop="name"`, `itemprop="price"`, `itemprop="priceCurrency"` (USD)
- **Prices extracted**: Lo $2.40, Jah $3.13, Ber $2.90, Zod $2.90, Vex $0.79, Ohm $1.78, Sur $2.00, Ist $0.60, Gul $0.60, Mal $0.39, Um $0.89, Pul $0.89, Lem $0.89, Hel $0.35, Ko $0.35, Lum $0.35, Io $0.35, Sol $0.35, Shael $0.35, Ort $0.35, Ral $0.35, Tal $0.35, Thul $0.35, Tir $0.35
- **Segment**: Item category filter static (Rune, Runeword, etc.) but server/platform selector requires JS. Prices may be base/minimum — segment-specific variants on individual product pages
- **Other categories**: `/buy_diablo_2_remaster_runeword/`, `/buy_diablo_2_remaster_runeword_base/` also have static content
- **Parser feasibility**: 8/10 — microdata + CSS extraction

### D2Stock (d2stock.com) ⭐⭐
- **Status**: `api_observed` — Google Shopping RSS feed discovered
- **RSS Feed URL**: `https://d2stock.com/rss.xml` (2.2 MB, 2,014 items)
- **Format**: Google Merchant XML (`<g:id>`, `<g:title>`, `<g:price>`, `<g:product_type>`, `<g:availability>`, `<g:link>`, `<g:image_link>`)
- **Segments in titles**: "Softcore Ladder RotW", "Softcore Non-Ladder RotW" (no Hardcore found in sample)
- **Rune prices**: 0.25–1.85+ USD per rune (single) with 10× packs available
- **Categories**: Runes > Buy D2R Runes, Runes > Rune Packs, Runes > Runewords + full item shop (runewords, uniques, sets, skillers, torches, jewels, bases, etc.)
- **Site**: SvelteKit app — JS-rendered pages but RSS feed is pure structured data
- **Parser feasibility**: 9/10 — XML feed parser, no browser needed

### Eldorado (eldorado.gg) 
- **Correct URL**: `https://www.eldorado.gg/diablo-2-resurrected-items/i/95-2-0`
- **Status**: `captured_browser`
- **Method**: Camoufox headless — page rendered successfully (title: "Buy D2R Items, Runes | Eldorado.gg")
- **Data**: 476 items found including specific rune listings with per-unit prices
- **Segments visible**: Ladder HC, Ladder SC, NonLadder HC, NonLadder SC, ROTW & LoD — embedded in listing titles
- **Seller info**: Seller names, reputation (99.x% with vote counts), delivery time
- **Site**: Angular SPA — no embedded JSON in static shell
- **Parser feasibility**: 6/10 — Camoufox rendered HTML has listing text but needs structured extraction

### MMOPixel (mmopixel.com)
- **Correct slug**: `diablo-ii-resurrected`
- **Status**: `captured_browser`
- **Method**: Camoufox headless — rendered successfully
- **Data**: 1,304 products on items page but showing item modifiers (sockets, enhanced damage, etc.) — not specifically runes. Has rune image assets in sitemap.
- **Segment**: Platform selector visible (PC)
- **Parser feasibility**: 5/10 — needs rune-specific URL capture

### RPGStash (rpgstash.com)
- **Status**: blocked
- **Curl**: Cloudflare blocking (403)
- **Camoufox**: Crashed ("Connection closed while reading from the driver") — Playwright coreBundle.js error
- **Cloudscraper**: Bypasses Cloudflare but page is fully JS-rendered (no static prices)
- **Individual product pages**: e.g. `/ber-rune-d2r-diablo2-resurrected.html` — 225KB, 20+ scripts, but all prices JS-rendered
- **Rune images**: Present at paths like `/43265-catalog_page/jah-rune-d2r...png`
- **Parser feasibility**: 2/10 — Camoufox render fails, JS-heavy

### eBay (ebay.com)
- **Status**: blocked
- **Curl**: 403 error page
- **Camoufox**: Renders but shows eBay error page — blocked at application level
- **Known capability**: eBay has sold/completed filter (`&rt=nc&LH_Sold=1&LH_Complete=1`) but cannot currently access
- **Segment filters**: Platform/ladder/HC/SC not available on eBay
- **Parser feasibility**: 1/10 — fully blocked

## Sources with Usable Artifacts Captured

1. **D2Stock** — RSS feed (`research/sources/captures/d2stock/2026-06-20_search_probe/rss_feed.xml`)
2. **MuleFactory** — Static rune page with microdata prices (`research/sources/captures/mulefactory/2026-06-20_search_probe/curl_rune_page.html`)
3. **Eldorado** — Camoufox-rendered page (`research/sources/captures/eldorado/2026-06-20_search_probe/page.html`)
4. **MMOPixel** — Camoufox-rendered page (`research/sources/captures/mmopixel/2026-06-20_search_probe/page.html`)

## Sources with Parser Candidates

1. **D2Stock** — RSS XML feed parser (highest priority)
2. **MuleFactory** — Static HTML microdata parser
3. **Eldorado** — Rendered HTML text parser

## Sources Needing Manual HTML Capture

1. **RPGStash** — Camoufox crashes; needs Playwright/Camoufox version upgrade or alternate capture approach
2. **eBay** — Fully blocked; manual browser session required

## Sources with Sold/Completed/History Found

- **eBay** — Sold filter exists but blocked from automated access
- **None of the others** — no sold/completed/history surface found

## Artifact Paths Created

- `research/sources/captures/eldorado/2026-06-20_search_probe/` — curl + Camoufox capture (8 files)
- `research/sources/captures/mmopixel/2026-06-20_search_probe/` — curl + Camoufox capture (10 files)
- `research/sources/captures/mulefactory/2026-06-20_search_probe/` — curl probes (9 files)
- `research/sources/captures/d2stock/2026-06-20_search_probe/` — curl + cloudscraper + RSS feed (8 files)
- `research/sources/captures/rpgstash/2026-06-20_search_probe/` — curl + cloudscraper (8 files)
- `research/sources/captures/ebay/2026-06-20_search_probe/` — curl + Camoufox (6 files)
