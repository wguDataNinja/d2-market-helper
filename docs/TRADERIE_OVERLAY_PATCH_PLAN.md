# Traderie Overlay Patch Plan

## Scope

First external patch to `github.com/wguDataNinja/TraderieTools/traderie-tools.user.js`. Conservative changes only — fix critical correctness gaps, add cache, add confidence/segment warnings. Preserve existing adblocker, UI panel, and bookmark modules.

---

## Patch Inventory

### 1. Feed URL / Schema compatibility shim

**Location:** Top of Rune Pricing module, after `const PRICE_URL` (current line 146)

**Changes:**
- Add a compatibility shim that unwraps `segments` key if present:

```javascript
function normalizePrices(json) {
  return json.segments ? json.segments : json;
}
```

Apply in `fetchRunePrices` callback:
```javascript
onload(resp) {
  const raw = JSON.parse(resp.responseText);
  runePrices = normalizePrices(raw);
  setupRuneObserver();
}
```

### 2. Cache (localStorage)

**Location:** New function block after PRICE_URL constant

**Design:**
- `CACHE_KEY = 'traderie-rune-prices-cache'`
- `CACHE_TTL_MS = 3600000` (1 hour)
- `getCachedPrices()` — read + validate TTL
- `setCachedPrices(prices)` — write with timestamp
- In `fetchRunePrices`: check cache first, fetch on miss, write cache on success
- On fetch failure: use cache, show "(cached)" indicator
- On parse error: clear corrupted cache, show "Pricing temporarily unavailable"

### 3. `parseRune()` — bare text fallback

**Current function (line 158-163):**
```javascript
function parseRune(el) {
    const c = el.cloneNode(true);
    Array.from(c.children).forEach(ch => c.removeChild(ch));
    const m = c.textContent.trim().match(/(\d+)\s*[xX]\s*(.+)/);
    return m ? { quantity: +m[1], item: m[2].trim() } : null;
}
```

**Problem:** Returns `null` for anchor text like `"Ber Rune"` (no quantity prefix). Single-quantity listings silently skipped.

**Fix:**
```javascript
function parseRune(el) {
    const c = el.cloneNode(true);
    Array.from(c.children).forEach(ch => c.removeChild(ch));
    const text = c.textContent.trim();
    const m = text.match(/(\d+)\s*[xX]\s*(.+)/);
    if (m) return { quantity: +m[1], item: m[2].trim() };
    return { quantity: 1, item: text };
}
```

### 4. AND/bundle trade detection

**Location:** `injectAll()` or `injectPercentAndTooltip()`

**Current behavior:** `parseAskGroups()` accumulates multi-item groups. `injectPercentAndTooltip()` sums them and shows a percentage. No "Complex" badge.

**Fix:** If `group.items.length > 1`, inject a yellow "Complex — review manually" badge instead of scoring. Use the existing `percent-injected` span pattern but with yellow color and fixed text.

```javascript
if (group.items.length > 1) {
  span.textContent = '(!)';
  span.title = 'Complex trade — review manually';
  span.style.color = '#facc15';
  // No tooltip needed — just the warning
}
```

### 5. Confidence badge

**Location:** `injectPercentAndTooltip()` — after percentage injection

**Current behavior:** No confidence check. All scored listings look identical regardless of data reliability.

**Fix:** Look up both offer and ask rune confidence. If any involved rune has `low_confidence === true`:
- Append an orange badge to the percentage span
- Use `span.style.border` or a small `::after` pseudo-element

```javascript
const lowConf = prices[slug]?.[off.item]?.low_confidence === true ||
                group.items.some(r => prices[slug]?.[r.item]?.low_confidence === true);
if (lowConf) {
  span.style.border = '1px solid orange';
  span.style.color = 'orange';
  span.textContent += '?'; // or use a separate badge element
}
```

### 6. Segment mismatch / default warning

**Location:** `injectAll()` or a new overlay header injection

**Current behavior:** Silently defaults to `pc_sc_nl` when URL has no filter params. No visual feedback.

**Fix:** At the top of `injectAll()`:
- Check if `prop_Platform`, `prop_Mode`, or `prop_Ladder` are absent from URL
- If absent, inject a small warning banner at the top of the listing area
- If the detected segment is not in `prices`, show "Unavailable" for all listings and inject a segment-mismatch banner

### 7. MutationObserver / SPA handling

**Current behavior:** `MutationObserver` on `document.body` with `{ childList: true, subtree: true }`. No popstate handler. No debounce.

**Fix:**
- Add debounce (200ms) to MutationObserver callback
- Add `window.addEventListener('popstate', () => injectAll(runePrices))` for SPA URL navigation
- Consider disconnecting observer when pricing is disabled

### 8. Tooltip enrichment

**Current behavior:** Shows Ist values for offer and ask.

**Fix:** Add `bid_price`/`ask_price` range display and `total_trades` count:

```
Offer: 1 x Ber Rune (12.43 Ist)
Ask: 1 x Jah Rune (17.25 Ist)
Bid 9.44 → Ask 11.10 | 49 trades
```

---

## Parser Architecture (post-patch)

