# Market Source Inventory Audit

Date: 2026-06-20
Scope: Every source in `data/source_manifest.json` (20 sources)
Method: Cross-reference manifest entries against all saved artifacts, source notes, capture artifacts, and memos.

---

## Surface Inventory by Category

### Category: completed_player_trades

| source | known active listing surface | known sold/completed surface | known price-history surface | cash listing surface | item-specific URL known? | search URL params known? | segment filters known? | parseability status | capture status | parser status | evidence strength | next required probe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **traderie** | Known — API supports `completed=false` | Known — `completed=true` param, 2,570 trades extracted | Unproven — API window behavior unknown | N/A | Yes — `item={traderie_item_id}` | Yes — `completed`, `auction`, `prop_Platform`, `prop_Mode`, `prop_Ladder`, `item` | Proven — platform, mode (softcore/hardcore), ladder all verified via API response | API | integrated | integrated | completed_trade | Run one live fetch with full raw response logging to inspect pagination fields (total, page, limit), listing IDs, timestamps, seller/buyer fields |
| **diablo2_io** | Known — `browsetrades.php` active browse verified | Known — `activesold=1` Jah fixture saved and parsed (7 rows) | Known — item page "Sold for" history (`misc/jah-t43.html`) | N/A | Yes — `uitemid=N` pattern confirmed | Yes — `keywords`, `uitemid`, `activesold`, `fid`, `sf`, `sr` observed | Proven — ladder (`zi-nonladder`/`zi-ladder`), platform (`zi-pc`), region (`zi-americas`/`zi-europe`), ruleset (`zi-tinylogrotw`) confirmed in HTML; HC/SC not yet confirmed | Static | fixture_saved (Jah sold search) | prototype | completed_trade | Capture Ber sold search fixture to validate parser generalization and confirm HC/SC icon classes exist in search results |

### Category: cash_market

