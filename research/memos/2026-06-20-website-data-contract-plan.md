# Website Data Contract Plan

Date: 2026-06-20
Status: Draft
Goal: Define the first static data contract between backend JSON products and a static website.

---

## 1. `/` — Market Overview

### Consumes
- `data/products/in_game_rune_values.json`
- `data/products/external_cash_prices.sample.json` (or live variant)
- `data/source_manifest.json`

### 1a. Segment Selector
- **What drives it:** `segments` keys from `in_game_rune_values.json` (currently `pc_sc_l`, `pc_sc_nl`, `pc_hc_l`, `pc_hc_nl`).
- **Display:** Map each slug to human label:
  - `pc_sc_l` → "PC Softcore Ladder"
  - `pc_sc_nl` → "PC Softcore Non-Ladder"
  - `pc_hc_l` → "PC Hardcore Ladder"
  - `pc_hc_nl` → "PC Hardcore Non-Ladder"
- **Default:** `pc_sc_nl` (largest active economy — 1,095 trades, covers high-runner runes).
- **Needed from each segment:** `segment_slug`, `platform`, `mode`, `ladder`, `hardcore`, `total_modeled_trades`.
- **Gap:** No segment-level metadata at the top level of the JSON. Currently embedded per-segment. The contract needs a top-level `segment_list` or the website reads `segments` keys directly.

### 1b. Market Snapshot Cards
- **What drives it:** The 4-6 highest-confidence, highest-value runes in the selected segment from `segments.{slug}.runes`.
- **Fields needed per card:** `rune` name, `value_ist`, `bid_price`, `ask_price`, `bid_count`, `ask_count`, `total_trades`, `confidence`, `confidence_reason`.
- **Sort:** By `total_trades` descending (highest volume first). Cap at N cards.
- **Gaps:** No "top runes" helper in the JSON. Website must sort and slice. No segment-to-segment comparison data — cross-segment diff would need the website to load multiple segments.

### 1c. Cheapest Cash Rune Sites
- **What drives it:** `observations` array from `external_cash_prices.sample.json` (or live `external_cash_prices.json`).
- **Display fields:** `source_slug`, `item_name`, `unit_price`, `currency`, `source_url`.
- **Caveat label:** "Cash listing prices — not in-game trade values. Asking prices, not completed sales."
- **Gap:** Cash prices file currently only has one segment (PC SC NL ROTW via IGGM). Filtering by active segment requires matching item_name to rune slugs. No crosswalk between `item_slug` (e.g. `ber_rune`) and `in_game_rune_values` keys (e.g. `Ber`). A mapping or shared item registry is needed.
- **Gap:** `external_cash_prices.sample.json` has no `source_url` per observation, only at source level. Need a URL for "view on source site" links.

### 1d. Source Directory Summary
- **What drives it:** `data/source_manifest.json` (full array of source objects).
- **Display fields:** `display_name`, `status`, `priority`, `evidence_classes`,  `caveats` (first 1-2).
- **Filter:** Only `status` in (`integrated`, `parser_prototype_ready`, `captured_browser`, `captured_static`, `offline_parse_candidate`). Exclude `discovered` and `deferred`.
- **Layout:** Compact card per source. Show badge for `priority`.
- **Gap:** No `last_updated` or `last_generated` on source_manifest — but not needed for this summary view.

---

## 2. `/runes` — Full Rune Dashboard

### Consumes
- `data/products/in_game_rune_values.json`
- `data/products/external_cash_prices.sample.json` (or live variant) — for cash comparison column only
- `data/products/traderie_tools_prices.json` — for traderie tools price comparison

### 2a. Segment Toggle
- Same specs as 1a.
- **Behavior:** Switching segment reloads the rune table for that segment. The `in_game_rune_values.json` has all 4 segments in a single file, so no separate fetch needed.
- **Should persist:** Segment choice should survive page navigation within the site (query param `?segment=pc_sc_nl` or `localStorage`).

### 2b. Rune Table
- **What drives it:** `segments.{selected_slug}.runes` from `in_game_rune_values.json`.
- **Required fields per row:**
  | Field | JSON Path | Notes |
  |---|---|---|
  | `rune` | `rune` | Rune name |
  | `value_ist` | `value_ist` | The blended VWAP |
  | `bid_price` | `bid_price` | Average buyer offer |
  | `ask_price` | `ask_price` | Average seller offer |
  | `bid_ct` | `bid_count` | Number of bids |
  | `ask_ct` | `ask_count` | Number of asks |
  | `confidence` | `confidence` | high/medium/low/unavailable |
  | `price_spread` | Computed: `ask_price - bid_price` (if both non-null) | Visual spread indicator |
  | `traderie_tools_ist` | From `traderie_tools_prices.json` | Only for comparison |

