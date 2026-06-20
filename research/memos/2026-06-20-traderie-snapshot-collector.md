# Traderie Snapshot Collector

## Script

`scripts/snapshot_traderie.py` — snapshot-preserving Traderie fetch that writes to the
`snapshot_io` pipeline (raw snapshots, normalized snapshots, JSONL history) while
maintaining backward-compatible `data/raw/raw_trades_{slug}.json` output.

## Behavior

For each (segment, item) combination:

1. **Fetch** `GET /api/diablo2resurrected/listings?completed=true` via cloudscraper
2. **Write raw snapshot** — full API response JSON via `snapshot_io.write_raw_snapshot`
3. **Normalize observations** — extract listing_id, seller, prices, segment metadata
4. **Write normalized snapshot** via `snapshot_io.write_normalized_snapshot`
5. **Append to history JSONL** via `snapshot_io.append_history` (dedup by observation_key)
6. **Append to legacy raw** `data/raw/raw_trades_{slug}.json` for backward compat

## Snapshot Paths

| Type | Path |
|---|---|
| Raw | `data/snapshots/raw/traderie/{segment}/{YYYYMMDD_HHMMSS}/response.json` |
| Normalized | `data/snapshots/normalized/traderie/{segment}/{YYYYMMDD_HHMMSS}.json` |
| History | `data/history/traderie/{segment}/completed_trades_{segment}.jsonl` |

Example paths for a `pc_sc_nl` run:
- Raw: `data/snapshots/raw/traderie/pc_sc_nl/20260620_105949/response.json`
- Norm: `data/snapshots/normalized/traderie/pc_sc_nl/20260620_105949.json`
- Hist: `data/history/traderie/pc_sc_nl/completed_trades_pc_sc_nl.jsonl`

## History Schema

Each line in the JSONL history file is a JSON object containing:

| Field | Source | Description |
|---|---|---|
| `_observation_key` | auto | Composite key: `source_slug::item_name::price_str::captured_at::listing_id` |
| `_content_hash` | auto | SHA-256 of the observation content |
| `_captured_at` | auto | Same as `captured_at` (for indexing) |
| `source_slug` | set | `"traderie/{segment}"` |
| `evidence_class` | fixed | `"traderie_completed_trade"` |
| `captured_at` | run start | ISO 8601 UTC timestamp of the run |
| `source_artifact_path` | auto | Absolute path to the raw snapshot |
| `source_url` | built | Full request URL with query params |
| `item_name` | item_ids.json | e.g. `"Jah Rune"` |
| `item_id` | item_ids.json | Numeric item ID |
| `listing_id` | API | Unique listing identifier |
| `seller` | API | Seller username |
| `seller_rating` | API | Float rating |
| `seller_reviews` | API | Review count |
| `quantity` | API | Amount being traded |
| `updated_at` | API | Last update timestamp |
| `price` | API | List of `{name, quantity, item_id}` dicts |
| `active` | API | Boolean |
| `completed` | API | Always `true` |
| `segment_slug` | config | e.g. `"pc_sc_nl"` |
| `version` | API | Response version string |
| `nextPage` | API | Integer (always `1`, not a real cursor) |
| `platform` | extracted | From API properties |
| `mode` | extracted | From API properties |
| `hardcore` | extracted | Bool |
| `ladder` | extracted | Bool |
| `product_id` | mapped | Set to `listing_id` for snapshot_io key compat |
| `price_usd` | fixed | `null` (in-game trades have no USD price) |

## Dedup Strategy

Uses `snapshot_io.observation_key` which builds a composite key:
`source_slug::item_name::price::captured_at::product_id`

- Within a single run: no duplicates (API returns each listing once).
- Across runs: runs at different `captured_at` times produce different keys, so
  history accumulates as a time series. Same listing captured at `T1` and `T2`
  both appear in history.
- `product_id` is mapped to `listing_id` for uniqueness per listing within a run.
- If `listing_id` is missing, the fallback composite key without it still ensures
  record-level uniqueness.

## Running

### Single item, single segment (test)
```bash
python3 scripts/snapshot_traderie.py --item jah --segment pc_sc_nl
```

### Single item, all segments
```bash
python3 scripts/snapshot_traderie.py --item jah
```

### All items, all segments (full inventory)
```bash
python3 scripts/snapshot_traderie.py
```

### Test mode (first match only)
```bash
python3 scripts/snapshot_traderie.py --single
```

Item matching is case-insensitive and supports partial names (`"jah"` matches `"Jah Rune"`).

## Scheduling

Recommended: run every 1-6 hours via cron or a scheduler.

The Traderie API exposes a rolling window of at most ~50 recent completed trades
(~7 hours for high-volume items like Jah Rune). Polling more frequently than the
churn rate produces redundant captures (same listings, different timestamps),
but the dedup in `append_history` prevents duplicate keys within the same run.

Suggested cron entry (hourly, all items):
```cron
0 * * * * cd /path/to/traderie && /path/to/python scripts/snapshot_traderie.py >> data/fetch_log.txt 2>&1
```

Per-segment staggering is unnecessary — each item/segment combo has a 5s delay
built in (`PER_ITEM_DELAY`). Full inventory (26 runes + 6 gems + 2 misc × 4 segments
= ~136 fetches) takes ~11 minutes.

## Full Inventory Item/Segment Count

| Dimension | Count |
|---|---|
| Items | 34 (26 runes + 6 gems + 2 misc) |
| Segments | 4 (pc_sc_nl, pc_sc_l, pc_hc_nl, pc_hc_l) |
| Total fetches | 136 |
| Est. duration | ~11 min (at 5s/item) |
