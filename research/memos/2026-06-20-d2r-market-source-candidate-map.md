# D2R Market Source Candidate Map

Generated: 2026-06-20
Based on: source_manifest.json (20 sources), 16 memos, 12 source notes, PROJECT_MEMORY.md

---

## 1. Player Completed-Trade Candidates

Sources exposing actual completed trades between players.

### Traderie API
- **Why useful:** Primary in-game barter source. Unofficial API returns completed trades with seller, price items, quantities, timestamps. Already powers rune VWAP model.
- **Best surface:** `GET /api/diablo2resurrected/listings?completed=true&item={id}&prop_Platform=PC&prop_Mode={mode}&prop_Ladder={bool}`
- **Extraction difficulty:** Low (cloudscraper, JSON API, no JS required)
- **Rune ratios:** Yes — only current source for Ist-normalized VWAP across 4 segments
- **Item prices:** Yes — but current pipeline only models runes
- **Evidence surface captured?** Yes (multiple raw payloads, 2,570 trades across 4 CSVs)
- **Parser exists?** validated (fetch → extract → price → generate JSON)
- **use_in_model?** true
- **Current priority:** tier_1
- **Flag:** No flag — this is the only properly integrated source.

### Diablo2.io Sold Search
- **Why useful:** Search-level filter `activesold=1` returns WTS/WTB SOLD rows with seller, buyer (sometimes), accepted consideration, relative time. Closest second completed-trade source to Traderie.
- **Best surface:** `search.php?keywords={rune}&activesold=1&uitemid={id}&fid[]=16`
- **Extraction difficulty:** Medium (static HTML parse from saved fixture, but pagination/segment-filters need validation)
- **Rune ratios:** Yes — Jah fixture shows clean rune-for-rune trades: 11 Ist, 2 Ber, 1 Sur+1 Lo, etc.
- **Item prices:** Possible for non-rune items via `uitemid` parameter
- **Evidence surface captured?** Yes — Jah sold search fixture saved (7 rows). Ber fixture URL known but not captured.
- **Parser exists?** prototype (parse_diablo2io_sold_search_offline.py exists, Jah output at data/research/diablo2io_sold_jah_trades.sample.json)
- **use_in_model?** false (all rows marked use_in_model=false until parser validation)
- **Current priority:** tier_1 (but 0 captures in manifest artifacts — only fixture)
- **Flag:** Manifest says tier_1 but no current_artifacts listed. Parser runs on fixture, not live data. Rating is correct pending validation.

### Diablo2.io Item Price History
- **Why useful:** Per-item page (e.g., `misc/jah-t43.html`) shows "Sold for: (last 10, 3d lag, 1d cache)" — compact historical summary.
- **Best surface:** Item detail pages
- **Extraction difficulty:** Low (static HTML, compact format)
- **Rune ratios:** Yes — shows 10 most recent sold prices per item
- **Item prices:** Yes for any item with a page
- **Evidence surface captured?** No (not separately captured as fixture)
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** tier_1 (implicit, via same source)

---

## 2. Player Active-Listing Candidates

Sources with WTS/WTB listings (not completed).

### Diablo2.io Active Trade Browse
- **Why useful:** `browsetrades.php` shows active WTS/WTB listings with asking prices. Order-book signal, not completed trades.
- **Best surface:** `browsetrades.php?sk=t&sd=d&ladder=1&hc=2&plat_pc=1&mode=highrunes`
- **Extraction difficulty:** Low (static HTML)
- **Rune ratios:** Partial — asking prices, not executed trades
- **Item prices:** Yes for browseable categories
- **Evidence surface captured?** No (inspected cursorily, no saved fixture)
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** tier_1 (implicit, via same source)

### Traderie Active Listings
- **Why useful:** Same API endpoint without `completed=true` returns active listings. Not currently used.
- **Best surface:** Same endpoint, omit completed param
- **Extraction difficulty:** Low
- **Rune ratios:** Partial (asking only)
- **Item prices:** Yes
- **Evidence surface captured?** No
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** tier_1 (implicit, via same source)

---

## 3. Cash/RMT Comparison Candidates

Sources with real-money prices.

