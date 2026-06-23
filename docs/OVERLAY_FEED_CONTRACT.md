# Traderie Overlay Feed Contract

## Purpose

This document defines the contract between the D2R Market Helper data pipeline and the external Traderie Tools Tampermonkey userscript (`github.com/wguDataNinja/TraderieTools/traderie-tools.user.js`). It describes which data feeds are produced, what shape they take, which sources are allowed, and how the overlay should consume them.

---

## Source Policy

### Allowed sources (in-game trade evaluation only)

| Source | Role |
|---|---|
| Traderie completed trades (API) | Sole canonical source for in-game Ist-normalized rune prices |

### Forbidden sources (must never appear in overlay)

| Source | Reason |
|---|---|
| Cash/RMT marketplaces (IGGM, ItemNow, D2Stock, PlayerAuctions, items7, etc.) | Cash asking prices are not completed-trade evidence. Never blend. |
| Diablo2.io | Insufficient completed-trade volume; research-only. |
| Reddit / Discord / community posts | Qualitative only; no structured pricing. |
| External blended values | Any price not derived exclusively from Traderie completed trades. |
| Active Traderie listings | Asking prices are not transaction prices. Only `completed=true` data. |

---

## Supported Feed Products

### Short-term: `rune_prices_legacy.json`

**Path:** `data/products/rune_prices_legacy.json`
**Schema version:** none (flat keys)
**Wrapped under `segments`:** no

```json
{
  "pc_sc_nl": {
    "Ber Rune": {
      "ist_value": 10.2695,
      "low_confidence": false,
      "confidence": "medium",
      "bid_price": 9.439,
      "ask_price": 11.1,
      "total_trades": 49
    }
  }
}
```

The existing userscript at `traderie-tools.user.js` expects this exact shape at the top level. No compatibility shim is needed.

### Medium-term: `traderie_tools_prices.json`

**Path:** `data/products/traderie_tools_prices.json`
**Schema version:** `"0.2"`
**Wrapped under `segments`:** yes

```json
{
  "schema_version": "0.2",
  "generated_at": "2026-06-20T20:45:50Z",
  "last_update": "2026-06-20T20:45:50Z",
  "segments": {
    "pc_sc_nl": {
      "Ber Rune": { ... }
    }
  }
}
```

The userscript needs a 1-line compatibility shim:

```javascript
const prices = json.segments ? json.segments : json;
```

### Long-term: `traderie_tools_prices.json` v0.3 (planned)

Same structure as v0.2 with these additions:

```json
{
  "schema_version": "0.3",
  "source_window_label": "rolling_recent_trades_50_cap",
  "cache_hint_ttl_seconds": 3600,
  "segments": { ... }
}
```

### Not used by overlay

| Product | Reason |
|---|---|
| `in_game_rune_values.json` | Uses short rune keys (`"Ber"` not `"Ber Rune"`) incompatible with `parseRune()`. Do not feed to userscript. |
| `external_cash_prices.sample.json` | Cash prices forbidden in overlay. |
| `source_manifest.json` | Internal source registry. |

---

## Segment Slugs

The userscript detects the segment from the page URL via `getServerSlug()`. Four PC segments are supported:

| Slug | Platform | Mode | Ladder | Hardcore |
|---|---|---|---|---|
| `pc_sc_l` | PC | softcore | true | false |
| `pc_sc_nl` | PC | softcore | false | false |
| `pc_hc_l` | PC | hardcore | true | true |
| `pc_hc_nl` | PC | hardcore | false | true |

**Default when no URL param:** `pc_sc_nl`. The overlay must warn when falling back to the default.

**Non-PC platforms:** Not supported. If an unrecognized slug is detected, the overlay should show "Unavailable" and not attempt to evaluate.

---

## Rune Key Format

All feed products consumed by the overlay use `"Ber Rune"` format (display name with " Rune" suffix). This matches the output of the userscript's `parseRune()` function after stripping child elements from the listing anchor.

33 runes, id 1-33 (El through Zod). See `data/rune_registry.json:names.traderie_tools` for the complete mapping.

