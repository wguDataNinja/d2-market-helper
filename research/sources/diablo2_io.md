# Diablo2.io — Source Notes

## Updated Finding (2026-06-20)

Diablo2.io has been re-evaluated after probing its **Sold trade-search surface** (`activesold=1`) and **active listing surface** (`browsetrades.php`), and confirming segment filters, pagination, and parseability.

### Sold Search Surface (`search.php?activesold=1`)

- URL pattern: `https://diablo2.io/search.php?...&activesold=1&uitemid=<item_id>`
- Ber fixture (new): `research/sources/captures/diablo2io/2026-06-20_search_probe/ber_sold_search.html`
- Ber + HC fixture: `research/sources/captures/diablo2io/2026-06-20_search_probe/ber_sold_hc_filter.html`
- Jah page 2 fixture: `research/sources/captures/diablo2io/2026-06-20_search_probe/jah_sold_page2.html`
- Source URL used (Jah): `https://diablo2.io/search.php?keywords=Jah&terms=all&author=&fid%5B%5D=16&sc=0&sf=titleonly&sr=topics&sk=t&sd=d&st=0&ch=300&t=0&submit=Search&activesold=1&uitemid=43`

The Sold search exposes WTB/WTS SOLD rows with:
- WTS/WTB trade direction
- SOLD status
- Target item and quantity
- Seller
- Buyer (when available)
- Relative sold time
- Accepted consideration after "for"

### Active Listing Surface (`browsetrades.php`)

- 324KB capture shows 23 WTS, 20 WTB, 27 SOLD mentions
- Platform detect: 31 PC, 19 Switch, 19 Xbox, 20 PlayStation
- Rich data-param attributes with item-specific filters (ed, eth, fcr, fhr, ias, charm, etc.)
- Segment filters: hc=1/2, activesold=1/2

### Segment Filters Discovered (via `data-param` attributes)

The page HTML embeds rich filter attributes:
- `data-param="ladder=1"` / `data-param="ladder=2"` — Ladder toggle
- `data-param="hc=1"` / `data-param="hc=2"` — Hardcore toggle (confirmed working: hc=1 yields fewer results)
- `data-param="plat_pc=1"` / `data-param="plat_switch=1"` — Platform filter
- `data-param="wtbs=1"` / `data-param="wtbs=2"` — WTB/WTS direction
- `data-param="activesold=1"` / `data-param="activesold=2"` — Sold status
- `data-param="sf=titleonly"` / `data-param="sf=firstpost"` — Search scope
- `data-param="sr=topics"` / `data-param="sr=posts"` — Result type
- `data-param="ed=1"` / `eth=1` / `fcr=1` / `fhr=1` / `ias=1` — Item-specific filters
- Time range filter: `st` param (All, 1 day, 7 days, 2 weeks, 30 days, 90 days, 365 days)

### Pagination

- `&start=50` parameter confirmed working for page navigation
- Page 2 of Jah sold search returns 114KB with `sold_class=3`

### Item Price History (`misc/jah-t43.html`)

- 302KB page with "Prices and Demand" and "On the trade market" sections
- 25 sold_class elements, 34 SOLD text mentions
- Less structured than sold search — serves as supplemental reference

### Classification

- This is **candidate completed-player-trade evidence**, not just price-check or community text.
- `use_in_model` must remain `false` until parser validation is complete.
- Current status in manifest: `parser_prototype_ready`, priority `tier_1`.
- Sold search surface is the primary candidate; active listing surface is secondary (order-book signal).

### Next Action

- Build sold-search parser against Ber fixture.
- Validate completed-trade semantics and segment filter integration.
- Do not merge into canonical pricing until validated.