### IGGM
- **Why useful:** 30 rune prices captured via browser, high segment confidence (PC/NL/SC/ROTW). Clean `lkr` attribute extraction.
- **Best surface:** `iggm.com/d2-resurrected-items` (runes category)
- **Extraction difficulty:** Low (extractable from rendered HTML attributes)
- **Cash-only or in-game barter?** Cash-only (USD, asking prices)
- **Rune ratios:** Yes (but cash prices, not in-game ratios)
- **Item prices:** Partial (rune-only parser; items mentioned but not profiled)
- **Evidence surface captured?** Yes — 2 captures, 30 observations extracted
- **Parser exists?** validated (parse_iggm_offline.py → iggm_cash_prices.json)
- **use_in_model?** false (external comparison only)
- **Current priority:** tier_2

### G2G
- **Why useful:** Large cash marketplace. Category pages render rune prices via Camoufox. Vue.js SPA but extractable after render.
- **Best surface:** `g2g.com/categories/diablo-2-resurrected-item-for-sale` (filtered to runes)
- **Extraction difficulty:** Medium (needs browser for SPA; offer detail pages crash Camoufox)
- **Cash-only or in-game barter?** Cash-only (USD, asking prices)
- **Rune ratios:** Yes (cash only)
- **Item prices:** Yes (broad marketplace)
- **Evidence surface captured?** Yes — lowest-price runes + cat-filtered captures
- **Parser exists?** none (deferred pending LoD/ROTW resolution)
- **use_in_model?** false
- **Current priority:** tier_2

### PlayerAuctions
- **Why useful:** Best structured cash-market HTML artifact. `data-bind` attribute encodes listing path, segment, item. JavaScript price table found in saved HTML.
- **Best surface:** Rune-specific search URL (not yet identified) or product detail pages
- **Extraction difficulty:** Low (static HTML with structured attributes) to Medium (need rune-specific URL for prices)
- **Cash-only or in-game barter?** Cash-only (USD)
- **Rune ratios:** Yes (cash only, excellent segmentation encoding)
- **Item prices:** Yes (broad item coverage including runewords, uniques)
- **Evidence surface captured?** Yes — browser smoke capture saved, but no rune-specific URL yet
- **Parser exists?** none (needs rune-specific capture first)
- **use_in_model?** false
- **Current priority:** tier_2

### items7
- **Why useful:** Simplest static cash pricing. Has prices in HTML but per-rune mapping not extractable.
- **Best surface:** items7.com runes category (needs browser render)
- **Extraction difficulty:** Medium (static HTML has prices but no name-price mapping; browser render likely cleans this up)
- **Cash-only or in-game barter?** Cash-only (USD)
- **Rune ratios:** Yes (cash only)
- **Item prices:** No (runes only on captured page)
- **Evidence surface captured?** Yes — static HTML downloaded
- **Parser exists?** prototype (parse_items7_offline.py documents 0 rows — static insufficient)
- **use_in_model?** false
- **Current priority:** tier_2

### Odealo
- **Why useful:** React app with excellent segmentation (PC/PS/Xbox/Switch, ladder/NL, SC/HC, ROTW). JSON-LD AggregateOffer with 155 offers.
- **Best surface:** `odealo.com/games/diablo-2-resurrected/marketplace/runes` (rune-specific URL)
- **Extraction difficulty:** Medium (React SPA, needs browser render of rune-specific page)
- **Cash-only or in-game barter?** Cash-only (USD)
- **Rune ratios:** Yes (cash only)
- **Item prices:** Yes (broad inventory)
- **Evidence surface captured?** Yes — browser smoke capture of general items page. Rune-specific URL not yet captured.
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** tier_3

### AOEAH
- **Why useful:** All 33 runes present in static HTML. Prices in CSS-styled elements.
- **Best surface:** `aoeah.com/diablo-2-resurrected/runes` (individual product pages likely have prices)
- **Extraction difficulty:** Medium (prices not plain-text in category page; individual pages may be cleaner)
- **Cash-only or in-game barter?** Cash-only (USD)
- **Rune ratios:** Yes (cash only)
- **Item prices:** No (runes only on captured page)
- **Evidence surface captured?** Yes — static HTML
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** tier_3