---

## Required Fields per Rune

| Field | Type | Used for |
|---|---|---|
| `ist_value` | number or null | Primary trade evaluation delta |
| `confidence` | string | Badge display: `"high"`, `"medium"`, `"low"`, `"unavailable"` |
| `low_confidence` | boolean | Backward-compat badge: `true` if confidence is low or unavailable |
| `bid_price` | number or null | Tooltip range: "Bid X.XX → Ask Y.YY" |
| `ask_price` | number or null | Tooltip range |
| `total_trades` | integer or null | Tooltip context: "Based on N trades" |

All fields are present on every rune entry. `ist_value`, `bid_price`, `ask_price` may be `null` when confidence is `"unavailable"`.

---

## Optional Metadata (feed-level)

| Field | Type | Purpose |
|---|---|---|
| `schema_version` | string | Feed format version for migration detection |
| `generated_at` | string (ISO 8601) | When the product was generated |
| `last_update` | string (ISO 8601) | Most recent source data timestamp |
| `source_window_label` | string | Always `"rolling_recent_trades_50_cap"` for Traderie feed |
| `cache_hint_ttl_seconds` | integer | Suggested cache TTL for the userscript |

---

## Overlay States

The overlay must display one of these eight states for each listing:

| State | Condition | Visual |
|---|---|---|
| **Good for you** | Receiver gains >= +0.5 Ist over blended VWAP | Green text |
| **Fair range** | Delta within +/-0.5 Ist of blended VWAP | Neutral/grey text |
| **Likely overpay** | Payer loses >= -0.5 Ist below blended VWAP | Red text |
| **Low confidence** | Any evaluated rune has confidence "low" or "unavailable" (overlay on any state) | Orange badge |
| **Unavailable** | Rune not found in feed, or `ist_value` is null | Grey "—" |
| **Complex trade — review manually** | Multi-item ask (AND trade, bundle), or ask group structure not safely evaluable | Yellow badge |
| **Segment mismatch** | Detected segment missing from feed data, or default segment used without user filter | Warning in overlay header |
| **Parse failed** | DOM parsing did not extract a recognizable item name | No score shown |

### Rules

- **No score on parse failure.** If `parseRune()` returns null or the item name is unrecognized, show no percentage.
- **No score on unknown/defaulted segment.** If `getServerSlug()` produces a slug not in the feed, or the user has no filter params set, show a segment mismatch warning and do not score.
- **No score on unavailable rune.** If `ist_value` is null, show "Unavailable".
- **Low-confidence caveat.** When either the offered or any requested rune has confidence "low" or "unavailable", overlay the percentage with a low-confidence indicator.
- **Complex AND/bundle before scoring.** If the listing has multiple request items (not separated by "OR"), show "Complex trade — review manually" instead of scoring.
- **Display thresholds only.** The scoring thresholds (+/-0.5 Ist) are display rules. They do not change the canonical pricing model.

---

## Cache and Fallback (for external userscript implementation)

The userscript must implement:

| Mechanism | Detail |
|---|---|
| **In-memory cache** | Keep parsed prices in a variable for the page session |
| **localStorage cache** | 1-hour TTL. Key: `traderie-rune-prices-cache`. Store `{ prices, timestamp }`. |
| **Staleness indicator** | When using cached data, append "(cached)" to the overlay footer |
| **Fetch failure fallback** | On network error or 500, use localStorage cache if available. If no cache exists, disable pricing and show "Pricing temporarily unavailable" in the panel. |
| **Corrupted cache recovery** | If `JSON.parse` fails on cached data, clear the key and retry fetch. |
| **Retry** | On transient failure, retry once after 2s. Do not retry on parse errors (format mismatch). |

---

## Pricing Math (immutable)

The overlay reads `ist_value` from the feed. It does not modify, blend, or recalculate prices. Scoring thresholds (+/-0.5 Ist) are display-level only.

- Do not change VWAP math.
- Do not blend segments.
- Do not compute cross-segment fallbacks.
- Do not incorporate cash prices.
- Do not modify the feed schema shape without versioning it.