- **Sort:** Default by `total_trades` descending. User should be able to click column headers to sort.
- **Filter:** Filter by confidence level (high/medium/low/unavailable).
- **Null handling:** `null` values for `bid_price`/`ask_price` render as "—". `null` `value_ist` with `confidence: "unavailable"` renders as "No data".
- **Gap:** Rune ordering — JSON has no canonical rune tier/level ordering. Website needs a separate rune tier list (e.g., `{"El": 1, "Eld": 2, ... "Zod": 33}`). This could be a shared constant or a small JSON in the item registry.

### 2c. Confidence Color Rules
| confidence | CSS class | Badge text |
|---|---|---|
| `high` | `.conf-high` | "High" |
| `medium` | `.conf-medium` | "Medium" |
| `low` | `.conf-low` | "Low" |
| `unavailable` | `.conf-none` | "No data" |

### 2d. Cash Price Comparison Column (Optional / "Beta")
- **What drives it:** Cross-reference `item_name` in `external_cash_prices.sample.json` observations vs the rune table row.
- **Display:** `unit_price` in USD from cheapest matching observation. Show source slug.
- **Caveat label per row:** "Cash listing price — not comparable to in-game value."
- **Gap:** Matching rune names across JSON files — `external_cash_prices` uses `item_slug` like `ber_rune`, `in_game_rune_values` uses `"Ber"`. Need a mapping table.

---

## 3. `/sources` — Source Directory and Trust Labels

### Consumes
- `data/source_manifest.json`

### 3a. Source Cards
- **What drives it:** Full `source_manifest.json` array.
- **Required fields per card:**
  | Field | Type | Notes |
  |---|---|---|
  | `display_name` | string | Card title |
  | `status` | enum | Badge: "Integrated", "Parsed", "Captured", "Static", "Candidate", "Discovered", "Deferred" |
  | `priority` | enum | Badge: `tier_1` / `tier_2` / `tier_3` / `later` |
  | `evidence_classes` | array | Tags: "completed_player_trades", "cash_market_listings", etc. |
  | `caveats` | array | Shown in expandable section |
  | `category` | enum | Section heading: "completed_player_trades", "cash_market", "community_discussion", etc. |
  | `base_url` | string | Link to source |
  | `segment_filters` | object | Which filters the source supports |
  | `next_action` | string | Shown only for non-integrated sources |

- **Grouping:** Group by `category`. Order: `completed_player_trades` first, then `cash_market`, then `forum_reference`, `community_discussion`, `source_directory_only`.
- **Priority badge:** `tier_1` = green, `tier_2` = yellow, `tier_3` = orange, `later` = gray.
- **Status badge:** `integrated` = green check, `parser_prototype_ready` = blue, `captured_browser` / `captured_static` / `offline_parse_candidate` = yellow, `discovered` / `deferred` = gray.

### 3b. Gaps
- No `last_updated` timestamp on individual sources, but not critical for MVP.
- No icon/logo URL for each source — cards will display text-only for now.
- `known_urls` is an array — website should show the first URL as primary, rest as expandable.

---

## 4. `/about-methodology` — Trust & Methodology

### Consumes
- No JSON files directly. Content driven by inline text with references to `data/products/in_game_rune_values.json` metadata fields.
- Optional: source counts from `source_manifest.json`.

### 4a. Required Caveats Display
Caveats are spread across multiple JSON files. The methodology page should aggregate and explain:

- **From `in_game_rune_values.json`:**
  - Model description: `model.description` — "Volume-weighted average price (VWAP) normalized to Ist Rune using completed player-to-player trades from Traderie.com."
  - Excludes list: `model.excludes` (6 items).
  - File-level caveats: `caveats` array (11 items).
  - Per-rune confidence: `confidence_reason` text.
  - Evidence class: `evidence_class` = `completed_player_trades`.

- **From `external_cash_prices.sample.json`:**
  - File-level caveats: `caveats` array (7 items about cash prices being external only).

- **From `source_manifest.json`:**
  - Per-source caveats extractable for "how we rate our sources" section.
  - Evidence class taxonomy from `category` and `evidence_classes` fields.

### 4b. Trust Label System
- **Data type badges:** "Completed Player Trades" / "Cash Market Listing" / "Community Discussion".
- **Confidence labels:** High / Medium / Low / Unavailable (with descriptions of thresholds from DATA_PRODUCTS.md: 100+ / 20-99 / 5-19 / 1-4 / < 1 trades).
- **Source priority:** Tier 1 (integrated into model), Tier 2 (captured, parsing in progress), Tier 3 (exploratory), Later (backlog).

---

## 5. Cross-Cutting Rules

### 5a. No-Source-Blending Display
- **Rule:** `in_game_rune_values.json` data and `external_cash_prices` data must never be blended into a single value. They are displayed in separate columns with different visual treatments.
- **Visual treatment:** Cash prices get a distinct background color (e.g., `#fff3e0` or a subtle orange), a $ prefix, and a caveat tooltip.
- **Nevers:**
  - Never compute a "USD per Ist" column that mixes both sources.
  - Never display cash and in-game values in the same sortable column.
  - Never show cash price as a fallback when in-game data is unavailable.