| source | known active listing surface | known sold/completed surface | known price-history surface | cash listing surface | item-specific URL known? | search URL params known? | segment filters known? | parseability status | capture status | parser status | evidence strength | next required probe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **iggm** | Known — rune listings visible in browser capture | Unproven — never searched for sold/completed | Unproven — never searched | Known — 30 rune prices extracted via offline parser | Unproven — page has item links but individual item pages never captured | Unproven — URL params not inspected; filter selection appears to use POST/JS | Proven — PC, Non-Ladder, Softcore, ROTW confirmed from page content; platform, ladder, HC, SC, season toggles visible | Rendered | browser_captured + fixture_saved (iggm_cash_prices.json) | validated | cash_listing | Capture Ladder and Hardcore segment variation to test if displayed prices differ |
| **g2g** | Known — category page renders 20+ listings | Unproven — never searched for sold/completed on G2G | Unproven — never searched | Known — asking prices visible in rendered DOM | Yes — `/offer/group?fa=...` pattern | Partial — `fa` filter param and `sort=lowest_price` verified; full param space not inspected | Unproven — manifest says platform=true (verified), ladder/hc/sc="partial (embedded in titles)". "partial" is accurate but "true" for ladder/hc/sc is misleading — no dedicated filter toggles exist | Rendered (Vue SPA) | browser_captured | prototype (samples extracted) | cash_listing | Capture ROTW-filtered rune search URL to resolve LoD/ROTW taxonomy ambiguity |
| **playerauctions** | Known — homepage rendered with data-bind attributes and nav items | Unproven — never searched for sold/completed | Unproven — never searched | Known — structured data-bind attributes encode listing metadata; price table exists in rendered HTML | Unproven — page has search URLs but never captured | Unproven — URL params not inspected | Proven — platform, ladder, hardcore, softcore, season encoded in listing paths (`pc--rotw--ladder-s14--sc--runes--runes30-ber`) | Rendered | browser_captured (homepage + warlock_gear_sets.html) | none | cash_listing | Capture rune-specific filtered search URL to get actual rune listing prices with prices visible |
| **items7** | Known — all 33 rune cards visible in static HTML | Unproven — never searched | Unproven — never searched | Partial — prices exist in HTML ($0.15-$2.85) but per-rune mapping unproven | Unproven — individual rune pages never captured | Unproven — URL params not inspected | Unproven — manifest says ladder=true, season=true based on navigation text, but never verified by testing URL filters or confirming toggle behavior | Static (prices loaded client-side) | static_captured | none (parse_items7_offline.py returned 0 rows) | cash_listing | Browser-capture items7 rendered rune page to see if client-side JS populates per-rune prices |
| **itemnow** | Known — product category page shows rune links | Unproven — never searched for sold/completed | Unproven — never searched | Partial — category page shows "Vary" for prices; WP REST API not queried | Partial — product links visible but never captured | Partial — `?server=...` params documented but never tested | Unproven — manifest says platform=true, ladder=true, hardcore=true. These are guessed from `?server=` param values, but no actual capture confirmed they work | Static (WordPress, prices AJAX-loaded) | static_captured | none | cash_listing | Query WordPress REST API root at `https://itemnow.com/wp-json/` to discover product endpoints with prices |
| **yesgamers** | Partial — page rendered with UI, prices behind login | Unproven — never searched | Unproven — never searched | Unproven — prices never visible; login required | Unproven — not captured | Unproven — not inspected | Unproven — manifest says ladder=true, hardcore=true, season=true. UI toggles visible but never verified while logged in | Rendered | browser_captured (UI only, no prices) | none (deferred) | forum_text | Deferred — requires login approval before any further investigation |
| **odealo** | Known — marketplace page renders listing titles in DOM | Unproven — never searched for sold/completed | Unproven — never searched | Partial — JSON-LD AggregateOffer (155 offers, $0.01-$999); per-item prices after hydration | Unproven — `/marketplace/runes` URL exists but smoke test used general items page | Unproven — URL params not inspected | Proven — platform, ladder, hardcore, softcore, season filters visible in UI (PC Ladder, PC Non-Ladder, Xbox Ladder, etc.) | Rendered (React) | browser_captured (smoke test, not rune-specific) | none | cash_listing | Capture dedicated rune marketplace URL: `/games/diablo-2-resurrected/marketplace/runes` |
| **aoeah** | Known — all 33 runes present in static HTML with CSS price classes | Unproven — never searched | Unproven — never searched | Partial — prices in CSS-styled elements, not plain-text extractable from category page | Unproven — individual rune product pages never captured | Unproven — URL params not inspected | Unproven — manifest says platform=true, ladder=true, season=true but these are visible as page UI elements, never verified by capture | Static | static_captured | none | cash_listing | Download individual rune product pages to see if prices are extractable per-rune |
| **chicksgold** | Unproven — 6 KB static shell, no listings visible | Unproven — never searched | Unproven — never searched | Unproven — no prices visible in static HTML | Unproven — not captured | Unproven — not inspected | Unproven — manifest says all false. This is correct based on observation, but "false" is accurate only for what was observed — we never confirmed there are no filters by interacting with the rendered page | Rendered (fully dynamic) | static_captured (ineffective — shell only) | none | reference_only | Browser-capture the page to determine if JS renders any listing content at all |
| **ebay** | Unproven — never visited | Unproven — never searched | Unproven — never searched | Unproven — no captures, no artifacts | Unproven — never visited | Unproven — never visited | Unproven — never visited; manifest guesses all false | Unknown | not_captured | none | reference_only | Visit eBay D2R rune search page and evaluate listing quality, structure, and segment support |
| **eldorado** | Unproven — never visited | Unproven — never searched | Unproven — never searched | Unproven — no captures, no artifacts | Unproven — never visited | Unproven — never visited | Unproven — never visited; manifest guesses all false | Unknown | not_captured | none | reference_only | Add to browser-capture queue after tier_2 sources are evaluated |
| **mmopixel** | Unproven — never visited | Unproven — never searched | Unproven — never searched | Unproven — no captures, no artifacts | Unproven — never visited | Unproven — never visited | Unproven — never visited; manifest guesses all false | Unknown | not_captured | none | reference_only | Add to browser-capture queue after tier_2 sources are evaluated |
| **mulefactory** | Unproven — never visited | Unproven — never searched | Unproven — never searched | Unproven — no captures, no artifacts | Unproven — never visited | Unproven — never visited | Unproven — never visited; manifest guesses all false | Unknown | not_captured | none | reference_only | Add to browser-capture queue after tier_2 sources are evaluated |
| **rpgstash** | Unproven — never visited | Unproven — never searched | Unproven — never searched | Unproven — no captures, no artifacts | Unproven — never visited | Unproven — never visited | Unproven — never visited; manifest guesses all false | Unknown | not_captured | none | reference_only | Add to browser-capture queue after tier_2 sources are evaluated |

### Category: forum_reference

