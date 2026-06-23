# Collection Scheduler & Runbook

## Collection Status Script

An inspect-only status script reports operational health from local files:

```bash
# Readable text report
python3 scripts/collection_status.py

# Machine-readable JSON
python3 scripts/collection_status.py --json
```

Reports:
- Traderie history row counts and unique listing IDs per segment
- Latest normalized snapshot age per segment
- Cash source snapshot counts
- Product generation timestamps and schema versions
- Launchd log tail and timeout counts
- Stale lock detection (does not remove)
- Overall status summary

The script is read-only — no network requests, no launchctl, no scrapers.

---

## Source Cadence Summary

| Source | Cadence | Command | Snapshot Integration | Collection Status |
|---|---|---|---|---|---|
| Traderie | 4x daily (05/11/17/23) | `python3 scripts/snapshot_traderie.py` | Complete — uses `snapshot_io` via launchd job | Tier 1 |
| ItemNow | Daily | `python3 scripts/parse_itemnow_api.py` | Complete | Tier 3 |
| D2Stock | Daily | `python3 scripts/parse_d2stock_rss.py` | Not yet (product only) | Tier 2 |
| IGGM | Weekly (Mon) | `python3 scripts/parse_iggm_offline.py` | Not yet (fixture-only) | Tier 2 |
| Diablo2.io | Weekly/Manual | `python3 scripts/parse_diablo2io_sold_search_offline.py --items jah,ber,lo,sur` | Not integrated (research only) | Tier 1 research |
| Items7 | Blocked | `python3 scripts/parse_items7_offline.py` | Not yet (no prices in static HTML) | Tier 3 |

---

## Detailed Source Instructions

### Traderie (completed trades)

**Cadence rationale:** Every 3h. The API exposes a rolling window of at most 50 completed trades per item/segment (see `research/memos/2026-06-20-traderie-pagination-window-audit.md`). For high-volume items (Jah Rune), the window cycles in ~7 hours. A 3h cadence captures most trades before they roll off. Increase to 1h for high-volume runes if rate limits permit; use 6h as the conservative fallback.

**Command:**
```bash
# Primary: snapshot-preserving collector (launchd runs this 4x daily)
python3 scripts/snapshot_traderie.py [--segment pc_sc_nl] [--item "Jah Rune"]

# Legacy: basic fetch without snapshots (kept for backward compat)
python3 scripts/fetch_completed_trades.py
```

**Safety:**
- Item list is bounded: `data/item_ids.json` only (currently ~70 items across Runes, Keys, and selected uniques)
- Per-item delay: 5s between requests
- No pagination beyond the single 50-listing page (confirmed: `nextPage` is a boolean flag, not a cursor)
- Cloudscraper handles Cloudflare challenge
- Timeout: 10s default (softcore), 30s for hardcore segments (`pc_hc_l`, `pc_hc_nl`) — hardcore API responses are slower
- Retry: up to 3 attempts per item with 5s/15s backoff
- Item failure does not abort segment (continues to next item)
- Output: `data/raw/raw_trades_{seg}.json` (4 segment files) + timestamped snapshots + history JSONL

**Output paths:**
- Raw: `data/raw/raw_trades_{pc_sc_l,pc_sc_nl,pc_hc_l,pc_hc_nl}.json`
- Snapshots: `data/snapshots/raw/traderie/<seg>/<ts>/response.json`
- Normalized: `data/snapshots/normalized/traderie/<seg>/<ts>.json`
- History: `data/history/traderie/<seg>/completed_trades_{seg}.jsonl`

**Note:** `scripts/snapshot_traderie.py` is the primary snapshot collector. It calls `snapshot_io.write_raw_snapshot()`, `write_normalized_snapshot()`, and `append_history()` for each item/segment. The launchd job `com.buddy.traderie.snapshot-traderie` runs it 4x daily via `scripts/run_traderie_snapshot_launchd.sh`.

### Generating Products from Retained History

Instead of relying only on current raw intermediates, prices can be generated from the append-only history JSONL:

```bash
# Build extracted CSVs from history (deduped by listing_id)
python3 scripts/build_traderie_dataset_from_history.py --write-research

# Calculate VWAP prices from history-derived CSVs
python3 scripts/calculate_rune_prices.py --input-dir data/research

# Regenerate products
python3 scripts/generate_prices_json.py
```

The history dataset spans farther back than current raw files because it accumulates across snapshot runs. See `docs/PRICING_MODEL.md` for per-segment time windows.

---

### ItemNow (WooCommerce Store API)

**Cadence:** Daily. Cash prices change slowly (days/weeks). A daily poll captures changes without unnecessary load on the public API.

**Command:**
```bash
python3 scripts/parse_itemnow_api.py
```

**Safety:**
- Public WooCommerce Store API — no auth needed
- Single URL: `https://itemnow.com/wp-json/wc/store/v1/products?category=99&per_page=100`
- 30s timeout
- No rate limiting observed
- Fixture fallback: `python3 scripts/parse_itemnow_api.py --offline <fixture.json>`

