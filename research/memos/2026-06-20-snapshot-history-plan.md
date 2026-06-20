# Snapshot & History Architecture

## Directory Structure

```
data/
  snapshots/
    raw/                        # Immutable raw API/parser responses
      itemnow/
        20260620_102555/
          response.json          ← full WooCommerce API response
      iggm/
        ...
      d2stock/
        ...
    normalized/                 # Timestamped normalized observation snapshots
      itemnow/
        20260620_102555.json     ← normalized observations list
      iggm/
        ...
      d2stock/
        ...
  history/                      # Append-only JSONL per source + dataset
    itemnow/
      cash_prices.jsonl          ← one JSON object per observation per run
    iggm/
      cash_prices.jsonl
    d2stock/
      cash_prices.jsonl
```

## How It Works

Every parser calls three functions from `scripts/lib/snapshot_io.py`:

1. **`write_raw_snapshot(data, source)`** — writes the exact API response (or loaded fixture) to `data/snapshots/raw/<source>/<YYYYMMDD_HHMMSS>/response.json`. Provides an immutable audit trail of what the source actually returned.

2. **`write_normalized_snapshot(observations, source)`** — writes the parsed/normalized observations list to `data/snapshots/normalized/<source>/<YYYYMMDD_HHMMSS>.json`. This is the structured, schema-applied view at a point in time.

3. **`append_history(source, dataset, observations)`** — appends each observation as a JSON line to `data/history/<source>/<dataset>.jsonl`. Each record includes `_observation_key` and `_content_hash` metadata fields for dedup and integrity checks.

## Dedup Strategy

- **`observation_key(obs)`** produces a stable composite key: `source_slug::item_name::price::captured_at::product_id`
- **`load_history_keys()`** reads all existing `_observation_key` values from the JSONL before appending
- Observations whose key already exists in the file are skipped
- The `_content_hash` (SHA256 of the JSON-sorted observation) enables future content-level dedup or change detection
- Within-run dedup happens naturally; cross-run dedup is by design (same data from same timestamp = skipped)

## Adoption for Other Parsers

### IGGM (`scripts/parse_iggm_offline.py`)
- After loading/fetching the HTML page, call `write_raw_snapshot(html_or_parsed_data, "iggm")`
- After building the observations list, call `write_normalized_snapshot(observations, "iggm")`
- Then `append_history("iggm", "cash_prices", observations)`
- Keep existing product output at `data/external/iggm_cash_prices.json`

### D2Stock (`scripts/parse_d2stock_rss.py`)
- After parsing RSS XML, call `write_raw_snapshot(parsed_feed, "d2stock")`
- After normalizing, `write_normalized_snapshot(observations, "d2stock")`
- Then `append_history("d2stock", "cash_prices", observations)`
- Keep existing product output at `data/external/d2stock_cash_prices.json`

### items7 (`scripts/parse_items7_offline.py`)
- Same pattern: raw snapshot of the parsed HTML/structured data
- Normalize, write, append

## Integration with Existing Pipeline

The existing `generate_external_cash_prices.py` merge script is unaffected — it reads `data/external/*_cash_prices.json` as before and produces `data/products/external_cash_prices.sample.json`.

The snapshot/history layer is purely additive. No existing output paths change. No pricing logic is touched. No data blending occurs.

## Migration Path

1. **Per-parser adoption**: Each existing parser (`parse_iggm_offline.py`, `parse_d2stock_rss.py`, `parse_items7_offline.py`) follows the same three-call pattern shown above.
2. **Gradual rollout**: Each parser can be migrated independently. The snapshot_io library is shared, so all parsers get consistent behavior.
3. **No schema changes**: The observation schema is whatever each parser produces. The snapshot/history layer stores it transparently.
4. **Future**: Add `data/history/<source>/<dataset>.jsonl` consumers for trend analysis, diff reports, and anomaly detection.
