# G2G Browser Capture Review — First Smoke Test

Generated: 2026-06-20
Tool: Camoufox (headless, from `playwright_workbench/.venv`)
Target: G2G D2R runes category, sorted lowest price
Artifacts: `research/sources/captures/g2g_2026-06-20_lowest-price-runes/`

## 1. Did the page render?

**Yes.** Camoufox loaded the G2G Vue.js SPA successfully. No Cloudflare challenge, no login wall, no bot detection. The page rendered listing cards with segment paths, prices, and offer counts.

## 2. Were rune prices visible?

**Yes.** Listing cards showed per-rune prices:
- Ith Rune: from $0.029 USD (7 offers)
- Ko Rune: from $0.03 USD (7 offers)
- Lum Rune: from $0.035 USD (7 offers)
- Hel Rune: from $0.039 USD (8 offers)
- Eld Rune: from $0.04 USD (7 offers)
- Io Rune: from $0.048 USD (7 offers)
- Dol Rune: from $0.049 USD (7 offers)

These are "from" prices (lowest offer for that item). The JSON-LD reports lowPrice=$0.000001, highPrice=$600,001, offerCount=33 — covering the full rune range.

Only low runes appeared because the sort was `lowest_price`. Higher runes (Ist, Jah, Ber) would be further down the page.

## 3. Were segment filters visible?

**Partially.** The page had filter dropdowns for Server/Region and Item Type. Segment info (PC/LoD/NonLadder/SC) was embedded in each listing card's title text rather than a filter toggle. There was no explicit ladder/SC/HC toggle in the visible UI — those dimensions are captured in the listing path:

```
PC - LoD - NonLadder - SC > Runes > Runes:6# Ith
```

The `fa` URL parameter controls the item subcategory within the category. The existing filter already selected "Runes" from the item type dropdown.

## 4. Could listings be parsed from rendered HTML?

**Yes, partially.** The capture script used a broad card selector (`[class*='card']`) and found 89 candidate elements. 20 samples were extracted. However, many were navigation elements (Home, Items, Game coins, Boosting, Accounts) — the selector was too broad for production use. A G2G-specific parser would need:

- Target `.g-card` or `[data-v-61390112]` scoped selectors
- Extract segment path from `.text-body1.ellipsis-2-lines span`
- Extract price from text matching "from [0-9.]+ USD"
- Extract offer count from text matching "[0-9]+ offers"
- Parse listing URL from the anchor's `href` attribute

## 5. Were useful API/endpoints observed?

**Yes.** Three preloaded JSON endpoints were visible in the page source:

| Endpoint | Purpose |
|---|---|
| `https://assets.g2g.com/offer/categories.json` | Category/taxonomy tree |
| `https://assets.g2g.com/offer/keyword.json` | Search keyword data |
| `https://assets.g2g.com/offer/navigation.json` | Navigation structure |
| `https://sls.g2g.com` | Primary API backend (inferred) |

These are static JSON files served from a CDN — they are readable without authentication. The main API backend (`sls.g2g.com`) likely serves the actual listing/pricing data through authenticated or internal endpoints.

## 6. Is G2G suitable for...

| Use Case | Suitable? | Notes |
|---|---|---|
| Source directory only | Yes | Complete URL, segment info, and screenshot archived |
| Manual/browser capture | **Yes** | Camoufox rendered it without issues. One page capture is fast (~13s). |
| Offline parser from saved HTML | **Yes** | Listing structure is regular enough for a small parser. |
| Future approved collector | Maybe | Would need to understand the `fa` filter parameter encoding and verify the API endpoints serve pricing data without authentication. |

## 7. What exact next capture should Buddy run?

**Recommended:** G2G D2R ROTW (expansion) runes page — same process, different filter.

The current capture showed "LoD" (Lord of Destruction) in listing titles, which may indicate classic D2 content rather than D2R. G2G has separate listings for ROTW (Reign of the Warlock, the D2R expansion). The correct filter URL needs to be found.

**Suggested approach:** From the G2G runes category page, look for a filter that distinguishes "LoD" from "ROTW" expansion. This may be in the Server/Region dropdown or a hidden filter parameter. Once found, run the same capture script with the new URL.

**Next Buddy action:** Browse G2G → D2R Items → Runes → check for expansion/version filter → copy the updated URL.

## Artifact Summary

| File | Size | Content |
|---|---|---|
| `page.html` | 134 KB | Full rendered HTML after Vue.js hydration |
| `screenshot.png` | 1.3 MB | Full-page screenshot of G2G runes category |
| `metadata.json` | 1 KB | Capture metadata (URL, filters, notes) |
| `listing_samples.json` | 12 KB | 20 extracted listing card samples |
| `network_summary.json` | 2.5 KB | API endpoints observed in page source |
