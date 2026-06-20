# Browser Automation Discovery Plan — D2R Source Discovery

Generated: 2026-06-20

## Why Camoufox

Camoufox is an anti-detect Firefox fork (~200MB) with drop-in Playwright compatibility via Python API. It is already installed, smoke-tested, and operational in the `playwright_workbench` repo. A VPS deployment also exists.

For D2R source discovery, the primary gap is that many cash/RMT marketplace sites render prices dynamically (React/Vue). Static HTML inspection only works for sites like items7 and partially for PlayerAuctions. Sites like G2G, Odealo, IGGM, and YesGamers require a JS-capable browser to see prices.

Camoufox is preferred over standard Playwright because:
- It provides anti-detection for sites that may block headless browsers (G2G, PlayerAuctions)
- It is already tested and available — no new infrastructure needed
- It supports screenshot + HAR capture for offline analysis
- It can save rendered HTML for post-hoc extraction

## Is Camoufox Appropriate for G2G Discovery?

Yes, with caveats:
- G2G is a cash marketplace — not a trading platform. The risk is low (no login gating for browse).
- G2G's page is 9 KB static — nearly everything is JS-rendered. A browser is required.
- Camoufox's stealth features help avoid Cloudflare/anti-bot blocks.
- Do NOT log in. Browse public listings only.
- Do NOT add items to cart or initiate checkout.
- Do NOT leave the browser running unattended.

## Minimal Setup

Camoufox is already installed in `playwright_workbench/.venv`. The D2R repo does not need its own Camoufox install. Instead, use a runner script that imports from the existing venv:

```bash
# From traderie repo, use the playwright_workbench venv
/Users/buddy/projects/playwright_workbench/.venv/bin/python scripts/capture_g2g_preview.py
```

Or, if a standalone script is preferred, install camoufox into the traderie venv:

```bash
/Users/buddy/projects/traderie/.venv/bin/pip install camoufox
/Users/buddy/projects/traderie/.venv/bin/python -m camoufox fetch
```

Either approach works. Using the existing `playwright_workbench` venv avoids duplicating the ~1.6GB browser binary.

**For now, no Camoufox install in the traderie repo.** Use the shared venv.

## Artifact Format and Output Paths

Each browser capture produces:

```
research/sources/captures/
├── {source_slug}_{timestamp}/
│   ├── page.html              # Rendered HTML after JS execution
│   ├── screenshot.png         # Full-page screenshot
│   ├── network.har            # HAR file (if captured)
│   ├── metadata.json          # Filters, URL, timestamp
│   └── listing_samples.json   # Extracted visible prices/items
```

### metadata.json schema

```json
{
  "source": "g2g",
  "url": "https://www.g2g.com/diablo-2-resurrected/runes",
  "filters": {"segment": "pc_sc_l"},
  "captured_at": "2026-06-20T12:00:00Z",
  "tool": "camoufox",
  "tool_version": "0.4.11",
  "visible_listings_count": 42,
  "has_prices": true,
  "has_segment_filters": true,
  "requires_login": false,
  "notes": ""
}
```

### listing_samples.json schema

```json
[
  {
    "item_name": "Ber Rune",
    "price_usd": 2.85,
    "seller": "SellerName",
    "quantity": 1,
    "segment_hints": ["ladder", "softcore"],
    "listing_url": "https://..."
  }
]
```

## Exact Safe Workflow — Capturing One G2G Filtered Page

This is the maximum scope for a single automated session. Do not exceed.

### Smoke Test (first run)

```
1. Open G2G D2R runes page (public, no login)
2. Wait for JS render
3. Wait for any visible price elements
4. Screenshot
5. Save rendered HTML
6. Extract visible prices from DOM
7. Close browser
8. Report: can you see prices? segment filters? listing details?
```

### Production Capture (if smoke test succeeds)

```
1. Open G2G D2R runes page
2. Wait for render + 5s settle
3. If segment filter dropdown exists:
   a. Read available options (ladder/non-ladder, SC/HC)
   b. Select first filter
   c. Wait for re-render
   d. Screenshot + save HTML
   e. Select next filter
   f. Repeat for up to 4 filter combinations
4. Close browser
5. Save all artifacts to research/sources/captures/g2g_{timestamp}/
```