### 5b. Required Caveat Labels
| Data Display Location | Required Caveat |
|---|---|
| Any in-game rune value table | "Prices are relative in-game trade values (Ist-normalized), not absolute cash values." |
| Any cash price display | "Cash listing prices. Not in-game trade values. Prices are asking prices, not completed sales." |
| Any confidence label | Display confidence_reason on hover or in tooltip. |
| Segment selector | "Each segment is a separate economy. Never merge segments." |

### 5c. Segment Selector Behavior
- **Initial load:** Default to `pc_sc_nl`. Rationale: highest volume (1,095 trades), covers the broadest set of runes, most commonly referenced by players.
- **Persistence:** Store selected segment in URL query param (`?segment=pc_sc_nl`) so links can be shared.
- **Layout:** Compact toggle (radio buttons or segmented control). Show segment slug + trade count: `pc_sc_nl (1,095 trades)`.
- **Disabled segments:** None — all 4 segments have data. But segments with `total_modeled_trades === 0` would show "No data" (currently none, but edge case for future console segments).

### 5d. Confidence Labels Display
- **high:** Green badge. Text: "High". Tooltip: "100+ trades — sufficient volume for stable VWAP."
- **medium:** Yellow badge. Text: "Medium". Tooltip: "20-99 trades — moderate volume."
- **low:** Red/orange badge. Text: "Low". Tooltip: "1-19 trades — thin volume (use with caution)."
- **unavailable:** Gray badge. Text: "No data". Tooltip: "No trades available for this rune in this segment."

### 5e. Traderie Tools Price Display
- `traderie_tools_prices.json` contains a simplified subset with `ist_value` and `low_confidence` boolean.
- Display in a separate "Traderie Tools" column on the /runes page for comparison against the main model prices.
- **Rule:** Do not blend. Always label column header: "Traderie Tools (comparison)" with a caveat that this is an external third-party price tracker, not our model.
- **Mapping:** Keyed by `"{rune_name} Rune"` format (e.g., "Ber Rune") — need name normalization to match `in_game_rune_values` keys ("Ber").

---

## 6. Rune Registry (New)

### Consumes
- `data/rune_registry.json` — canonical 33-rune list with ordering, tier classification, and name crosswalk.

### 6a. What It Provides
The rune registry (`data/rune_registry.json`) is a small JSON array that fills the gaps identified above:

- **Canonical ordering** (id 1-33): Website sorts the rune table by `id` for default display.
- **Tier classification** (`low`/`medium`/`high`): UI can group or color-code runes by tier. Used for segment selector filtering and visual hierarchy.
- **Name crosswalk** (`names` object): Maps rune names across all three price products so the website can join:
  - `in_game_rune_values.json` keys (`short_name` → `"Ber"`)
  - `traderie_tools_prices.json` keys (`"{short_name} Rune"` → `"Ber Rune"`)
  - `external_cash_prices` `item_name` / `item_slug` (`"Ber"` / `"ber_rune"`)
- **UI display text** (`name`): Full display name for table headers and tooltips.

### 6b. How It Feeds the UI

| UI Component | Registry Field Used |
|---|---|
| Rune table sort order | `id` (ascending) |
| Rune name display | `name` |
| Segment selector rune grouping | `tier` |
| Cash price matching | `names.cash` → `item_name`, `names.cash_slug` → `item_slug` |
| Traderie Tools comparison lookup | `names.traderie_tools` |
| In-game value lookup | `names.in_game` |
| Tier badge / color coding | `tier` |

### 6c. Gap Closure
| Original Gap | How Registry Closes It |
|---|---|
| "No rune tier ordering (1-33) in any JSON" | `id` field (1-33) provides ordering; `tier` provides grouping |
| "No item name crosswalk between `in_game_rune_values` and `external_cash_prices`" | `names.in_game`, `names.cash`, `names.cash_slug` fields |
| Traderie Tools name normalization | `names.in_game` vs `names.traderie_tools` (short vs " Rune" suffix) |

---

## Summary of Key Gaps

| Gap | Affects | Priority |
|---|---|---|
| No rune tier ordering (1-33) in any JSON | /runes table default sort | High |
| No item name crosswalk between `in_game_rune_values` (short name) and `external_cash_prices` (slug format) | Cash comparison column | High |
| No `external_cash_prices.json` for segments other than PC SC NL | / (cash sites section limited to one segment) | Medium |
| `external_cash_prices.sample.json` lacks per-observation `source_url` | / (can't link directly to listing) | Medium |
| No segment-level metadata index at top level of `in_game_rune_values.json` | / market overview segment selector | Low (can derive from keys) |
| No `latest_generated_at` on `source_manifest.json` | /sources freshness indicator | Low |
