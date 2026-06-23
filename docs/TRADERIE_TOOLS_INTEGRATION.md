# Traderie Tools Userscript Integration

## Current Userscript Structure

The userscript lives at `github.com/wguDataNinja/TraderieTools/traderie-tools.user.js`. It is a single-file Tampermonkey script with four modules:

| Module | Lines | Purpose |
|---|---|---|
| Adblocker | ~120 | CSS injection + MutationObserver for ad containers |
| Rune Pricing | ~130 | Fetch JSON, parse listing DOM, show value tooltips |
| UI Panel | ~120 | Draggable panel with Bookmarks/Options tabs |
| Bookmarks | ~80 | Save/name/manage listings and searches |

## Current Data Consumption

The userscript fetches a single JSON file via `GM_xmlhttpRequest`:

```javascript
const PRICE_URL = 'https://raw.githubusercontent.com/wguDataNinja/TraderieTools/main/rune_prices.json';
```

### Current JSON Format (produced by previous manual pipeline)

```json
{
  "pc_sc_nl": {
    "Ber Rune": { "ist_value": 7.59, "low_confidence": true },
    "Jah Rune": { "ist_value": 10.3814, "low_confidence": false }
  },
  "pc_sc_l": { ... },
  "pc_hc_nl": { ... },
  "pc_hc_l": { ... }
}
```

### Current JSON → DOM Flow

1. `fetchRunePrices()` loads the JSON via `GM_xmlhttpRequest`
2. `injectAll(prices)` iterates all listing anchors on the current Traderie page
3. `getServerSlug()` reads page URL params to determine current segment (`pc_sc_nl`, etc.)
4. `parseRune(el)` extracts offered item name + quantity from listing anchor text
5. `parseAskGroups(container)` extracts requested items from price lines
6. `injectPercentAndTooltip()` computes value difference and injects a percentage span + hover tooltip

### Current Segment Detection

```javascript
function getServerSlug() {
  const p = new URLSearchParams(window.location.search);
  const plat = (p.get('prop_Platform') || 'pc').toLowerCase();
  const mode = p.get('prop_Mode') === 'hardcore' ? 'hc' : 'sc';
  const lad = p.get('prop_Ladder') === 'true' ? 'l' : 'nl';
  return `${plat}_${mode}_${lad}`;
}
```

This reads the filters from the Traderie page URL. If no filters are set, it defaults to `pc_sc_nl`.

### Current Price Matching

Item names in the JSON are matched against listing text using `parseRune(el)` which extracts `{quantity, item}` from anchor text matching `/(\d+)\s*[xX]\s*(.+)/`. The item name must match keys in the JSON exactly (e.g. `"Ber Rune"` matches `"Ber Rune"` in listing text).

## Proposed Public JSON Schema for Userscript v1

The current JSON format is already close to what's needed. The proposed upgrade adds schema versioning, metadata, and a confidence model:

```json
{
  "schema_version": "0.1",
  "product": "in_game_rune_values",
  "generated_at": "2026-06-20T12:00:00Z",
  "model": "ist_normalized_vwap_v1",
  "segments": {
    "pc_sc_nl": {
      "segment": "pc_sc_nl",
      "platform": "pc",
      "mode": "softcore",
      "ladder": false,
      "runes": {
        "Ber Rune": {
          "ist_value": 7.59,
          "confidence": "low",
          "total_trades": 15
        }
      }
    }
  },
  "caveats": [
    "Prices are Ist-normalized VWAP from Traderie completed trades.",
    "Confidence: high=100+ trades, medium=20-99, low=5-19, very_low=1-4.",
    "Prices are in-game trade values, not cash prices.",
    "AND trades and non-Ist pairs are not included in this model."
  ]
}
```

### Changes from Current Format

