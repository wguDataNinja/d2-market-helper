# Traderie Userscript Audit

Date: 2026-06-20
Context: Traderie is confirmed as the canonical completed-trade source. The userscript is the primary in-page consumer of the data feed.

---

## 1. Current Architecture

### Userscript Location
The userscript lives at `github.com/wguDataNinja/TraderieTools/traderie-tools.user.js` — a separate GitHub repo from this project. This repo (`traderie`) produces the data feed it consumes.

### Data Feed
```javascript
// Current fetch URL (in userscript)
const PRICE_URL = 'https://raw.githubusercontent.com/wguDataNinja/TraderieTools/main/rune_prices.json';
```

This repo produces `data/products/traderie_tools_prices.json` which is the same format.

### Current Format Compatibility
The userscript expects the price JSON at the **top level** as per-segment keys:
```json
{
  "pc_sc_nl": { "Ber Rune": { "ist_value": 7.59, "low_confidence": true } },
  "pc_sc_l": { ... }
}
```

This repo currently produces:
```json
{
  "schema_version": "0.1",
  "generated_at": "2026-06-20T11:04:19Z",
  "last_update": "2026-06-20T04:14:51Z",
  "segments": { "pc_sc_l": { ... }, ... }
}
```

**The `segments` wrapper makes the current output incompatible with the userscript.** A compatibility shim needs to be added either in the generator or in the userscript.

### Current Supported Pages
Based on the userscript's DOM parsing, it works on Traderie listing pages where:
- `.listing-name` anchors exist (contain item name + quantity)
- `.price-line` containers exist (contain requested items)
- URL params `prop_Platform`, `prop_Mode`, `prop_Ladder` are present for segment detection

---

## 2. Audit Findings

### Segment Detection
- **Status:** ✅ Correct
- `getServerSlug()` reads URL params `prop_Platform`, `prop_Mode`, `prop_Ladder`
- Defaults to `pc_sc_nl` when no params present
- No change needed

### Item/Rune Parsing
- **Status:** ✅ Correct for single-rune offers
- `parseRune(el)` extracts `{quantity, item}` via regex `/(\d+)\s*[xX]\s*(.+)/`
- Item name must match JSON keys exactly (e.g., `"Ber Rune"`)
- `traderie_tools_prices.json` uses `"Ber Rune"` format — correct

### Listing/Offer Direction Parsing
- **Status:** ⚠️ Partial
- The userscript reads the **offered** item from the listing anchor
- The **requested** items are read from `.price-line` containers via `parseAskGroups`
- Bid (you offer, you want) vs ask (you want, you offer) semantics may be swapped depending on listing context
- No direction indicator in the overlay

### Multi-Rune Prices (Offer Side)
- **Status:** ⚠️ Partial
- `parseRune(el)` can extract quantity from anchors like `"2x Ber Rune"`
- Tooltip currently shows per-unit Ist value, but total value for multi-quantity offers is not always clear

### AND Trades / Bundles
- **Status:** ❌ Not supported
- The userscript only evaluates rune-for-rune trades where the requested item is a single rune
- If a listing requests multiple runes (e.g., "Lo + Ohm"), the current code does not handle this
- The tooltip/injection will be misleading or absent for AND trades

### Low-Confidence / Unavailable Behavior
- **Status:** ⚠️ Minimal
- The current format uses `low_confidence: true/false` boolean
- No distinction between "low", "medium", "high", "unavailable"
- No visual distinction in the overlay when confidence is low
- Unavailable runes simply show no tooltip (silent)

### UI Placement
- **Status:** ✅ Functional
- Percentage span injected next to the listing
- Hover tooltip shows offer/ask Ist values
- Panel is draggable with tabs for bookmarks/options

### Data Feed Loading
- **Status:** ⚠️ Brittle
- `GM_xmlhttpRequest` fetches from raw GitHub URL
- No cache fallback implemented (discussed in integration docs but not confirmed)
- On fetch failure, the module silently disables
- No retry logic

