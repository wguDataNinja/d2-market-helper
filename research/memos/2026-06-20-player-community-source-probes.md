# Player/Community Source Probes — 2026-06-20

## Summary

Probed d2jsp (forums.d2jsp.org), Reddit (r/D2R_Marketplace, r/diablo2, r/Diablo_2_Resurrected), and Diablo2.io for non-cash player/community trade data. Diablo2.io is the standout — it has both completed-trade (sold search) and active-listing surfaces with static HTML, pagination, and data-param-based segment filters. Reddit is qualitative-only. d2jsp is fully gated behind login (Camoufox confirms guest view shows no topics, only login wall).

## Per-Source Findings

### d2jsp (forums.d2jsp.org)

| Attribute | Finding |
|---|---|
| Main page via curl | 403 (Cloudflare) |
| Main page via Camoufox | 200 — login wall. 26KB page shows forum categories and login form. No topics visible. |
| D2R Trade Forum (f=271) via Camoufox | 200 — login wall. 16KB. 0 topic titles found. |
| D2R Price Check (f=272) via Camoufox | 200 — login wall. 16KB. 0 topic titles found. |
| Jah search via Camoufox | 200 — login wall. 26KB. Identical to main page. |
| Guest access | ❌ No public topic list, no search results, no trade data. |
| FG mentions | FG header appears in all pages. No FG-denominated trade data accessible. |
| Rune mentions | 20–45 per page, but these are likely forum-description/footer text, not actual listings. |
| **Verdict** | **Gated/manual.** Public crawl is not viable without login. No structured trade data accessible. |

**FG note:** Cannot confirm whether FG-denominated trades could serve as rune ratio reference. The 2 FG mentions per page are site-level navigation text, not trade content. FG pricing evidence class would require logged-in access.

### Reddit

| Attribute | Finding |
|---|---|
| reddit.com/.json (new Reddit) | 403 — Cloudflare blocks curl |
| old.reddit.com (HTML) | 200 — accessible, parseable HTML |
| r/D2R_Marketplace (25 posts) | Mixed: PC, WTB/WTS, price-checks, show-offs. 4 trade-tagged posts. 542 rune mentions in comments. No structured completed-trade surface. |
| r/diablo2 (25 posts) | General discussion. 660 rune mentions. 0 trade-tagged posts. |
| r/Diablo_2_Resurrected (25 posts) | General discussion. 779 rune mentions. 1 trade-tagged post. |
| Search: Jah/Ber/Lo on r/D2R_Marketplace | Results show mixed content. 42 titles per search. 2–4 trade tags. |
| **Verdict** | **Qualitative only.** No structured completed-trade or active-listing surface. Useful for venue discovery, player language, item candidates. Not for pricing. |

### Diablo2.io

| Attribute | Finding |
|---|---|
| Main page via curl | 200 — 201KB static HTML |
| Ber Sold Search | 200 — 186KB. 11 sold_class elements, 33 SOLD text mentions. Structured trade rows. |
| Ber Sold + Ladder (sc=1) | 200 — 186KB. Same counts. Ladder param may need `ladder=1` (data-param discovered). |
| Ber Sold + HC (hc=1) | 200 — 171KB. 7 sold_class (vs 11 non-HC). HC filter confirmed working. |
| Jah Sold Page 2 (&start=50) | 200 — 114KB. Pagination confirmed functional. |
| Jah Price History (misc/jah-t43.html) | 200 — 302KB. Item info + "Prices and Demand" section + "On the trade market". 25 sold_class elements. |
| Browse Trades (browsetrades.php) | 200 — 324KB. Active listings. 23 WTS, 20 WTB, 27 SOLD. Rich platform data: 31 PC, 19 Switch, 19 Xbox, 20 PS. |
| **Segment filters** | Confirmed via `data-param` attributes: ladder=1/2, hc=1/2, plat_pc=1, plat_switch=1, wtbs=1/2 (WTS/WTB), activesold=1/2, plus item-specific filters (ed, eth, fcr, fhr, ias, charm, etc.) |
| **Parseability** | Static HTML. Excellent. Well-structured data-param attributes. |
| **Verdict** | **Strong completed-trade candidate.** Both active listings (browsetrades.php) and sold search (search.php?activesold=1) with segment filters, pagination, and platform data. |

## Per-Source Findings Table