| source | known active listing surface | known sold/completed surface | known price-history surface | cash listing surface | item-specific URL known? | search URL params known? | segment filters known? | parseability status | capture status | parser status | evidence strength | next required probe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **d2jsp** | Unproven — forum known, page never captured | Unproven — never searched for sold/completed trade surfaces | Unproven — never searched for price-check forum | N/A (FG economy) | Unproven — never visited | Unproven — never visited | Unproven — never visited; manifest says all false — this is a guess | Unknown | not_captured | none | reference_only | Visit d2jsp and evaluate whether price-check forum or trade history has any publicly accessible surface without login |

### Category: community_discussion

| source | known active listing surface | known sold/completed surface | known price-history surface | cash listing surface | item-specific URL known? | search URL params known? | segment filters known? | parseability status | capture status | parser status | evidence strength | next required probe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **reddit** | Known — 3 subreddits scraped, 2,998 posts collected | Partial — WTS/WTB/WTS SOLD posts present in corpus but not systematically extracted or quantified | Unproven — no comment tree analysis done | N/A | N/A (Reddit search by subreddit/keyword) | Known — Reddit API observed | N/A — Reddit has no segment filter UI | API (embedded JSON) | static_captured (raw/selected/notes directories) | none (deferred) | forum_text | Deferred — revisit only for hypothesis-driven comment fetches (e.g., "how often is 'sold for' mentioned in r/D2R_Marketplace comments") |
| **discord_baals_ledger** | Unproven — never contacted | Unproven — never searched | Unproven — never searched | N/A | Unproven — no Discord server joined, no web interface found | Unproven — never inspected | Unproven — never investigated | Unknown | not_captured | none | reference_only | Search for Baal's Ledger website or public trade feed before considering Discord bot investigation |

### Category: source_directory_only

| source | known active listing surface | known sold/completed surface | known price-history surface | cash listing surface | item-specific URL known? | search URL params known? | segment filters known? | parseability status | capture status | parser status | evidence strength | next required probe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **d2stock** | Unproven — never visited | Unproven — never searched | Unproven — never searched | N/A | Unproven — never visited | Unproven — never visited | Unproven — manifest says all false. This is a guess — never visited | Unknown | not_captured | none | reference_only | Visit d2stock.com and classify whether it has trade data, prices, or is a directory |

---

## Known Unknowns

### Sources where we have zero capture evidence
- **ebay** — discovered entry, never visited, no artifacts
- **eldorado** — discovered entry, never visited, no artifacts
- **mmopixel** — discovered entry, never visited, no artifacts
- **mulefactory** — discovered entry, never visited, no artifacts
- **rpgstash** — discovered entry, never visited, no artifacts
- **d2stock** — discovered entry, never visited, no artifacts
- **discord_baals_ledger** — discovered entry, never contacted, no artifacts
- **d2jsp** — discovered entry, never visited, no artifacts

### Sources where segment filters are assumed but not verified
- **items7** — manifest says `ladder: true, season: true`. ROTW ladder/non-ladder seen in navigation text, but no URL params tested; no capture confirms toggle behavior
- **aoeah** — manifest says `platform: true, ladder: true, season: true`. UI toggles visible in static HTML, but no URL capture confirms they produce different segment-specific pages
- **itemnow** — manifest says `platform: true, ladder: true, hardcore: true`. `?server=` params documented but never actually tested in a live URL
- **chicksgold** — manifest says all segment filters false. The static shell showed nothing, but no browser capture was done to confirm this is actually true when JS renders
- **yesgamers** — manifest says `ladder: true, hardcore: true, season: true`. UI toggles were visible but never verified while logged in
- **g2g** — manifest says `ladder: "partial (embedded in listing titles)", hardcore: "partial", softcore: "partial"`. This is accurate for the observed behavior, but "partial" is more honest than the `true` values assigned to other sources that were also never tested

### Sources where sold/completed surfaces were never searched
- Every single cash-market source (g2g, playerauctions, items7, iggm, itemnow, yesgamers, odealo, aoeah, chicksgold, ebay, eldorado, mmopixel, mulefactory, rpgstash) — none were searched for a sold/completed trade surface
- d2jsp — never searched
- discord_baals_ledger — never searched

### Sources where pagination was never tested
- **traderie** — API pagination/window behavior is the #1 risk. No `page`, `limit`, or cursor params ever tested
- **diablo2_io** — Jah sold-search fixture is single page; total results = 2,812 across 57 pages, pagination never tested
- **g2g** — single category page captured; pagination not evaluated
- **playerauctions** — homepage only; no pagination testing
- **iggm** — single rune page; pagination not evaluated
- **itemnow** — single category page; pagination not evaluated
- **odealo** — single page; pagination not evaluated
- **aoeah** — single category page; pagination not evaluated
- **reddit** — 2,998 posts collected; pagination was handled by the API but window limits unknown
- All never-captured sources: pagination entirely unknown

