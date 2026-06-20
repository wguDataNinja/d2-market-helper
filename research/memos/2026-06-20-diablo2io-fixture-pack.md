# diablo2.io Fixture Pack — Sold Search Validation

## Summary

Created a minimum fixture pack for diablo2.io sold-search capture using Playwright Chromium (Camoufox Firefox crashed on diablo2.io page-level JS errors). All 4 page-1 captures succeeded. No pagination exists on any page (all show "Page 1 of 1").

## Fixture Paths

| Fixture | Item | Path |
|---|---|---|
| ✓ | Jah p1 | `research/sources/captures/diablo2io/2026-06-20_jah_sold_search_p1/` |
| ✓ | Ber p1 | `research/sources/captures/diablo2io/2026-06-20_ber_sold_search_p1/` |
| ✓ | Lo p1 | `research/sources/captures/diablo2io/2026-06-20_lo_sold_search_p1/` |
| ✓ | Sur p1 | `research/sources/captures/diablo2io/2026-06-20_sur_sold_search_p1/` |

Each contains: `rendered.html`, `screenshot.png`, `metadata.json`

## Source URLs

| Item | URL |
|---|---|
| Jah | `https://diablo2.io/search.php?keywords=Jah&fid[]=16&sf=titleonly&sr=topics&sk=t&sd=d&st=0&ch=300&submit=Search&activesold=1&uitemid=43` |
| Ber | `https://diablo2.io/search.php?keywords=Ber&fid[]=16&sf=titleonly&sr=topics&sk=t&sd=d&st=0&ch=300&submit=Search&activesold=1&uitemid=45` |
| Lo | `https://diablo2.io/search.php?keywords=Lo&fid[]=16&sf=titleonly&sr=topics&sk=t&sd=d&st=0&ch=300&submit=Search&activesold=1&uitemid=48` |
| Sur | `https://diablo2.io/search.php?keywords=Sur&fid[]=16&sf=titleonly&sr=topics&sk=t&sd=d&st=0&ch=300&submit=Search&activesold=1&uitemid=47` |

Note: `fid[]=16` filters to the "Market" forum. `activesold=1` filters to sold trades.

## Row Counts

| Item | Match Count | Visible Trade Est. |
|---|---|---|
| Jah | 7 | 36 DOM elements |
| Ber | 2 | 21 DOM elements |
| Lo | 3 | 24 DOM elements |
| Sur | 2 | 21 DOM elements |
| **Total** | **14** | **102** |

Note: "Visible trade" count includes DOM elements (filter panels, sidebar widgets, etc.) beyond actual trade rows. Actual trade count = match count (7 for Jah, 2-3 for others).

## Captured vs Failed

All 4 page-1 captures succeeded. No page 2 existed for any item.

Failed captures: None with Chromium. Initial Camoufox (Firefox-based) attempts crashed with `TypeError: Cannot read properties of undefined (reading 'url')` — a Playwright internal error triggered by unhandled JS errors on diablo2.io. Switched to Playwright Chromium with JS error suppression (`add_init_script`), which resolved the issue.

## Segment Filter Evidence

The diablo2.io search page exposes the following filter segments (all visible in captured HTML):

| Segment | Values |
|---|---|
| **Game Version** | `Resurrected`, `RotW` (Reign of the Warlock) |
| **Trade Type** | `WTS` (Want to Sell), `WTB` (Want to Buy) |
| **Listing Status** | `Active`, `Sold`, `Online` |
| **Game Mode** | `Non-ladder`, `Ladder` |
| **Difficulty** | `Softcore`, `Hardcore` |
| **Platform** | `PC`, `Switch`, `Playstation`, `Xbox` |
| **Expansion** | `Expansion`, `Non-Expansion` |
| **Region** | `NA`, `EU`, `AS` (visible in trade listings, not as a top-level filter button) |

Each trade listing includes per-trade metadata:
- Version icon (RotW vs Resurrected)
- Non-Ladder / Ladder tag
- Platform icon (PC, etc.)
- Seller and buyer names
- Timestamp (relative + absolute)
- Items exchanged (e.g., "for 1 Sur 1 Lo")
- "Sold X hours/days ago" with user links

## Pagination Behavior

All 4 searches show `<!-- • Page <strong>1</strong> of <strong>1</strong> -->`. No pagination exists for these low-volume items. The `&start=50` parameter was not tested since no page 2 exists.

The diablo2.io search appears to cap results at ~300 (`ch=300` in URL). For lower-volume high runes, all results fit on one page.

## Capture Method Note

Used Playwright Chromium directly (not Camoufox). The capture script is at `scripts/capture_diablo2io_fixtures.py`. Key departure from the standard workflow:
- Playwright Chromium with JS error suppression, not Camoufox Firefox
- Saves `rendered.html` (not `page.html`)

## Manual Captures Still Needed

- No manual captures needed for these 4 items (all page 1 captured automatically).
- Additional items that could be captured in the future: Ohm, Vex, Gul, Ist, Cham, Zod
- These would follow the same URL pattern with adjusted `uitemid` and `keywords` parameters.