| Source | Public Completed-Trades | Public Active-Listings | Qualitative Only | Gated/Manual | Parseability | Parser Feasibility (0–10) | Next Action |
|---|---|---|---|---|---|---|---|
| Diablo2.io | ✅ Yes (sold search, item history) | ✅ Yes (browsetrades.php) | ❌ No | ❌ No | Static HTML | 9 | Build sold-search parser. Validate completed-trade semantics. Integrate as first community-trade source. |
| Reddit | ❌ No | ❌ No | ✅ Yes | ❌ No (old.reddit.com accessible) | Static HTML (old.reddit) | 3 | Continue monitoring for structured trade threads. Not viable for pricing. |
| d2jsp | ❌ No | ❌ No | ❌ N/A | ✅ Yes (login required) | Gated | 0 | Deferred. No public data surface. Revisit only if login access approved. FG evidence class requires login. |

## Evidence Artifacts Captured

### Diablo2.io (research/sources/captures/diablo2io/2026-06-20_search_probe/)
- `ber_sold_search.html` (186KB) — Ber sold search results
- `ber_sold_ladder_filter.html` (186KB) — Ber sold + ladder filter (sc=1)
- `ber_sold_hc_filter.html` (171KB) — Ber sold + HC filter (hc=1)
- `jah_sold_page2.html` (114KB) — Jah sold search page 2 (&start=50)
- `jah_price_history.html` (302KB) — Jah item price history page (misc/jah-t43.html)
- `browsetrades.html` (324KB) — Active trade listings browser
- `main_page.html` (201KB) — Main page

### Reddit (research/sources/captures/reddit/2026-06-20_search_probe/)
- `r_d2r_marketplace.html` (163KB) — old.reddit.com/r/D2R_Marketplace
- `r_diablo2.html` (182KB) — old.reddit.com/r/diablo2
- `r_diablo2_resurrected.html` (194KB) — old.reddit.com/r/Diablo_2_Resurrected
- `search_jah_trade.html` (92KB) — r/D2R_Marketplace search for Jah
- `search_ber_trade.html` (91KB) — r/D2R_Marketplace search for Ber
- `search_lo_trade.html` (94KB) — r/D2R_Marketplace search for Lo

### d2jsp (research/sources/captures/d2jsp/2026-06-20_search_probe/)
- `browser_main.html` (26KB) — Browser-captured main page (login wall)
- `browser_d2r_trade_forum.html` (16KB) — Browser-captured D2R Trade Forum (login wall)
- `browser_d2r_price_check.html` (16KB) — Browser-captured D2R Price Check forum (login wall)
- `browser_search_jah.html` (26KB) — Browser-captured Jah search (login wall)

## Source Manifest Update Recommendations

1. **diablo2_io** — Upgrade status from `offline_parse_candidate` to `parser_prototype_ready`. Confirm `static_html` and `segment_filters` with evidence from data-param discovery. Add surfaves_checked parseability and pagination confirmations.

2. **reddit** — Status stays `deferred`. Evidence class stays `community_discussion`. Add known_url for old.reddit.com alternative access. Verify segment_filters remain at `false` (no segment UI on Reddit).

3. **d2jsp** — Status stays `discovered`. Add gated note. No change to known_urls or segment_filters until login access is approved.

## Key Discovery: Diablo2.io data-param Attributes

The page HTML embeds rich filter attributes via `data-param`:
- `data-param="ladder=1"` / `data-param="ladder=2"` — Ladder toggle
- `data-param="hc=1"` / `data-param="hc=2"` — Hardcore toggle
- `data-param="plat_pc=1"` / `data-param="plat_switch=1"` — Platform filter
- `data-param="wtbs=1"` / `data-param="wtbs=2"` — WTB/WTS direction
- `data-param="activesold=1"` / `data-param="activesold=2"` — Sold status
- `data-param="sf=titleonly"` / `data-param="sf=firstpost"` — Search scope
- `data-param="sr=topics"` / `data-param="sr=posts"` — Result type
- `data-param="ed=1"` / `eth=1` / `fcr=1` / `fhr=1` / `ias=1` — Item-specific filters

This is effectively an API-like query surface embedded in static HTML. A parser could:
1. Extract available filter toggles from data-param attributes
2. Construct URL params from selected toggles
3. Parse trade rows from static HTML
4. Paginate using &start=N