### What NOT to do

- Do not paginate beyond page 1. One page per filter is enough for discovery.
- Do not click on individual listings (unless a specific item is needed and approved).
- Do not submit forms or login.
- Do not run longer than 5 minutes per session.
- Do not set up recurring/automated capture schedules.
- Do not scrape pricing data for bulk analysis — this is discovery, not collection.

## What Should Remain Manual

- Selecting which source and which filter to capture
- Reviewing captured screenshots and deciding what to capture next
- Approving any capture that goes beyond public browse (login, checkout, account)
- Adding new source URLs to the capture list
- Interpreting whether extracted prices are listing prices or completed sale prices
- Deciding whether a source is worth deeper investigation

## What Should Not Be Automated

- Login-based access to any site
- Multi-page pagination loops
- Cross-site price comparison aggregation
- Scheduled or recurring captures
- Price change monitoring or alerting
- Captures that require bypassing anti-bot measures beyond what Camoufox provides by default

## Camoufox vs Standard Playwright

| Capability | Playwright | Camoufox |
|---|---|---|
| Headless browsing | Yes | Yes |
| JS rendering | Yes | Yes |
| Stealth (no webdriver flag) | Partial | Built-in (C++ level) |
| Fingerprint rotation | No | Yes (BrowserForge) |
| Screenshot capture | Yes | Yes |
| HAR capture | Yes (via CDP) | Yes (via Juggler) |
| Memory footprint | 800MB+ Chrome | ~200MB Firefox |
| Already installed | No (needs install) | Yes (playwright_workbench) |
| Anti-bot detection risk | Higher | Lower |

**Verdict:** Camoufox is preferred. The overhead is lower (shared venv), the stealth is better for sites that may block headless Chrome, and the existing smoke test confirms it works. Standard Playwright (with Chromium) would be a reasonable fallback if Camoufox has compatibility issues with a specific site.

## Recommended First Smoke Test

### Target

G2G D2R runes page:
https://www.g2g.com/diablo-2-resurrected/runes-ist-rune-jah-rune-ber-rune-listing

### Questions to Answer

1. Do prices render in the static HTML after JS execution?
2. Are segment filters (ladder, SC/HC) visible and functional?
3. Are prices clearly listing prices (asking) or completed sale prices?
4. Is there any structured data in the DOM (data attributes, JSON in scripts)?
5. Is the page usable without login?
6. Does Camoufox trigger any anti-bot challenge?

### Pass/Fail Criteria

**Pass:** Prices are visible. Segment filters are present. We can extract a few sample USD prices.
**Partial pass:** Prices visible but no segment filters. Good enough for a single "cash market" entry.
**Fail:** Anti-bot challenge blocks the page. Prices are loaded via XHR after user interaction. Page requires login.

### Script Location

`/Users/buddy/projects/traderie/scripts/capture_g2g_preview.py`
(or `/Users/buddy/projects/playwright_workbench/scripts/capture_g2g_preview.py` using the existing venv)

### Expected Output

```
research/sources/captures/g2g_20260620_120000/
├── page.html
├── screenshot.png
├── metadata.json
└── listing_samples.json (if prices extracted)
```

## Subsequent Candidates (after G2G)

| Site | Priority | Why Camoufox |
|---|---|---|
| G2G | 1 | Fully dynamic, 9 KB static shell, needs JS |
| Odealo | 2 | React app, excellent segment UI, dynamic prices |
| YesGamers | 3 | 884 KB but JS-rendered prices, interactive filter UI |
| IGGM | 4 | Dynamic prices, good segment descriptions |
| PlayerAuctions | 5 | Has some static data, but API endpoints could be tested |
| Chicks Gold | 6 | Small dynamic site, low priority |

## References

- Camoufox study: `/Users/buddy/projects/browser_llm/docs/research/camoufox_study.md`
- Camoufox research: `/Users/buddy/projects/playwright_workbench/docs/research/camoufox.md`
- VPS guide: `/Users/buddy/projects/ih_market_companion/_internal/vps_helper/docs/camoufox_vps_guide.md`
- Camoufox Python API: https://github.com/daijro/camoufox
- Current source docs: `research/sources/`, `docs/SOURCE_DISCOVERY.md`