### Failure States
- **Status:** ❌ Silent failures
- Network error → pricing module silently disabled
- Parse error → silent
- Missing segment → no fallback
- Missing rune in JSON → no tooltip but no warning

---

## 3. Evaluation Model Design

The overlay should use these thresholds based on `traderie_tools_prices.json`:

| Label | Threshold | Visual |
|---|---|---|
| **Good deal** | Receiver gains ≥ +0.5 Ist over ask | Green (#4ade80) |
| **Fair range** | Within ±0.5 Ist of blended VWAP | White/grey |
| **Overpay** | Payer loses ≥ -0.5 Ist below bid | Red (#f87171) |
| **Unknown** | Rune not in feed or unavailable | Grey (#6b7280) |
| **Complex** | AND/bundle trade | Yellow (#facc15) with "review manually" |

### Bid/Ask Spread Display
- Show `Bid → Ask` range in tooltip
- Example: "Ber: 12.43 Ist (bid 11.85 → ask 12.99)"

### Segment Mismatch Warning
- If page URL params produce a different segment than expected, warn: "Segment auto-detected as {segment}"
- If no URL params found, show default segment with caveat: "Defaulting to pc_sc_nl — enable Traderie filters for accurate pricing"

### Cash/RMT Exclusion
- Cash prices from `external_cash_prices.sample.json` must NEVER be shown in the overlay
- The overlay is in-game trade evaluation only
- If the user tries to evaluate a listing with real-money prices, show no overlay

---

## 4. Proposed Data Feed Improvements

### Add flat-format output to generator

The generator should emit a second format at the top level (without `segments` wrapper) for backward compatibility:

```json
{
  "pc_sc_nl": {
    "Ber Rune": { "ist_value": 12.43, "low_confidence": false },
    ...
  }
}
```

### Improve confidence model
Replace boolean `low_confidence` with string levels matching `in_game_rune_values.json`:

```json
{
  "Jah Rune": {
    "ist_value": 17.25,
    "confidence": "high",       // "high" | "medium" | "low" | "unavailable"
    "low_confidence": false,    // keep for backward compat
    "bid_price": 16.39,
    "ask_price": 18.12,
    "total_trades": 220
  }
}
```

---

## 5. Recommendations

### Priority 1: Data Feed Compatibility
Emit the flat (legacy) format that the userscript expects. Add as a second output from `generate_prices_json.py`.

### Priority 2: Confidence in Overlay
- Add color-coded confidence badges to tooltips
- Show `total_trades` count in tooltip
- Distinguish "unavailable" from "low confidence"

### Priority 3: AND Trade Warning
- Detect multi-item `.price-line` containers
- Show "Complex trade — review manually" instead of attempting to evaluate

### Priority 4: Segment Caveat
- Show detected segment at the top of the overlay
- If no filter params found, show default fallback notice

### Priority 5: Fallback/Caching
- Implement localStorage cache with 1-hour TTL
- On fetch failure, use cached data and show "(cached)" indicator
- On parse error, show "Pricing temporarily unavailable"

### Not Recommended
- Do NOT add cash prices to the overlay
- Do NOT automate listing interactions
- Do NOT modify account data
- Do NOT change VWAP math

---

## 6. Userscript Changes (to be made in TraderieTools repo)

| Change | File | Effort |
|---|---|---|
| Add compatibility shim for `segments` key | `fetchRunePrices()` | 5 min |
| Add confidence string to tooltip | `injectPercentAndTooltip()` | 10 min |
| Add localStorage cache | New function | 15 min |
| Add AND trade detection/warning | `parseAskGroups()` | 20 min |
| Add segment display in overlay | `injectPercentAndTooltip()` | 10 min |

## 7. Changes in This Repo

| Change | File | Effort |
|---|---|---|
| Emit flat legacy format | `scripts/generate_prices_json.py` | 15 min |
| Add confidence string + bid/ask/trades to feed | `scripts/generate_prices_json.py` | 10 min |
| Update docs/USERSCRIPT.md | New file | 15 min |