```
fetchRunePrices()
  → check localStorage cache (1h TTL)
  → GM_xmlhttpRequest to PRICE_URL on miss
  → normalizePrices() unwraps segments if needed
  → setCachedPrices() on success
  → setupRuneObserver()

getServerSlug()
  → URLSearchParams → "pc_sc_nl" etc.
  → default check → inject warning banner

injectAll(prices)
  → check segment validity
  → inject segment warning if defaulted/missing
  → walk a.listing-name.selling-listing:not([data-injected])
  → parseRune(el) for offered item
  → parseAskGroups(container) for requested items
  → for each ask group:
      if multi-item → "Complex — review manually" (yellow badge)
      else → injectPercentAndTooltip()

injectPercentAndTooltip(off, group, prices, slug)
  → compute Ist deltas
  → color green/red/neutral
  → check low_confidence → orange badge
  → attach hover tooltip with bid/ask range + trades count
```

---

## Evaluator Architecture (unchanged except AND detection)

- Keep Ist delta-based evaluation from the data feed
- Display thresholds remain display-level only
- Do not change VWAP math
- Do not blend segments
- Do not compute cross-segment fallbacks

---

## Feed Selection

| Phase | Feed file | Userscript change needed | Risk |
|---|---|---|---|
| **Immediate** | Copy `rune_prices_legacy.json` to userscript repo as `rune_prices.json` | None (already compatible) | None |
| **After cache patch** | Switch to `traderie_tools_prices.json` via raw GitHub URL from this repo | Add `normalizePrices()` shim | Low — shim handles both shapes |
| **Long-term** | Same feed from project-deployed URL | Update `PRICE_URL` constant | Medium — URL change requires userscript update |

---

## Rollout Order

| Step | Action | Dependencies |
|---|---|---|
| **1** | Copy `rune_prices_legacy.json` to userscript repo as `rune_prices.json` | Product generation |
| **2** | Patch `parseRune()` — add bare-text fallback | Userscript edit |
| **3** | Add localStorage cache | Userscript edit |
| **4** | Add AND/bundle "Complex" detection | Userscript edit |
| **5** | Add confidence badge | Userscript edit |
| **6** | Add segment warning banner | Userscript edit |
| **7** | Add popstate listener + observer debounce | Userscript edit |
| **8** | Enrich tooltip with bid/ask + trade count | Userscript edit |
| **9** | Switch PRICE_URL to serve from project repo | Deployment setup |
| **10** | Manual browser acceptance (see below) | All patches deployed |

Steps 2-8 can be done in any order. Step 9 is independent and can wait.

---

## Manual Browser Acceptance Checks

| # | Page / situation | What to verify |
|---|---|---|
| 1 | `?prop_Platform=PC&prop_Mode=softcore&prop_Ladder=false&item=Jah+Rune` | Pricing loads, correct segment |
| 2 | `?prop_Platform=PC&prop_Mode=hardcore&prop_Ladder=true&item=Ber+Rune` | Hardcore pricing (or unavailable if thin) |
| 3 | No filters: `traderie.com/d2r` | Segment warning banner shown |
| 4 | Listing with `"Ber Rune"` text (no `1x`) | Parse succeeds, quantity=1 |
| 5 | Listing requesting `"Lo Rune + Ohm Rune"` | Yellow "Complex — review manually" |
| 6 | Listing requesting `"Lo Rune OR Ohm Rune"` | Two percentage spans, one per option |
| 7 | Low-confidence rune (e.g. Hel) | Orange badge on percentage |
| 8 | Unavailable rune (El or Lum) | Grey "—" with no percentage |
| 9 | Unknown item (Shako, Griffon) | No percentage, no tooltip |
| 10 | Network offline → reload | Cached prices shown with "(cached)" |
| 11 | SPA: navigate to different item | Pricing re-injects on re-render |
| 12 | Panel toggle: disable/enable pricing | All injected elements removed/restored |

---

## Functions to Patch in `traderie-tools.user.js`

| Function | Current line | Change |
|---|---|---|
| `PRICE_URL` constant | 146 | (optional) switch to project URL |
| `normalizePrices()` | (new) | Extract from fetch callback |
| `fetchRunePrices()` | 188-198 | Add cache read/write, segment unwrap |
| `getCachedPrices()` | (new) | localStorage read + TTL check |
| `setCachedPrices()` | (new) | localStorage write + timestamp |
| `parseRune()` | 158-163 | Add bare-text fallback |
| `injectPercentAndTooltip()` | 196-217 | Add AND detection, confidence badge, enriched tooltip |
| `injectAll()` | 219-227 | Add segment warning, popstate listener, debounce |
| `setupRuneObserver()` | 230-242 | Add debounce, popstate |
| `buildTooltipText()` | 180-187 | Add bid/ask range + trade count |
| `showTooltip()` | 189-195 | (no change needed) |
| CSS `.percent-injected` | Inline style block | Add orange border variant, yellow badge variant |
| CSS `#rune-tooltip` | Inline style block | (no change needed) |

---

## Files NOT Touched

- Adblocker module (lines ~16-137)
- UI panel HTML/CSS (lines ~280-380)
- Bookmark module (lines ~380-470)
- Drag/resize handlers (lines ~480-530)

These modules are independent of the pricing data format and do not need changes.
