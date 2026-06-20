# Collection Scheduler Plan

## Cadence Reasoning

### Traderie — Every 3h (Tier 1)

The pagination audit (`2026-06-20-traderie-pagination-window-audit.md`) established that the API's `completed=true` endpoint returns a **rolling window of at most 50 listings** per item/segment. For high-volume items like Jah Rune, this window spans approximately 7 hours. There is no pagination — `nextPage` is a boolean flag, not a cursor.

**Why 3h:**
- At 3h intervals, we capture trades before they roll off for most items
- High-volume items (Jah, Ber) cycle faster — 1h would be ideal but the 5s per-item delay already makes a full 4-segment run take ~25 minutes
- A 3h cadence means ~8 snapshots/day, giving good time-series density
- If rate limits allow, increase high-volume runes to 1h by running a focused subset (e.g., Jah, Ber, Lo, Sur, Ohm, Vex only)

**Why not 6h:** A 6h gap risks missing an entire window cycle for Jah/Ber. If the window is 7h, 6h polling means at most 1 snapshot per window — insufficient for trend detection.

**Bounded risk:** The item list is limited to `data/item_ids.json` (~70 items). Each fetch is a single page with no pagination depth. This is not a crawl — it's a bounded, targeted poll.

### ItemNow — Daily (Tier 3)

Public WooCommerce Store API. Cash prices change at seller discretion, typically on day-to-week timescales. The API returns base prices (minimum variation prices) — per-segment prices require authenticated variation-level access. Daily polling captures changes without unnecessary load on the public endpoint.

### D2Stock — Daily (Tier 2)

Public Google Shopping RSS feed (2.2 MB, 2,014 items). Segment-specific pricing (Softcore Ladder RotW, Softcore Non-Ladder RotW). Prices change at low frequency. Daily polling is sufficient and respects the feed as a public data product.

### IGGM — Weekly (Tier 2)

IGGM requires a browser capture fixture. The IGGM page is a multi-seller listing page; prices change at seller discretion. Weekly cadence captures week-over-week trends. Running on Monday sets a consistent anchor point for weekly comparisons. The parser is fixture-only — no live fetch.

### Diablo2.io — Weekly/Manual (Tier 1 research)

Diablo2.io sold-search requires browser-captured fixture HTML. Volume is low (dozens of trades per item, not hundreds). The output is research-only (`use_in_model: false`). Weekly or manual cadence is appropriate until:
1. The sold-search results are validated against Traderie data
2. A decision is made on whether to integrate into the model
3. A browser-capture automation path is established

### Gated sources (d2jsp, YesGamers, PlayerAuctions) — Deferred

These sources are behind login walls, Cloudflare challenges, or client-side rendering that prevents automation:
- **d2jsp**: Fully gated behind login. Guest view shows only a login wall. Forum Gold (FG) economy is separate from in-game rune values.
- **YesGamers**: Prices require login. Excellent segment filters (ladder, SC/HC, ROTW) but inaccessible without an authenticated session.
- **PlayerAuctions**: Browser-required. Segment filters embedded in data-bind paths but not confirmed as working.
- **eBay**: Fully blocked — curl and Camoufox both fail.

These are not included in the automated collection schedule. Revisit only if login access is approved or the anti-bot posture changes.

### Items7 — Blocked (Tier 3)

Static HTML does not contain per-rune prices. Prices are loaded client-side. No schedule until a browser-capture rendering path is established.

---

## Snapshot Retention Strategy

The snapshot architecture (detailed in `2026-06-20-snapshot-history-plan.md`) has three layers:

1. **Raw snapshots** (`data/snapshots/raw/<source>/<ts>/response.json`):
   - Immutable audit trail of exactly what the source returned
   - Enables replaying the parser against old data
   - Retained indefinitely — storage is small (KB per snapshot)
   - NOT committed (in `.gitignore`)

2. **Normalized snapshots** (`data/snapshots/normalized/<source>/<ts>.json`):
   - Schema-applied observations at a point in time
   - Enables time-series analysis without re-parsing raw data
   - Retained indefinitely — each snapshot is a few KB
   - NOT committed