### itemnow (d2items_for_sale)
- **Why useful:** WordPress/WooCommerce site. WordPress REST API (wp-json) exposed — may provide structured product data with prices.
- **Best surface:** WordPress REST API (not yet queried). Product pages have server-rendered prices.
- **Extraction difficulty:** Medium (WP API discovery needed; AJAX prices)
- **Cash-only or in-game barter?** Cash-only (USD)
- **Rune ratios:** Yes (cash only)
- **Item prices:** Likely (WooCommerce shop)
- **Evidence surface captured?** Yes — static HTML of runes category
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** tier_3

### YesGamers
- **Why useful:** Best segment UI (ladder/SC/HC/ROTW toggles). Rich product data behind login.
- **Best surface:** Product detail pages (behind login)
- **Extraction difficulty:** High (login wall)
- **Cash-only or in-game barter?** Cash-only (USD)
- **Rune ratios:** Yes (cash only, but behind login)
- **Item prices:** Yes (broad inventory including Annihilus, Torch, Shako)
- **Evidence surface captured?** Yes — browser smoke capture (screenshot, HTML). No prices visible.
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** tier_3 (deferred)

### Chicks Gold
- **Why useful:** Minimal. Dynamic shell (6 KB). No segment filters visible.
- **Best surface:** Main page
- **Extraction difficulty:** High (fully dynamic, no segment info)
- **Cash-only or in-game barter?** Cash-only
- **Rune ratios:** Unlikely (no rune names in static HTML)
- **Item prices:** Unknown
- **Evidence surface captured?** Yes — static HTML
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** later

### eBay
- **Why useful:** General marketplace with D2R items. Can filter by sold items for completed sale prices.
- **Best surface:** eBay search for "diablo 2 resurrected rune" with Sold filter
- **Extraction difficulty:** High (anti-bot, general marketplace, inconsistent naming)
- **Cash-only or in-game barter?** Cash-only
- **Rune ratios:** Weak (no segment filtering)
- **Item prices:** Yes but noisy
- **Evidence surface captured?** No
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** later

### Eldorado.gg
- **Why useful:** Cash marketplace, unknown segment support. Not yet evaluated.
- **Best surface:** `/diablo-2-resurrected/` category page
- **Extraction difficulty:** Unknown
- **Cash-only or in-game barter?** Cash-only
- **Rune ratios:** Unknown
- **Item prices:** Unknown
- **Evidence surface captured?** No
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** later

### MMOPixel
- **Why useful:** Cash marketplace, unknown segment support. Not yet evaluated.
- **Best surface:** `/diablo-2-resurrected` category page
- **Extraction difficulty:** Unknown
- **Cash-only or in-game barter?** Cash-only
- **Rune ratios:** Unknown
- **Item prices:** Unknown
- **Evidence surface captured?** No
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** later

### MuleFactory
- **Why useful:** Cash marketplace, unknown. Not yet evaluated.
- **Best surface:** `/diablo-2-resurrected/` category page
- **Extraction difficulty:** Unknown
- **Cash-only or in-game barter?** Cash-only
- **Rune ratios:** Unknown
- **Item prices:** Unknown
- **Evidence surface captured?** No
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** later

### RPGStash
- **Why useful:** Cash marketplace, unknown. Not yet evaluated.
- **Best surface:** `/diablo-2-resurrected` category page
- **Extraction difficulty:** Unknown
- **Cash-only or in-game barter?** Cash-only
- **Rune ratios:** Unknown
- **Item prices:** Unknown
- **Evidence surface captured?** No
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** later

---

## 4. Forum/Community Signal Candidates

Sources with qualitative market discussion.

### Reddit (r/D2R_Marketplace, r/Diablo_2_Resurrected, r/diablo2)
- **Why useful:** Venue discovery (Traderie mentioned 45×, Discord 18×), player language (PGems 88+), item candidates, new-player pain points.
- **Best surface:** Pushshift API (already collected 2,998 posts)
- **Extraction difficulty:** Low (API) but low signal density (8 direct-market posts out of 2,998)
- **Rune ratios:** No (qualitative only)
- **Item prices:** No
- **Evidence surface captured?** Yes — 2,998 post metadata, 0 comment trees
- **Parser exists?** validation-level (reddit_extract_items.py)
- **use_in_model?** false
- **Current priority:** tier_3 (deferred)