### Sources where URL params were not inspected
- **iggm** — filter selection appears to use POST or JS; URL params never inspected
- **yesgamers** — browser capture completed but URL params not inspected
- **odealo** — browser capture completed but URL params not inspected
- **aoeah** — static capture completed but URL params not inspected
- **chicksgold** — static capture (shell) but URL params not inspected
- All never-captured sources: URL params unknown

---

## Misclassified or Overranked

### Overranked: items7 at tier_2
Current priority: tier_2. Status: captured_static. The static HTML was downloaded and parsed, yielding 0 rows. The prices are loaded client-side and cannot be extracted without a browser capture. Tier_2 implies it should be higher priority than tier_3 sources, but ranking it above iggm (which has a working parser and 30 validated observations) or odealo (which has a browser capture with visible prices) is misleading. **Recommendation:** Downgrade to tier_3 until browser capture proves per-rune prices are extractable.

### Overranked: playerauctions at tier_2
Current priority: tier_2. The browser capture was of the homepage and the `warlock_gear_sets.html` artifact. Neither shows actual rune prices in a directly usable format — the homepage shows navigation items, and the data-bind attributes encode listing metadata but were never parsed into prices. Tier_2 implies it's readier than iggm (tier_3) when iggm has a validated parser and 30 observations. **Recommendation:** Downgrade to tier_3 until a rune-specific search URL is captured and parsed.

### Underranked: iggm at tier_3
Current priority: tier_3. iggm has the best evidence of any cash market source: browser capture confirmed, 30 rune prices extracted, segment confidence high, validated parser. It should be tier_2 at minimum, if not tier_1 for cash markets. The tier_3 label undermines its actual readiness. **Recommendation:** Upgrade to tier_2.

### Classification concern: g2g segment_filters values
The manifest uses `true` for platform and `"partial (embedded in listing titles)"` for ladder/hardcore/softcore. The platform value is correct — the filter dropdown was visible. But the ladder/hc/sc values being marked "partial" rather than true/false is an honest assessment. However, the `segment_filters` schema expects booleans and this uses strings — the validator passed so the schema must allow strings, but this inconsistency makes it harder to compare across sources. Not a reclassification, but worth normalizing.

### Borderline: diablo2_io segment_filters
Manifest says `platform: true, ladder: true, hardcore: true, softcore: true`. The fixture HTML confirmed `zi-pc` (platform) and `zi-nonladder`/`zi-ladder` classes. But `zi-softcore` and `zi-hardcore` were **not found** in the Jah fixture. Every row is softcore by default or the icon is not shown. `hardcore: true` and `softcore: true` are assumed, not proven. **Recommendation:** Change to `hardcore: "unproven"` and `softcore: "unproven"` until a fixture with explicit HC/SC filter confirms the icons appear.

### Questionable: itemnow segment_filters
Manifest says `platform: true, ladder: true, hardcore: true`. The source notes document `?server=d2r-non-ladder`, `?server=d2r-hc-non-ladder`, `?server=d2r-hc-ladder` params. These imply ladder and hardcore toggles, but no platform param was noted (which would imply platform is NOT filterable via URL). Yet the manifest says `platform: true`. This seems wrong. **Recommendation:** Set `platform: false` unless a platform-specific URL param is discovered.

---

## Key Findings Summary

1. **8 of 20 sources have zero capture evidence** — they exist only as manifest entries with URLs. This is fine for `later` priority sources, but the gap between "discovered" and "evaluated" is wide.

2. **Every cash-market source has never been searched for a sold/completed surface.** This is the single largest blind spot. If any cash site has a completed-sales filter (like eBay's "Sold Items"), we would have missed it entirely.

3. **Pagination is untested for every single source** except Reddit (via API). We do not know the window/limit behavior of any source.

4. **iggm is the strongest cash-market source** by a wide margin (validated parser, 30 observations, high segment confidence) but is ranked tier_3 below items7 and playerauctions which have zero working parsers.

5. **items7, playerauctions, and g2g are overranked** relative to their actual evidence readiness. Their tier_2 labels suggest they are closer to integration than the evidence supports.

6. **Segment filters are frequently assumed, not proven.** 5+ sources have segment_filters marked true based on UI observation alone, without confirming the filter actually works or produces segment-specific data.
