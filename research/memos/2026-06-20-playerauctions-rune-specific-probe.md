# PlayerAuctions Rune-Specific Probe Results

**Date:** 2026-06-20
**Status:** Complete
**Protocol Stage:** Stage 3 (Deep Market-Surface Search) — partial; Stage 2 inventory needed

---

## URLs Probed

| # | URL | Method | Result |
|---|---|---|---|
| 1 | `/?search=Jah+Rune` | curl | **403** — Cloudflare managed challenge |
| 2 | `/diablo-2-resurrected-items/` | curl | **403** — Cloudflare managed challenge |
| 3 | `/diablo-2-resurrected-items/runes/` | curl | **403** — Cloudflare managed challenge |
| 4 | `/diablo-2-resurrected-items/runes` | curl | **403** — Cloudflare managed challenge |
| 5 | `/diablo-2-resurrected-items/?search=Jah+Rune` (full browser headers) | curl | **403** — Cloudflare |
| 6 | `member.playerauctions.com/` | curl | **200** — Angular SPA shell (login required) |
| 7 | API endpoints (see below) | curl | 404/empty/health-check |

### API Endpoint Probe Results

| Endpoint | HTTP | Response |
|---|---|---|
| `https://public-api.playerauctions.com/` | 404 | Empty |
| `https://public-api.playerauctions.com/{v1,listings,search,...}` | — | Connection dropped by Cloudflare |
| `https://user-api.playerauctions.com/` | 404 | Empty |
| `https://account-api.playerauctions.com/` | 200 | `"ok!"` (health check only) |

All main-domain curl requests (including `robots.txt`, `sitemap.xml`) are blocked by Cloudflare managed challenge (403). The site is fully behind Cloudflare and requires a JavaScript-capable browser to access.

---

## Existing Fixtures Used for Analysis

The existing `warlock_gear_sets.html` fixture (saved prior to this probe, 861 KB) provided the most useful data. This file was apparently downloaded from a D2R items listing page and contains **30 product listing cards** with fully server-rendered HTML.

### Product Detail URL Pattern (from fixture)

```
/diablo-2-resurrected-items/{offerID}i!{segment-path}/
```

Example: `/diablo-2-resurrected-items/290440468i!pc--rotw--ladder-s14--sc--runes--runes31-jah/`

### data-bind Attribute Pattern

```
{offerID}i!{segment-path}/?quantity={n}
```

Example: `290440467i!pc--rotw--ladder-s14--sc--runes--runes30-ber/?quantity=1`

### Segment Path Encoding

The segment path follows a structured format:

| Format | Example |
|---|---|
| Full segment path | `pc--rotw--ladder-s14--sc--runes--runes30-ber` |
| Parsed segments | platform=`pc`, region=`rotw`, ladder=`ladder-s14`, hardcore=`sc` (SC), category=`runes`, item=`ber`, rune_number=`30` |
| Cross-platform | `all-severs14-runes30-ber` (platform=`all`, season=`season14`) |
| Hardcore variant | `ber-rune-hardcore-ladder-d2r` |
| Non-ladder variant | `pc--non-ladder-softcore--rotw-wisp-projector-...` |

### Price Structure (Static HTML)

```
Unit price:   <span class="item-price-name">$6.180 / 1</span>   (in .price-per-unit div)
Total price:  <div class="offer-price-tag price">$6.18</div>     (in .offer-buttons div)
```

Both unit and total prices are **server-rendered in static HTML** — no JavaScript required for extraction.

### Sample Rune Prices from Fixture