### d2jsp
- **Why useful:** Forum-based economy using Forum Gold (FG). Separate from in-game rune economy but influential. FG-to-Ist conversion is an indirect reference.
- **Best surface:** `forums.d2jsp.org` — price check forum or searchable trade history
- **Extraction difficulty:** High (requires forum scraping or manual review; no public API)
- **Rune ratios:** Indirect (FG-denominated market, requires conversion methodology)
- **Item prices:** Yes (broad forum marketplace)
- **Evidence surface captured?** No
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** tier_3

### Diablo2.io General Forum Discussions
- **Why useful:** Community forums alongside trade system. Qualitative sentiment.
- **Best surface:** Forum threads
- **Extraction difficulty:** Low
- **Rune ratios:** No
- **Item prices:** No
- **Evidence surface captured?** No
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** tier_1 (by source priority — but qualitative content is same priority bracket)

---

## 5. Price-Guide/Reference Candidates

Static price lists or reference pages.

### d2jsp Price Check Forum
- **Why useful:** Players post price checks and other players respond with FG values. Historical reference for FG-denominated pricing.
- **Best surface:** Price check subforum
- **Extraction difficulty:** High (forum scraping, FG values are qualitative)
- **Rune ratios:** Indirect (FG-based)
- **Item prices:** Yes (FG-denominated)
- **Evidence surface captured?** No
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** tier_3

### Diablo2.io Item Price History Pages
- **Why useful:** Compact "Sold for: (last 10)" per item. Historical summary.
- **Best surface:** `misc/{item}-t{id}.html`
- **Extraction difficulty:** Low
- **Rune ratios:** Yes (reference only)
- **Item prices:** Yes
- **Evidence surface captured?** Partial (inspected cursorily)
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** tier_1 (by source priority)

---

## 6. Discord/Manual-Only Candidates

Sources requiring login, invite, or manual collection.

### Discord — Baal's Ledger
- **Why useful:** Discord trade bot mentioned in Reddit posts. May have a public trade feed or API.
- **Best surface:** Discord server or potential web interface
- **Extraction difficulty:** High (requires joining server or finding web interface; potential API unknown)
- **Rune ratios:** Unknown
- **Item prices:** Unknown
- **Evidence surface captured?** No
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** later

### D2Stock
- **Why useful:** Unknown nature — may be price aggregator, source directory, or forum.
- **Best surface:** `d2stock.com/`
- **Extraction difficulty:** Unknown (not yet visited)
- **Rune ratios:** Unknown
- **Item prices:** Unknown
- **Evidence surface captured?** No
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** later

---

## 7. API/Network Data Candidates

Sources where hidden endpoints were observed or suspected.

### PlayerAuctions API Endpoints
- **Why useful:** Three endpoints discovered: `user-api.playerauctions.com`, `public-api.playerauctions.com`, `account-api.playerauctions.com`. May serve listing/pricing data.
- **Best surface:** `public-api.playerauctions.com` — try unauthenticated GET
- **Extraction difficulty:** Unknown (not tested)
- **Rune ratios:** Yes (if listing data available)
- **Item prices:** Yes
- **Evidence surface captured?** No (endpoints noted but not queried)
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** tier_2 (by source priority, speculative)

### G2G CDN/API Endpoints
- **Why useful:** `sls.g2g.com` likely primary API backend. `assets.g2g.com/offer/categories.json`, `keyword.json`, `navigation.json` are unauthenticated CDN files.
- **Best surface:** `assets.g2g.com/offer/categories.json` — already readable
- **Extraction difficulty:** Low (CDN JSON endpoints are unauthenticated)
- **Rune ratios:** No (category taxonomy, not pricing)
- **Item prices:** No
- **Evidence surface captured?** No (endpoints noted but not saved as artifacts)
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** tier_2 (by source priority)

### itemnow WordPress REST API
- **Why useful:** WordPress REST API at `/wp-json/` may expose product data with prices. WooCommerce endpoints often include `product` and `product_cat` resources.
- **Best surface:** `itemnow.com/wp-json/wp/v2/product_cat/99` (already observed)
- **Extraction difficulty:** Low (WordPress REST API is unauthenticated by default)
- **Rune ratios:** Yes (if prices per product)
- **Item prices:** Yes (WooCommerce product catalog)
- **Evidence surface captured?** No (endpoint noted but not queried)
- **Parser exists?** none
- **use_in_model?** false
- **Current priority:** tier_3

