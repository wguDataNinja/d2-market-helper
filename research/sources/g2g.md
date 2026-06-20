# Source: G2G

## URL

https://www.g2g.com/categories/diablo-2-resurrected-item-for-sale

## Type

Cash/RMT marketplace. Vue.js SPA with server-rendered shell. Prices and listings load dynamically from internal APIs.

## Browser Capture Result (2026-06-20)

See `research/memos/2026-06-20-g2g-browser-capture-review.md` for full findings.

**PASS:** Page rendered successfully with Camoufox. 20 listing samples extracted from 89 candidate elements.

### Rune Prices

Visible in rendered HTML. Listing card structure:

```
Listing card (div with q-card / g-card classes)
├─ Anchor → href="/categories/diablo-2-resurrected-item-for-sale/offer/group?fa=..."
│  └─ Segment path: "PC - LoD - NonLadder - SC > Runes > Runes:6# Ith"
│  └─ Price: "from 0.029 USD"
│  └─ Offers: "7 offers"
```

**Price range observed:** $0.029 (Ith) to ? (higher runes not visible at lowest_price sort). JSON-LD shows lowPrice=$0.000001, highPrice=$600,001, offerCount=33.

**Segment format:** `PC - {Expansion} - {LadderStatus} - {Hardcore} > Runes > Runes:{Slot}# {RuneName}`

| Segment | Meaning |
|---|---|
| PC | Platform (PC, Xbox, PS, Switch) |
| LoD / ROTW | Expansion (Lord of Destruction / Reign of the Warlock) |
| NonLadder / Ladder | Ladder status |
| SC / HC | Softcore / Hardcore |
| Runes:6# Ith | Rune slot number and name |

**Important ambiguity:** The downloaded URL filters for D2R items (title says "D2R Items"), but listings show "LoD" (Lord of Destruction — the original expansion). G2G may:
1. Bundle classic D2 and D2R items under the same category
2. Use "LoD" as a generic label for the base game
3. Have a separate "ROTW" filter for D2R-specific items

This needs investigation — a different filter URL may show ROTW-exclusive listings.

### API Endpoints Observed

**Preloaded JSON endpoints** (found in page source `<link rel="preload">`):
- `https://assets.g2g.com/offer/categories.json`
- `https://assets.g2g.com/offer/keyword.json`
- `https://assets.g2g.com/offer/navigation.json`

**Internal subdomain:**
- `https://sls.g2g.com` — likely the primary API backend

**Existing research (from prior static HTML inspection):**
- `https://identitytoolkit.googleapis.com` — Firebase auth
- Google Fonts, Translate, reCAPTCHA

### Listing URL Pattern

Each listing group links to:
`/categories/diablo-2-resurrected-item-for-sale/offer/group?fa={filter_params}&sort=lowest_price`

The `fa` parameter encodes the filter chain (category, subcategory, item). Example:
`7075ff24:2c21e727|7071deb3:4d2c8b55|ec59a3aa:b927e0c8`

### Segmentation

- Server/region dropdown (US shown in capture)
- Item Type dropdown (Runes selected)
- Individual listing segments embedded in titles: `PC - LoD - NonLadder - SC`
- The `fa` URL filter parameter controls category/subcategory/item selection
- No explicit ladder/SC/HC toggle visible — these are embedded in the item title/listing card

### Static vs Dynamic

Dynamic (Vue.js SPA). Listings render client-side. Camoufox or another JS-capable browser is required.

## Assessment

**Suitable for:** Manual/browser capture → offline parser from saved HTML.

G2G renders all listing data in the DOM after hydration. The segment info, prices, and offer counts are extractable from captured HTML. Internal API endpoints are available but would require study (the SPA uses Firebase auth and internal APIs).

**Not suitable for:** Direct static HTTP download (the 9 KB static page shell contains no listing data).

## Recommended Next Capture

A filtered URL for ROTW (D2R expansion) runes only, to determine whether the "LoD" label is a G2G naming convention or actual classic D2 content. Try adding a filter parameter for the D2R expansion or searching specifically for "rotw" runes.