3. **History JSONL** (`data/history/<source>/<dataset>.jsonl`):
   - Append-only, deduped stream of all observations
   - Each record includes `_observation_key` and `_content_hash` for integrity
   - Cross-run dedup via `observation_key()`: `source_slug::item_name::price::captured_at::product_id`
   - Retained indefinitely — JSONL is the canonical historical record
   - NOT committed

**How depth builds over time:**
- Traderie: After 1 week of 3h polling → ~56 snapshots → ~2,800 raw listing captures (56 × 50) → deduped to the unique trades that appeared in the window
- ItemNow: After 1 month of daily polling → ~30 snapshots → 30 data points per rune price → enough for basic trend analysis
- Historical depth is purely forward-looking — there is no backfill path for Traderie because the API has no pagination

**Storage estimate:**
- Traderie: ~25 KB per segment per snapshot → ~100 KB/run → ~800 KB/day → ~5.6 MB/week
- ItemNow: ~40 KB per snapshot → ~1.2 MB/month
- D2Stock: ~400 KB per snapshot (raw feed) → ~12 MB/month
- Total: ~30 MB/year for all sources — negligible

---

## Product Regeneration Timing

### In-game rune values (`in_game_rune_values.json`, `traderie_tools_prices.json`)

Generated from Traderie data. These are the primary product — freshness matters for users.

**When to regenerate:**
- After EVERY Traderie collection run (every 3h)
- The pipeline is: `fetch_completed_trades.py` → `extract_rune_trades.py` → `calculate_rune_prices.py` → `generate_prices_json.py`
- Running the full chain after each Traderie poll ensures the product is never more than 3h stale

### External cash prices (`external_cash_prices.sample.json`)

Merged from all cash sources (ItemNow, IGGM, D2Stock).

**When to regenerate:**
- After EACH cash source collection (daily for ItemNow/D2Stock, weekly for IGGM)
- Running `generate_external_cash_prices.py` is fast — it just merges already-written files
- There is no harm in calling it multiple times per day — it reads the latest from each source's product file

### Validation

Run after each product regeneration:
- `validate_source_manifest.py` — structural check (daily)
- `validate_in_game_rune_values.py` — schema check after Traderie pipeline
- `validate_external_cash_prices.py` — schema check after cash merge

---

## Gap Analysis: Snapshot Integration Status

| Source | `write_raw_snapshot` | `write_normalized_snapshot` | `append_history` | History dir exists |
|---|---|---|---|---|
| ItemNow | ✅ | ✅ | ✅ | `data/history/itemnow/` |
| Traderie | ❌ Not yet | ❌ Not yet | ❌ Not yet | — |
| D2Stock | ❌ Not yet | ❌ Not yet | ❌ Not yet | — |
| IGGM | ❌ Not yet | ❌ Not yet | ❌ Not yet | — |
| Diablo2.io | ❌ Research only | ❌ Research only | ❌ N/A | — |
| Items7 | ❌ No prices | ❌ No prices | ❌ N/A | — |

**Action items** (per `2026-06-20-snapshot-history-plan.md`):
1. Add `snapshot_io` calls to `parse_iggm_offline.py` — add after HTML load and after observations build
2. Add `snapshot_io` calls to `parse_d2stock_rss.py` — add after feed fetch/parse and after observations build
3. Create `scripts/snapshot_traderie.py` — wrapper around `fetch_completed_trades.py` with snapshot integration
4. All four sources should be snapshotted before the scheduler goes live

---

## Recommended Initial Schedule

```cron
# Traderie poll (every 3 hours, at 0 minutes past the hour)
0 */3 * * *  traderie_pipeline.sh

# Cash sources (daily at 0600)
0 6 * * *    cash_sources.sh

# IGGM (weekly Monday 0600, requires fixture)
0 6 * * 1    iggm_weekly.sh

# Full validation (daily at 0630)
30 6 * * *   validate_all.sh
```

Where `traderie_pipeline.sh` runs: fetch → extract → calculate → generate in-game prices → validate in-game prices.
Where `cash_sources.sh` runs: ItemNow → D2Stock → generate external prices → validate external prices.