**Output paths:**
- Raw: `data/snapshots/raw/itemnow/<ts>/response.json`
- Normalized: `data/snapshots/normalized/itemnow/<ts>.json`
- History: `data/history/itemnow/cash_prices.jsonl`
- Product: `data/external/itemnow_cash_prices.json`

---

### D2Stock (RSS feed)

**Cadence:** Daily. RSS feed is static and public. Daily polling captures price changes without load on the server.

**Command:**
```bash
python3 scripts/parse_d2stock_rss.py
```

**Fixture fallback:**
```bash
python3 scripts/parse_d2stock_rss.py --offline
```

**Safety:**
- Public Google Shopping RSS feed at `https://d2stock.com/rss.xml`
- No auth needed
- Single URL fetch, 30s timeout
- 2.2 MB feed with 2,014 items — parses locally
- Cloudflare protects main pages but RSS feed is accessible

**Needed:** Add `snapshot_io` calls (raw, normalized, history) to this parser.

**Output paths (current):**
- Product: `data/external/d2stock_cash_prices.json`

**Output paths (planned):**
- Raw: `data/snapshots/raw/d2stock/<ts>/response.json`
- Normalized: `data/snapshots/normalized/d2stock/<ts>.json`
- History: `data/history/d2stock/cash_prices.jsonl`

---

### IGGM (browser-captured HTML)

**Cadence:** Weekly (Monday). Requires a fresh browser capture fixture to be placed at `research/sources/captures/iggm_*/page.html` before running the parser. The page is a multi-seller listing page; prices change at seller discretion.

**Command:**
```bash
python3 scripts/parse_iggm_offline.py
```

**Fixture placement:**
```bash
# After capturing via Camoufox, point to the capture directory:
python3 scripts/parse_iggm_offline.py --input-dir research/sources/captures/iggm_2026-06-27_runes-focused
```

**Safety:**
- Fixture-only — no live fetch
- Parser reads `page.html` and optional `metadata.json` from the input directory
- Segment metadata in `metadata.json` is optional but recommended
- 33 rune prices extracted via regex

**Needed:** Add `snapshot_io` calls (raw, normalized, history) to this parser.

**Output paths (current):**
- Product: `data/external/iggm_cash_prices.json`

**Output paths (planned):**
- Raw: `data/snapshots/raw/iggm/<ts>/response.json`
- Normalized: `data/snapshots/normalized/iggm/<ts>.json`
- History: `data/history/iggm/cash_prices.jsonl`

---

### Diablo2.io (sold-search)

**Cadence:** Weekly or manual. Low-volume source that requires browser-captured fixture HTML. No live fetch.

**Command:**
```bash
# Parse one or more item fixtures:
python3 scripts/parse_diablo2io_sold_search_offline.py --items jah,ber,lo,sur
```

**Fixture placement:** `research/sources/captures/diablo2io/2026-06-20_{slug}_sold_search_p1/rendered.html`

**Safety:**
- Fixture-only offline mode — no network access
- Research-only output (`use_in_model: false`)
- Does not integrate with snapshot history or product pipeline

**Output paths:**
- Research: `data/research/diablo2io_sold_{slug}_trades.sample.json`
- Combined: `data/research/diablo2io_sold_rune_trades.sample.json`

---

### Items7 (static HTML — blocked)

**Status:** No extractable per-rune prices in static HTML. Blocked on browser-capture.

**Command:**
```bash
python3 scripts/parse_items7_offline.py
```

**Output:** Documents the limitation. Zero observations emitted.

---

## Full Pipeline Command Sequence

Run the full collection + pricing pipeline in order:

```bash
# === 1. Traderie completed trades ===
python3 scripts/fetch_completed_trades.py

# === 2. Extract and calculate rune prices ===
python3 scripts/extract_rune_trades.py
python3 scripts/calculate_rune_prices.py

# === 3. Generate in-game prices product ===
python3 scripts/generate_prices_json.py

# === 4. Cash market sources ===
python3 scripts/parse_itemnow_api.py
python3 scripts/parse_d2stock_rss.py
# python3 scripts/parse_iggm_offline.py  # requires fresh fixture

# === 5. Merge external cash prices ===
python3 scripts/generate_external_cash_prices.py

# === 6. Validate ===
python3 scripts/validate_source_manifest.py
python3 scripts/validate_in_game_rune_values.py
python3 scripts/validate_external_cash_prices.py
```

**One-shot alias (once snapshot wrappers are complete):**
```bash
# Daily/3h core loop (no fixture-dependent sources):
python3 scripts/fetch_completed_trades.py && \
python3 scripts/extract_rune_trades.py && \
python3 scripts/calculate_rune_prices.py && \
python3 scripts/generate_prices_json.py && \
python3 scripts/parse_itemnow_api.py && \
python3 scripts/parse_d2stock_rss.py && \
python3 scripts/generate_external_cash_prices.py && \
python3 scripts/validate_source_manifest.py && \
python3 scripts/validate_in_game_rune_values.py && \
python3 scripts/validate_external_cash_prices.py
```

