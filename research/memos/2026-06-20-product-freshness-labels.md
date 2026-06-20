# Product Freshness Labels

## Context

Each product output needs to communicate when it was generated and what time
window its source data represents. This memo documents the labeling approach.

## Two-Layer Model

Every product carries two timestamp/metadata layers:

1. **Generation timestamp** (`product_generated_at`): When the JSON was written
   to disk. Matches `generated_at` for simplicity.

2. **Source window label** (`source_window_label`): What time window the source
   data covers. This is an epistemic label — it captures what we *know* (and
   don't know) about the source's temporal behavior.

## Label Values

### `current_snapshot`

Used for sources where data comes from one-off captures, browser probes, or
API calls that are not historically indexed. The data is a point-in-time
snapshot. History begins when we started collecting.

**Applied to:** `external_cash_prices.sample.json`

### `unknown_window`

Used when the source provides data but the temporal window is not well
understood. For example, Traderie completed trades — we don't know how far
back the "completed" window extends, whether pagination returns all results,
or whether cursor behavior affects comprehensiveness.

**Applied to:** `in_game_rune_values.json`

### `historical_window` (reserved)

Future use. Applied when a source's time window is empirically characterized
(e.g., "API returns trades from the last 7 days"). Once labeled, the data can
be treated as a proper historical time series.

## Per-Source Caveats

Each product also carries structured caveat strings that explain the window
limitations in plain language:

| Product | Field | Value |
|---|---|---|
| `external_cash_prices` | `caveat_history` | "Project history starts when snapshots began. Prices are current snapshots, not historical time series." |
| `in_game_rune_values` | `caveat_window` | "Traderie completed-trades window behavior is not fully understood. Results may represent a recent window, not full history." |
| `in_game_rune_values` | `caveat_pagination` | "Pagination/cursor behavior not yet fully characterized." |

## Migration Path

1. When Agent Z or future investigation characterizes the Traderie API window,
   update `source_window_label` to `historical_window` and add a
   `caveat_window` explaining the known bounds.
2. When the snapshot pipeline accumulates enough runs, add
   `source_window_label: historical_window` to cash price products and
   document the start date.
3. No changes to pricing logic, blending, or weights are required for any
   freshness label update.

## Files Changed

- `scripts/generate_prices_json.py` — added `product_generated_at`,
  `source_window_label`, `caveat_window`, `caveat_pagination`
- `scripts/generate_external_cash_prices.py` — added `product_generated_at`,
  `source_window_label`, `caveat_history`
- `scripts/validate_in_game_rune_values.py` — accept new fields (optional)
- `scripts/validate_external_cash_prices.py` — accept new fields (optional)
- `docs/DATA_PRODUCTS.md` — added Freshness & History section
- `data/products/in_game_rune_values.json` — regenerated with new fields
- `data/products/external_cash_prices.sample.json` — regenerated with new fields