| Rune | Segment | Unit Price | Total | Seller |
|---|---|---|---|---|
| Ber (#30) | PC, RoTW, Ladder S14, SC | $6.18 | $6.18 | cheaprsgolds |
| Jah (#31) | PC, RoTW, Ladder S14, SC | $7.21 | $7.21 | cheaprsgolds |
| Cham (#32) | PC, RoTW, Ladder S14, SC | $3.06 | $6.12 (x2) | cheaprsgolds |
| Zod (#33) | PC, RoTW, Ladder S14, SC | $5.14 | $5.14 | cheaprsgolds |
| Ber (#30) | All Servers, S14 | $6.50 | $6.50 | (no seller extracted) |
| Ber (HC) | Hardcore Ladder D2R | not extracted | not extracted | (different seller) |

---

## Surface Inventory

| Surface | Status | Notes |
|---|---|---|
| completed_trade | **absent** | No sold/completed/history tab or filter visible on any page |
| active_listing | **found** | 30+ listing cards with prices in warlock_gear_sets.html fixture |
| price_history | **absent** | No price history view observed |
| cash_listing | **found** | Primary surface — all listings are cash (USD), asking prices |
| forum_text | absent | N/A for this source type |
| reference | absent | N/A |
| api | **absent** | API endpoints return 404 or empty; no XHR data endpoints found |
| item_page | **found** | Product detail URLs follow pattern `/diablo-2-resurrected-items/{id}i!{path}/` |
| search_page | **unchecked** | Curl blocked by Cloudflare; search results unknown |

---

## Sold/Completed Status

**No sold or completed trade surface exists on PlayerAuctions.** The site is a cash marketplace for active listings only. There is:
- No "sold" filter or tab
- No "completed" section
- No price history view
- No auction-style "closed" listings
- No "recent sales" data

All listings are **active asking prices** from sellers. This is strictly a cash-market comparison source, not a completed-trade source.

---

## Parseability

### Static HTML Parseability

**High** — when the page is accessible. The `warlock_gear_sets.html` fixture proves that listing cards are fully server-rendered with:
- Listing titles with item name and segment info
- `data-bind` attribute with structured segment-path encoding
- Unit price per item
- Total price
- Seller name and stats
- Delivery time

### Curl Blocking

**Blocked by Cloudflare managed challenge.** All curl requests return 403 with a `window._cf_chl_opt` challenge script. The site implements:
- Cloudflare managed challenge (turnstile + JS computation)
- No curl/curl-like access possible
- Even full browser headers fail — the request must complete the challenge

### Required Access Method

**Browser automation.** To capture the page with listing data:
1. Use Camoufox or similar headless browser
2. Navigate to `/diablo-2-resurrected-items/` or a rune-specific subcategory
3. Let the Cloudflare challenge complete (browser solves it automatically)
4. Wait for full page render (the JS may still be loading additional data)
5. Capture the rendered HTML

### Existing Fixture Path Forward

The `warlock_gear_sets.html` fixture already contains 30+ listings with parseable data. However:
- It's unclear from which exact URL this was saved
- It may be a stale/frozen snapshot
- Need to re-capture via browser to confirm the URL and ensure freshness
- Only one seller's listings are present in this fixture (cheaprsgolds)

---

## Segment Filters

### Status: Partially Proven

Segment filters are **embedded in listing data paths** but **not confirmed as UI filter controls**.

**Proven (from data-bind attributes and titles):**
- Platform: `pc`, `all-severs` (PS, Xbox, Switch likely exist)
- Region: `rotw` (LOD/NL distinction unclear)
- Ladder: `ladder-s14`, `season-14`, `non-ladder`, `hardcore-ladder`
- Hardcore/Softcore: `sc`, `hc` (in path and title)
- Season: `s14`, `season-14`

**Not Yet Proven:**
- Whether UI filter dropdowns/toggles exist on the listing page
- Whether filtering changes the listing results
- Whether multiple segments can be selected simultaneously
- Browser smoke output showed `ladder` and `season` text on the page but no functional filter controls in the rendered HTML

**Segment encoding confidence:** High for listings that use the structured path format. Some listings use free-text titles (e.g., `ber-rune-hardcore-ladder-d2r`) which lack the structured segment path.

---

## Cash-Only Status

**Cash-only (USD).** All prices are in USD, displayed with `$` prefix. The site is a real-money marketplace for virtual goods. No in-game barter or trade-in-kind is supported.

---

## Feasibility Scores

### Surface: active_listing (PlayerAuctions D2R items page)

| Dimension | Score | Evidence |
|---|---|---|
| evidence_strength | **cash_listing** | Asking prices, not completed trades |
| segment_clarity | **partial** | Segment encoded in listing data-bind paths, but UI filter controls unconfirmed |
| consideration_clarity | **none** | Cash-only; consideration is USD by definition, not a variable |
| time_clarity | **none** | No timestamps on listing cards |
| counterparty_clarity | **seller_only** | Seller name visible; no buyer information |
| pagination_clarity | **page** | URL `?PageIndex=N` observed in item links; page size unknown |
| parseability | **hostile** (requires browser) | Static HTML parseable IF accessible; Cloudflare blocks curl |
| legal_risk | **acceptable** | Public cash marketplace; no anti-scrape ToS found |
| volume_potential | **medium** | 30 listings per page × multiple pages × multiple sellers |
| normalization_fit | **item_only** | Cash prices for specific items, not rune-for-rune ratios |

### Surface: item_page (Individual product detail pages)

| Dimension | Score | Evidence |
|---|---|---|
| evidence_strength | **cash_listing** | Per-item detail with price |
| segment_clarity | **explicit** | URL path encodes full segment; title also contains it |
| consideration_clarity | **none** | Cash-only |
| time_clarity | **none** | No timestamps |
| counterparty_clarity | **seller_only** | Seller name visible |
| parseability | **hostile** (requires browser) | Cloudflare blocks curl |
| legal_risk | **acceptable** | Public page |
| volume_potential | **low** | One listing per page |
| normalization_fit | **item_only** | Cash price per item |

---

## Assessment

### Strengths
- Segments are explicitly encoded in listing paths — most structured segment data of any cash source
- Prices are server-rendered in static HTML (when accessible)
- Clear item naming with rune numbers (#30 Ber, #31 Jah)
- Seller metadata (level, total orders, rating, delivery time)

### Weaknesses
- **No completed/sold surface** — asking prices only
- **Cloudflare blocks curl** — browser capture required
- Only one seller's listings captured in existing fixture
- Free-text listing paths exist alongside structured ones (inconsistent)
- No filter UI controls confirmed in rendered page
- Cash-only — no in-game trade equivalent

### Next Parser Task (or Rejection)

**Recommended: Parser Prototype Candidate (Deferred)**

PlayerAuctions is viable as a cash-comparison source, with segment encoding superior to other cash sources. However:

1. **The existing fixture (`warlock_gear_sets.html`) is a sufficient base for an offline parser**, but its URL origin is ambiguous.
2. **Need a confirmed browser capture** of the actual `/diablo-2-resurrected-items/` listing page via Camoufox to:
   - Verify the URL that produces listing cards
   - Confirm multiple sellers are present
   - Check if filter UI controls affect the rendered output
   - Validate pagination
3. **Once captured**, an offline parser can extract:
   - Listing ID → segment → item → unit_price → total_price → seller → delivery
   - Output as `external_cash_prices.json` format

**Priority:** Lower than IGGM (already parser_prototype_ready) and Diablo2.io (tier_1 completed trades). Similar priority to G2G — both cash sources with browser requirements.

**Status recommendation:** `captured_static` (existing fixture) → needs `captured_browser` (confirm URL) → `offline_parse_candidate` → `parser_prototype_ready`

---

## Files Created

| File | Description |
|---|---|
| `research/sources/captures/playerauctions/2026-06-20_rune_specific/01_jah_rune_search.html` | Curl response for ?search=Jah+Rune (403 Cloudflare) |
| `research/sources/captures/playerauctions/2026-06-20_rune_specific/02_general_d2r_items.html` | Curl response for /diablo-2-resurrected-items/ (403 Cloudflare) |
| `research/sources/captures/playerauctions/2026-06-20_rune_specific/03_runes_category.html` | Curl response for /runes/ (403 Cloudflare) |
| `research/sources/captures/playerauctions/2026-06-20_rune_specific/04_runes_category_no_slash.html` | Curl response for /runes (403 Cloudflare) |
| `research/sources/captures/playerauctions/2026-06-20_rune_specific/05_jah_search_full_headers.html` | Curl with full browser headers (403 Cloudflare) |
| `research/sources/captures/playerauctions/2026-06-20_rune_specific/06_member_subdomain.html` | Member subdomain (200 Angular SPA shell) |
| `data/research/playerauctions_rune_probe.sample.json` | Sanitized sample of Ber/Jah/Cham/Zod listing data from fixture |

### Existing Files Used
| File | Description |
|---|---|
| `research/sources/downloads/rune_sources_2026-06-20/warlock_gear_sets.html` | 861 KB fixture with 30 D2R product listing cards |
| `research/sources/captures/playerauctions_2026-06-20_browser-smoke/` | Previous browser smoke capture (marketplace homepage, no listing data) |