**Weekly add-ons (requires fixtures):**
```bash
python3 scripts/parse_iggm_offline.py
python3 scripts/parse_diablo2io_sold_search_offline.py --items jah,ber,lo,sur
python3 scripts/generate_external_cash_prices.py  # re-run to include IGGM
```

---

## Safety Rules

### Bounded item list
- Traderie: only items in `data/item_ids.json`. No crawling beyond the defined item set.
- Cash sources: source-defined product lists (ItemNow: category 99; D2Stock: RSS feed; IGGM: capture page).
- No auto-discovery of new items. New items are added to `item_ids.json` and `rune_registry.json` manually.

### Backoff on errors
- Traderie: 2 attempts per fetch, delay scales as `RETRY_DELAY * (attempt + 1)` (5s base).
- All HTTP fetches: 30s timeout. Connection errors abort the item/product.
- No infinite retry loops.

### Logs retained
- Traderie: `data/fetch_log.txt` with timestamps.
- Each snapshot timestamp directory serves as its own log record.
- History JSONL provides append-only audit trail.

### Raw snapshots private
- `data/snapshots/raw/` contains full API responses including listing metadata.
- These paths are NOT committed (in `.gitignore` strategy).
- Only product JSONs in `data/products/` are public/shipped.

### Generated public products separate from private history
- Public: `data/products/in_game_rune_values.json`, `data/products/traderie_tools_prices.json`, `data/products/external_cash_prices.sample.json`
- Private: `data/snapshots/raw/`, `data/snapshots/normalized/`, `data/history/`, `data/raw/`
- Never commit raw snapshots or history files.

---

## Deployment Options

### Local cron (Linux/macOS)

```cron
# Traderie — every 3 hours
0 */3 * * * cd /path/to/traderie && python3 scripts/fetch_completed_trades.py >> data/cron_traderie.log 2>&1

# ItemNow + D2Stock — daily at 6am
0 6 * * * cd /path/to/traderie && python3 scripts/parse_itemnow_api.py >> data/cron_cash.log 2>&1
0 6 * * * cd /path/to/traderie && python3 scripts/parse_d2stock_rss.py >> data/cron_cash.log 2>&1

# Full pipeline — daily at 7am (after cash sources)
0 7 * * * cd /path/to/traderie && python3 scripts/extract_rune_trades.py && python3 scripts/calculate_rune_prices.py && python3 scripts/generate_prices_json.py && python3 scripts/generate_external_cash_prices.py >> data/cron_pipeline.log 2>&1

# Validation — daily at 7:30am
30 7 * * * cd /path/to/traderie && python3 scripts/validate_source_manifest.py && python3 scripts/validate_in_game_rune_values.py && python3 scripts/validate_external_cash_prices.py >> data/cron_validate.log 2>&1

# IGGM — weekly Monday 6am (requires fixture)
0 6 * * 1 cd /path/to/traderie && test -d research/sources/captures/iggm_$(date +\%Y-\%m-\%d)_runes-focused && python3 scripts/parse_iggm_offline.py && python3 scripts/generate_external_cash_prices.py >> data/cron_weekly.log 2>&1
```

### macOS launchd

Create `~/Library/LaunchAgents/com.traderie.collection.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.traderie.collection.traderie</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/traderie/scripts/fetch_completed_trades.py</string>
    </array>
    <key>StartInterval</key>
    <integer>10800</integer>
    <key>WorkingDirectory</key>
    <string>/path/to/traderie</string>
    <key>StandardOutPath</key>
    <string>/path/to/traderie/data/launchd_traderie.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/traderie/data/launchd_traderie_err.log</string>
</dict>
</plist>
```

Load:
```bash
launchctl load ~/Library/LaunchAgents/com.traderie.collection.traderie.plist
```

### GitHub Actions

**Caveats:**
- Cloudflare-protected endpoints (Traderie) may behave differently from automation IPs.
- Cash source public APIs (ItemNow, D2Stock RSS) are safe.
- Secrets (if any) must be stored as GitHub Secrets.
- ToS considerations: Traderie is an unofficial API surface. Do not publish the schedule or rate-limit details publicly.

```yaml
# .github/workflows/collection.yml
name: Collection Pipeline
on:
  schedule:
    - cron: '0 */3 * * *'   # Traderie
    - cron: '0 6 * * *'     # Cash sources + full pipeline
  workflow_dispatch:
jobs:
  traderie:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: python3 scripts/fetch_completed_trades.py
      - run: python3 scripts/extract_rune_trades.py
      - run: python3 scripts/calculate_rune_prices.py
      - run: python3 scripts/generate_prices_json.py
  cash:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: python3 scripts/parse_itemnow_api.py
      - run: python3 scripts/parse_d2stock_rss.py
      - run: python3 scripts/generate_external_cash_prices.py
```