### Traderie API (Internal Details)
- **Why useful:** Already integrated. Pagination (`nextPage` cursor), listing IDs, seller metadata fields now captured. Buyer fields NOT exposed by API (confirmed).
- **Best surface:** Same endpoint as above
- **Extraction difficulty:** Low (already working)
- **Rune ratios:** Yes
- **Item prices:** Yes
- **Evidence surface captured?** Yes (multiple raw payloads)
- **Parser exists?** validated
- **use_in_model?** true
- **Current priority:** tier_1

---

## Source-Agnostic Market Hypothesis

### All Theoretical Collection Methods

| Method | Description | Status |
|---|---|---|
| **API scraping** | Site has public/undocumented JSON API | Tried on Traderie (working). Noted on G2G, PlayerAuctions, itemnow (unqueried). |
| **Forum scraping** | Parse HTML forum pages for trade posts | Tried on Diablo2.io (prototype). Not tried on d2jsp. |
| **Browser automation** | Render JS SPAs, capture rendered HTML | Tried on 6 sites (G2G, IGGM, Odealo, PlayerAuctions, YesGamers). Working for most. |
| **Manual HTML save** | User saves page via browser | Tried on Diablo2.io Jah fixture. Ber fixture planned. |
| **Static HTML download** | curl/wget for server-rendered pages | Tried on 10 sites. Only items7 and PlayerAuctions had extractable data. |
| **Reddit API** | Pushshift/PRAW for post metadata | Tried (2,998 posts). Low signal density. |
| **WordPress REST API** | Unauthenticated WP JSON endpoints | Noted for itemnow. Not queried. |
| **Discord bot monitoring** | Monitor trade bot feed/channel | Not tried. Baal's Ledger identified as candidate. |
| **eBay API** | eBay Finding/Shopping API | Not tried. |
| **Cash marketplace API** | Public or undocumented listing API | Noted for PlayerAuctions. Not queried. |
| **In-game capture** | Screenshot/OCR from game client | Not tried. Would require different tooling. Not proposed. |

### Method Gaps Worth Closing

1. **PlayerAuctions API endpoints** — `public-api.playerauctions.com` and `user-api.playerauctions.com` should be probed with a simple unauthenticated GET to see if they return listing data. This is the highest-ROI untested collection method because the endpoints were explicitly seen in the page HTML.

2. **itemnow WordPress REST API** — Query `/wp-json/wp/v2/product?categories=99` or similar. WordPress REST APIs are famously open. Could yield structured product data with prices in minutes.

3. **Diablo2.io Ber sold-search fixture** — Already planned as P0. Same structure as Jah fixture. Would double parsed evidence base.

4. **d2jsp public price check forum** — Needs a one-off visit to determine if trade history is accessible without login. If yes, forum scraping is feasible.

5. **PlayerAuctions rune-specific URL** — Find the correct filtered/search URL that shows rune listings with prices. The homepage showed navigation only.

6. **Odealo rune marketplace page** — The rune-specific URL (`/games/diablo-2/marketplace/runes`) is known but never captured. Prices render in React.

---

## Next Probe Candidates

Ranked by expected value per unit effort.

### #1: PlayerAuctions rune-specific URL capture
- **Source:** PlayerAuctions
- **Surface to probe:** Rune search or filtered URL (e.g., `playerauctions.com/diablo-2-resurrected-items/search?q=rune`)
- **Why promising:** Already captured_browser. Homepage showed navigation but the `data-bind` attributes with structured segment info prove pricing data exists. A rune-filtered URL is the missing piece.
- **Successful probe proves:** PlayerAuctions can become a parsed cash-price source for runes. Structured segment encoding enables clean segment tracking.
- **Estimated effort:** 30 minutes (find URL via manual browse → Camoufox capture → inspect)