| Change | Current | Proposed |
|---|---|---|
| Schema versioning | None | `schema_version: "0.1"` |
| Generation timestamp | None | `generated_at` field |
| Model label | Implicit | `model` field |
| Segment metadata | Slug only | `segment`, `platform`, `mode`, `ladder` fields |
| Confidence | Boolean `low_confidence` | String `confidence` with 4 levels |
| Trade count | Not included | `total_trades` for transparency |
| Caveats | None | `caveats` array |

### Backward Compatibility

The userscript currently expects `{ "pc_sc_nl": { "Ber Rune": { "ist_value": ..., "low_confidence": ... } } }` at the top level. The proposed format nests segments under a `segments` key. A compatibility shim can be added to the userscript:

```javascript
const data = (json.segments) ? json : { segments: json };
```

Or the pipeline can emit both formats for a transition period.

## How Users Should Select Segment

The userscript already handles this correctly via `getServerSlug()`. No user action is required — the segment is detected from the page URL. If the user is browsing `prop_Mode=hardcore&prop_Ladder=true`, the userscript automatically loads `pc_hc_l` prices.

**No segment selector UI is needed in the userscript.** The page URL is the authoritative segment identifier.

## Cache/Update Strategy

| Strategy | Recommendation |
|---|---|
| Fetch frequency | On each page load (Tampermonkey default) |
| Cache duration | Browser cache via `Cache-Control` headers on the raw GitHub URL |
| Stale fallback | Keep last known prices in `localStorage` |
| Update trigger | New commit to the main branch deploys to the raw GitHub URL |

### Proposed localStorage Cache

```javascript
const CACHE_KEY = 'traderie-rune-prices-cache';
const CACHE_TTL_MS = 3600000; // 1 hour

function getCachedPrices() {
  const cached = localStorage.getItem(CACHE_KEY);
  if (!cached) return null;
  const { prices, timestamp } = JSON.parse(cached);
  if (Date.now() - timestamp > CACHE_TTL_MS) return null;
  return prices;
}

function setCachedPrices(prices) {
  localStorage.setItem(CACHE_KEY, JSON.stringify({ prices, timestamp: Date.now() }));
}
```

## Fallback When JSON Fails

| Scenario | Fallback |
|---|---|
| Network error | Use cached prices from localStorage |
| Parse error | Disable pricing module, show "pricing unavailable" in panel |
| GitHub raw URL down | Use cached prices, retry on next page load |
| Empty/partial data | Show available runes, skip unavailable ones |
| Corrupted cache | Clear cache, retry fetch |

Currently, the userscript silently fails if `fetchRunePrices` errors. The fallback should at minimum log to console and disable the pricing toggle with a notification.

## Relationship to D2R Market Helper Website

| Component | Data Source | Update Cadence |
|---|---|---|
| Userscript (v1) | `in_game_rune_values.json` on raw GitHub | Per-commit |
| Website dashboard | Same JSON via API/GitHub | Per-commit |
| External cash comparison | `external_cash_prices.sample.json` | Manual (offline) |
| Source directory | `source_manifest.json` | Manual updates |

The userscript and website should consume the **same** `in_game_rune_values.json` to ensure consistency. The website can also display the cash-comparison data that the userscript does not show.

## Migration Plan

1. **Current**: Manual `rune_prices.json` pushed to GitHub. Userscript fetches it directly.
2. **Short-term**: Add `scripts/generate_prices_json.py` to produce schema-versioned output. Update userscript with compatibility shim. Add localStorage cache.
3. **Medium-term**: Automate generation via GitHub Action or cron. Add trade count and confidence levels to output. Version the schema.
4. **Long-term**: Publish via a simple API endpoint (GitHub Pages or similar) instead of raw GitHub URLs. Allow the website and userscript to share the same endpoint.

## What Remains Unchanged

- The userscript's DOM parsing logic (`parseRune`, `parseAskGroups`) does not need to change.
- The segment detection logic (`getServerSlug`) does not need to change.
- The tooltip display logic does not need to change.
- The UI panel, adblocker, and bookmark modules are independent of the pricing data format.