### #2: itemnow WordPress REST API probe
- **Source:** itemnow.com (d2items_for_sale)
- **Surface to probe:** `itemnow.com/wp-json/wp/v2/product?categories=99&per_page=100`
- **Why promising:** WordPress REST APIs are typically unauthenticated and return structured JSON (title, price, categories). The WP API root was already confirmed at `/wp-json/`. WooCommerce extends WP API with product endpoints.
- **Successful probe proves:** Structured product data with prices available without JS rendering. Could yield 30+ rune prices in <5 min.
- **Estimated effort:** 10 minutes (curl API root → discover product endpoint → query with category filter)

### #3: Diablo2.io Ber sold-search fixture
- **Source:** Diablo2.io
- **Surface to probe:** `diablo2.io/search.php?keywords=Ber&activesold=1&uitemid=45`
- **Why promising:** P0 per validation plan. Jah fixture proves the surface; Ber tests parser generalizability and doubles evidence base. No code changes needed.
- **Successful probe proves:** Parser handles multiple runes. ITEM_NAME_MAP correctly resolves `runeBer_sicon`. Segment icon classes consistent across runes.
- **Estimated effort:** 10 minutes (save HTML → run parameterized parser)

### #4: IGGM segment variation capture
- **Source:** IGGM
- **Surface to probe:** `iggm.com/d2-resurrected-items` with Ladder filter toggled
- **Why promising:** IGGM is the most trusted cash source (parser_prototype_ready, 30 runes). Testing Ladder vs Non-Ladder would reveal whether IGGM prices vary by segment — critical for segment-aware cash comparison.
- **Successful probe proves:** Either (a) prices vary by segment → need per-segment cash product, or (b) prices are constant → simplifies segment handling.
- **Estimated effort:** 20 minutes (Camoufox capture with different filter → re-run parser)

### #5: Odealo rune marketplace capture
- **Source:** Odealo
- **Surface to probe:** `odealo.com/games/diablo-2-resurrected/marketplace/runes`
- **Why promising:** JSON-LD already showed 155 offers aggregate. Rune-specific URL likely renders per-rune prices in React after hydration. Excellent segment filtering (PC/console, ladder, SC/HC, ROTW).
- **Successful probe proves:** Third cash-price source for runes. Best segment diversity beyond IGGM.
- **Estimated effort:** 30 minutes (Camoufox capture rune page → inspect rendered HTML for prices)

### #6: PlayerAuctions public API probe
- **Source:** PlayerAuctions
- **Surface to probe:** `GET https://public-api.playerauctions.com/` (unauthenticated)
- **Why promising:** Endpoint explicitly observed in page HTML. May expose listing data without browser. If it returns structured JSON, this is the highest-ROI cash data source.
- **Successful probe proves:** Cash pricing available via direct API, bypassing browser automation entirely for PlayerAuctions.
- **Estimated effort:** 10 minutes (curl endpoint → inspect response)

### #7: d2jsp accessibility check
- **Source:** d2jsp
- **Surface to probe:** `forums.d2jsp.org` — check if price check forum or trade history is readable without login
- **Why promising:** FG economy is influential in D2R trading. A public price-check forum would enable forum-based pricing reference (FG-denominated, requiring separate methodology).
- **Successful probe proves:** d2jsp is a viable forum-scraping source, or is login-walled and should be deferred.
- **Estimated effort:** 15 minutes (manual browse → check view-source for login requirement)

---

## Summary

- **20 sources cataloged** (1 integrated, 1 parser_prototype_ready, 3 captured_browser, 3 captured_static, 1 offline_parse_candidate, 1 deferred, 8 discovered, 2 later)
- **2 player completed-trade candidates** (Traderie integrated, Diablo2.io pending parser validation)
- **13 cash/RMT candidates** (1 parsed, 12 at various pre-parser stages)
- **2 forum/community candidates** (Reddit mined, d2jsp untouched)
- **2 Discord/manual candidates** (both untouched)
- **4 API/network candidates** (Traderie working; PlayerAuctions, G2G, itemnow endpoints unqueried)
- **7 untested collection methods** (vs 4 tested: API scraping, browser automation, static HTML, Reddit API)
- **Ranked next probes:** PlayerAuctions rune URL > itemnow WP API > Diablo2.io Ber > IGGM segment > Odealo rune > PlayerAuctions public API > d2jsp login check
