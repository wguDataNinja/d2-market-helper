# Traderie — Retention, Pruning, Archive, and UI-History Decision

**Date:** 2026-07-06
**Run slug:** traderie-retention-pruning-ui-audit
**Scope:** Ecosystem-wide VPS retention rules, Traderie table-level retention, UI history requirements, Mac archive design, pruning workflow, bloat controls, capacity budgets
**Governing principle:** VPS stores recent operational data and compact summaries. Mac holds the complete long-term archive. Storage policy governs UI design, not the reverse.

---

## 1. Executive Conclusion

**Governing ecosystem documents:** `vps/shared-conventions.md` §9 (Backup and Restore) and §10 (Raw Artifact and Export Policy) are the only ivy-control documents with retention rules. They cover pg_dump retention and raw artifact (file) retention only. **No ecosystem-wide PostgreSQL table-level retention rules exist yet.** These must be established for Traderie as the first PG workload.

**What is mandatory versus proposed:** The shared-conventions backup retention (§9: 7 daily + 4 weekly dumps on VPS, 14+7 daily + 4 weekly on Mac) and raw artifact retention (§10: 7-30 days on VPS) are mandatory. Everything else in this report is proposed for Traderie's first PG workload.

**Current growth rate:** ~22,000 rows/day across 4 segments, ~27 MB/day raw JSONL, ~55 MB/day estimated PG (row + indexes). This is the Traderie API production source only — the only mature recurring source.

**Projected growth at current rates (unbounded raw retention):**

| Horizon | Rows (M) | PG size (GB) | PG + indexes (GB) |
|---------|----------|--------------|-------------------|
| 30 days | 1.0 | 1.6 | 3.2 |
| 90 days | 2.4 | 4.8 | 9.6 |
| 180 days | 4.4 | 9.6 | 19.2 |
| 365 days | 8.5 | 19.4 | 38.8 |

These numbers are for **one** recurring source. At 180+ days, PG alone exceeds the VPS CX23 disk (~38 GB total, ~4 GB free after workloads). **Unbounded raw retention is not viable on the VPS.**

**Recommended VPS retention posture:**
- Raw completed trades: **7 days** on VPS (sufficient for the 4x daily snapshot window)
- Per-rune hourly aggregates: 30 days
- Per-rune daily aggregates: 365 days (replaces raw rows for product generation)
- Current product state: indefinite (reproducible from aggregates + raw-to-aggregate parity)
- Health/error records: 90 days
- snapshot_runs metadata: 90 days
- product_builds: 365 days

**Mac archive:** Raw JSONL (source-native, already on Mac), full pg_dump daily snapshots, compact hourly/daily aggregate CSVs. Mac retains everything indefinitely or until a formal archive retirement.

**UI history requirements: NONE.** The current UI is entirely snapshot-based. It reads 5 JSON files at build time and displays a single current-state table per segment. There are no time-series graphs, no charts, no trend lines, no history displays, and no price-history features in the codebase (`web/src/` has zero references to "history", "trend", "chart", "graph", or "series"). The product file's `generated_at` timestamp is the only time-related UI element. **No raw trade rows are required by the current UI.**

---

## 2. Ecosystem-Wide VPS Rules

### Current Rules (from ivy-control shared-conventions.md)

| Rule | Source | Authority | Decided? |
|------|--------|-----------|----------|
| VPS stores bounded recent data; full archives leave the VPS | §10 (Raw Artifact policy) — raw artifacts on VPS at 7-30 days | Active | Yes (file artifacts only) |
| pg_dump retention: 7 daily + 4 weekly on VPS | §9 (Backup and Restore) | Active | Yes |
| pg_dump retention: 14 daily (cutover) / 7 daily (steady) + 4 weekly on Mac | §9 | Active | Yes |
| Backup transport via scp with SHA-256 verification | §9 | Active | Yes |
| Monthly restore drill required | §9 | Active | Yes |
| Raw artifacts on VPS bounded at 7-30 days by re-fetchability | §10 | Active | Yes |
| No cloud backup until destination/budget confirmed | §9 | Active | Yes (deferred) |
| Destructive Operation Gate required before pruning | §11 | Active | Yes |

### Proposed New Rules (for Traderie as first PG workload)

| Rule | Proposed | Needs New Decision? |
|------|----------|---------------------|
| VPS stores current state + bounded recent windows per-data-class | Yes — defined in this report per table | Needs Buddy sign-off |
| Compact aggregates may be retained longer than raw rows | Yes — hourlies 30d, dailies 365d | No — flows from VPS-small principle |
| Raw captures (JSONL, snapshots) are short-lived on VPS | Already in shared-conventions §10 | Already decided |
| Full archives leave the VPS to Mac | Already in shared-conventions §9/§10 | Already decided |
| Every repo has documented retention by table | Traderie first — template for others | Needs Buddy sign-off |
| Pruning must be deterministic, tested, observable | Yes — specified in §8 below | No |
| Pruning never runs where backup is stale | Yes — Destructive Operation Gate from shared-conventions | Already decided |
| Disk growth and prune results in health reporting | Yes — recommended for health.health_runs | Recommended |
| No repository receives unlimited storage by default | Yes — Traderie gets a soft budget (see §10) | Needs Buddy sign-off |

---

## 3. Traderie Table Inventory

### app.snapshot_runs

| Property | Value |
|---|---|
| Purpose | Track each snapshot collection run per segment (4x daily, 4 segments = 16 rows/day) |
| Row granularity | One row per segment per run |
| Current count | 0 (empty, never loaded) |
| Expected rows/day | 16 (4 segments × 4 snapshots) |
| Expected rows/year | ~5,840 |
| Row size | ~256 bytes (UUID + text + timestamptz + int + jsonb) |
| Indexes | segment, timestamp DESC, status |
| FK | app.segments(segment_slug) |
| UI dependency | None |
| Model dependency | Referenced by completed_trades via snapshot_run_id FK |
| Rollback dependency | Yes — pilot rollback deletes by segment_slug |
| Audit dependency | Yes — provenance for which run produced which data |
| Mac archive | Raw JSONL history already records run boundaries |
| **Recommended VPS retention** | **90 days** (~1,440 rows, ~0.4 MB) |

### app.completed_trades (largest table by far)

| Property | Value |
|---|---|
| Purpose | Core deduplicated trade observations from Traderie API |
| Row granularity | One row per deduped observation_key per segment |
| Current count | 0 (empty, never loaded) |
| Expected rows/day | ~22,000 (4 segments, varies by segment) |
| Expected row size | ~1,200 bytes (many text fields, jsonb source_payload) |
| Indexes | 5 (unique on segment_slug+observation_key, listing_id, captured_at DESC, content_hash, ruleset, item_id) |
| FK | app.segments(segment_slug), app.snapshot_runs(snapshot_run_id) |
| UI dependency | **None** — no row-level trade data displayed |
| Model dependency | Primary input to price calculation (VWAP). But model only needs a bounded recent window + raw-to-aggregate parity file |
| Rollback dependency | Yes — pilot deletes by segment_slug + observation_key |
| Audit dependency | Yes — provenance chain back to raw API captures |
| Mac archive | Raw JSONL history file (source-native, already on Mac) |
| **Recommended VPS retention** | **7 days raw** (~154,000 rows, ~185 MB) — sufficient for the 50-cap rolling window. Older rows are for model only, which can use aggregates |

### app.price_entries

| Property | Value |
|---|---|
| Purpose | Normalized individual prices from the prices array in each completed_trade (can be 1-6+ per trade) |
| Row granularity | One row per price item per completed_trade |
| Current count | 0 |
| Expected rows/day | ~40,000-60,000 (1.8-2.7× completed_trades) |
| Row size | ~256 bytes (UUID + FK + text + int + boolean + timestamptz) |
| Indexes | 4 (trade FK, requested_item_id, rune_item_id, trade+add_flag) |
| FK | app.completed_trades(trade_observation_id) ON DELETE CASCADE |
| UI dependency | None — not displayed directly |
| Model dependency | Used for AND-trade decomposition and non-Ist pair analysis |
| Mac archive | Reconstructable from completed_trades JSONL + price extraction script |
| **Recommended VPS retention** | **7 days** (follows completed_trades via CASCADE delete) |

### app.product_builds + app.product_build_log

| Property | Value |
|---|---|
| Purpose | Track each product regeneration run (daily at 06:00) |
| Row granularity | One row per build per segment (4 rows/day) + 0-n log rows |
| Expected rows/year | ~1,460 builds + log entries |
| UI dependency | None directly (UI reads product JSON, not this table) |
| Model dependency | FK target for segment_rune_prices and ruleset_breakdowns |
| **Recommended VPS retention** | **365 days** (small table, needed for price history lineage) |

### app.sources, app.segments, app.rune_registry

| Property | Value |
|---|---|
| Purpose | Reference data — changed only by migration |
| Row count | ~20 sources, 4 segments, 33 runes |
| Growth | None (static reference data) |
| UI dependency | Yes — source_manifest.json is rendered, segments are the core selector |
| **Recommended VPS retention** | Indefinite (current state only, no history needed) |

### app.segment_rune_prices + app.ruleset_breakdowns

| Property | Value |
|---|---|
| Purpose | Per-build computed rune prices by segment (product output in relational form) |
| Row granularity | 23 runes × 4 segments = 92 rows per build |
| Expected rows/year | ~33,580 (92 × 365) |
| UI dependency | Yes — these rows contain the exact data rendered in the UI |
| **Recommended VPS retention** | **365 days** (1 year of daily pricing history, ~33K rows, compact) |

### health.health_runs + health.workflow_status

| Property | Value |
|---|---|
| Purpose | Pipeline health monitoring |
| Row granularity | One health run per workflow per check interval |
| Expected rows/day | ~8 (snapshot, regen, validate, backup, health check) |
| UI dependency | No — monitoring/ops tooling |
| **Recommended VPS retention** | **90 days** (operational diagnostics) |

### health.ingestion_errors

| Property | Value |
|---|---|
| Purpose | Structured fetch error records |
| Expected rows/day | ~0-50 (mostly 0; hardcore segments may have some) |
| **Recommended VPS retention** | **30 days** (errors are informative when recent) |

### app.segment_run_aggregates (proposed new table)

Not yet in migrations. Recommended to add for hourly/daily VWAP rollups — see §6.

---

## 4. UI History Requirements

The existing UI has **zero history requirements.** Inspection of all 4 pages and the data loader:

| Page | What it displays | Is it time-series? | Needs raw trade rows? |
|------|-----------------|--------------------|-----------------------|
| Home (Market Overview) | Segment selector, 8 top runes by volume, modeled trade count, source directory cards | No — current snapshot only | No |
| Runes (Rune Dashboard) | Full rune table with Ist values, bid/ask, trade counts, confidence, cash comparison | No — current snapshot only | No |
| Sources (Source Directory) | Source metadata cards with status, priority, caveats | No — static directory | No |
| Methodology (About) | Methodology explainer | No — static page | No |

The only time-related UI element is the freshness bar:
```
Data generated: 2026-07-06T10:00:11Z · Window: rolling_recent_trades_50_cap
```

**No graph, chart, trend, history, or series component exists anywhere in `web/src/`.**

**Conclusion:** The UI proposed in BACKLOG.md item "Graph model v2" and "Price-history probe" are speculative future features. Per the governing principle, they do not justify indefinite raw-row retention. When such features are proposed, they should be designed around compact aggregate tables, not raw observation scans.

---

## 5. Proposed Retention Tiers

| Tier | Description | VPS | Mac | Examples |
|------|-------------|-----|-----|----------|
| **A** | Current canonical state | Indefinite (current row only) | Indefinite | app.segments, app.sources, app.rune_registry |
| **B** | Recent row-level operational history | 7 days | Indefinite (JSONL archive) | app.completed_trades, app.price_entries |
| **C** | Compact aggregates (hourly, daily) | Hourly: 30d, Daily: 365d | Indefinite (CSV archive) | app.segment_run_aggregates (proposed), app.segment_rune_prices, app.ruleset_breakdowns |
| **D** | Short-lived diagnostics | snapshot_runs: 90d, health_runs: 90d, ingestion_errors: 30d | Indefinite (via pg_dump) | app.snapshot_runs, health.*, app.product_builds: 365d |
| **E** | Mac-only archive | None (transferred then pruned) | Indefinite | Raw JSONL history, raw snapshots, normalized snapshots, pg_dump history |

---

## 6. Snapshot and Aggregate Strategy

**Does every raw Traderie API observation need to remain in PostgreSQL?** No.

The VWAP pricing model needs:
1. **Recent raw rows** (7 days) — sufficient for the rolling 50-cap window. Older raw rows add no new information because the API only returns the most recent 50 trades.
2. **Compact daily aggregates** — the VWAP model can run against pre-computed hourly/daily Ist-pair summaries instead of scanning all raw rows.

### Proposed aggregate table

```sql
CREATE TABLE IF NOT EXISTS app.segment_run_aggregates (
    aggregate_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_slug     text NOT NULL REFERENCES app.segments(segment_slug),
    bucket           timestamptz NOT NULL,  -- truncated to hour or day
    rune_id          integer NOT NULL REFERENCES app.rune_registry(rune_id),
    granularity      text NOT NULL CHECK (granularity IN ('hourly', 'daily')),
    unique_listings  integer NOT NULL DEFAULT 0,
    total_quantity   integer NOT NULL DEFAULT 0,
    ist_pairs_count  integer NOT NULL DEFAULT 0,
    and_trade_count  integer NOT NULL DEFAULT 0,
    bid_vwap         numeric(12,6),
    ask_vwap         numeric(12,6),
    value_ist_vwap   numeric(12,6),
    min_price        numeric(12,6),
    max_price        numeric(12,6),
    median_price     numeric(12,6),
    ruleset_rotw_pct numeric(5,2),
    created_at       timestamptz NOT NULL DEFAULT now(),
    UNIQUE (segment_slug, bucket, rune_id, granularity)
);
```

**26 bytes/row × 23 runes × 4 segments × 24 hours = ~57K rows/day hourly, or 92 rows/day daily.**

Hourly aggregates: retain 30 days (~1.7M rows, manageable).
Daily aggregates: retain 365 days (~33K rows, trivial).

The daily regenerate pipeline would work as:
1. Raw rows arrive → written to `app.completed_trades` (7-day window) + `app.price_entries` (7-day window)
2. Post-snapshot hook: upsert hourly aggregates from new raw rows
3. Daily `calculate_rune_prices.py` equivalent: read last-7-days aggregates + current raw window → VWAP → write `app.segment_rune_prices` → generate product JSON
4. Row-level pruning: DELETE from completed_trades and price_entries where captured_at < now() - 7 days (with archive/prerequisite check)
5. Aggregate pruning: hourly aggregates older than 30 days, daily aggregates older than 365 days

### Product-build snapshots

The existing `app.segment_rune_prices` (one row per rune per segment per build) and `app.ruleset_breakdowns` already serve as versioned product snapshots. Retain 365 days. Current JSON product files (which are the UI's input) are generated from these tables.

---

## 7. Mac Archive Design

### What is archived on the Mac

| Asset | Format | Size | Retention | Prune trigger |
|-------|--------|------|-----------|---------------|
| Raw JSONL history (source-native) | `.jsonl` (already exists on Mac) | ~425 MB today, ~3.7 GB/year | Indefinite | Never (source evidence) |
| pg_dump (full database) | `.dump.gz` + `.sha256` + manifest | ~1-2 GB per dump | 14 daily → 7 daily | Age > 7d (steady state) |
| pg_dump weekly checkpoints | `.dump.gz` + `.sha256` + manifest | ~1-2 GB each | 4 weekly | Age > 4 weeks |
| Hourly aggregate CSVs | `.csv.gz` | ~2 MB/day → ~730 MB/year | Indefinite | Never |
| Daily aggregate CSVs | `.csv.gz` | ~50 KB/day → ~18 MB/year | Indefinite | Never |
| Generated product JSONs | `.json` | ~500 KB each | Git history | Version control |

### Archive directory layout on Mac

```
/Users/buddy/projects/backups/postgres/traderie/
  pg_dump/
    daily/     (7-14 dumps)
    weekly/    (4 dumps)
    immutable/ (pre-migration, cutover baselines)
  source_archive/
    history/   (JSONL files, re-compressed .gz versions)
    aggregates/hourly/
    aggregates/daily/
    products/
  manifests/
    dump_manifest_YYYYMMDD.json
    source_archive_manifest_YYYYMMDD.json
```

### Transfer and verification

- PostgreSQL dumps: `pg_dump` → gzip → scp to Mac → SHA-256 verify → log to manifest
- Aggregate CSVs: generated on Mac post-dump or as part of deployment pipeline
- Source JSONL: already on Mac (current Traderie data directory)
- Restore drill: monthly on Mac dev PostgreSQL — restore dump, verify row counts, max timestamps, key queries

---

## 8. Pruning Workflow

### Safe sequence

1. **Identify eligible rows**: Query `app.completed_trades` WHERE `captured_at < now() - interval '7 days'`. Dry-run only.
2. **Produce dry-run counts**: Print count, oldest/newest timestamp, total bytes affected.
3. **Verify backup prerequisites**: Check `health.workflow_status` for backup_state = 'ok' and age < 24h. Fail if backup is stale.
4. **Prune in bounded batches**: DELETE 10,000 rows at a time within a single transaction per batch. Sleep 100ms between batches to avoid lock buildup.
5. **Preserve referential integrity**: `DELETE FROM app.price_entries WHERE trade_id IN (selected trades)` first, then DELETE from `app.completed_trades`. Use CASCADE for safety but explicitly batch for observability.
6. **ANALYZE**: `ANALYZE app.completed_trades; ANALYZE app.price_entries;` after pruning.
7. **VACUUM**: Only if dead-tuple ratio exceeds 40%. Standard VACUUM (not FULL). This marks space reusable but does not return it to the OS.
8. **Record**: Insert into a prune audit table or log to `health.health_runs`: rows removed, bytes estimated, duration, batch count.
9. **Export health metrics**: Update `health.health_runs` with storage_bytes and storage_growth_bytes_24h.
10. **Alert on failures**: If prune fails or unexpected growth detected (>50% above daily average), record in health run with status='fail'.

### Prune strategy: DELETE, not partition-drop

Table partitioning is not justified at current scale. At ~150K rows/week for completed_trades, DELETE of 7-day-old rows removes ~150K rows/week, which is well within normal PostgreSQL maintenance. Re-evaluate partitioning only if:
- completed_trades exceeds 10M rows
- DELETE/VACUUM cycles fail to keep up
- Autovacuum falls behind

### Failed pruning resume

Each batch is a separate transaction. If pruning fails mid-way, the next run starts from the same eligible-looking query (captured_at < now() - 7 days) and deletes only remaining rows. Idempotent by design.

### Pilot rollback safety

Pilot data is loaded with specific observation_keys. Pruning must use `captured_at` or `ingested_at`, not observation_key ranges. The pilot's small bounded subset (25 records, pc_sc_l) will be pruned along with everything else >7 days. Document the pilot experiment end date so prune can exclude pilot rows until analysis is complete, if needed. Use a `app.prune_exclusions` table if required:

```sql
CREATE TABLE IF NOT EXISTS app.prune_exclusions (
    exclusion_id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name      text NOT NULL,
    key_pattern     text NOT NULL,  -- LIKE pattern for observation_key
    reason          text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    expires_at      timestamptz NOT NULL
);
```

---

## 9. PostgreSQL Bloat Controls

| Concern | Risk | Control |
|---------|------|---------|
| Autovacuum | Low at current scale | Leave at defaults. 150K rows/week DELETE is trivial. |
| Dead tuples | ~150K/week on completed_trades | Standard VACUUM weekly. Not VACUUM FULL. |
| Table size growth | 185 MB/week raw retention, then stable | DELETE keeps size bounded. No unbounded growth. |
| Index bloat | Low (150K deleted rows/week on 5 indexes) | Standard VACUUM handles this. Reindex monthly if index scans degrade. |
| Long-running transactions | Pipeline scripts run <5 minutes | Set `statement_timeout = 300s` per shared-conventions. Log any >60s. |
| WAL growth | Moderate (~2 GB/week) | `max_wal_size = 2GB`, `min_wal_size = 256MB` per existing config. Monitor WAL directory size. |
| Log rotation | PostgreSQL log to Homebrew default | Ensure `log_filename` includes date and `log_rotation_age = 1d` |
| Duplicate prevention | Already handled by `observation_key` unique index | ON CONFLICT DO NOTHING in loader and adapter |
| Partitioning | Not justified | Defer until >10M rows or prune performance degrades |

**Conclusion:** No partitioning, no VACUUM FULL, no special bloat controls needed. Standard autovacuum handles the Traderie workload easily.

---

## 10. Capacity Budgets and Thresholds

| Metric | Soft Warning | Hard Limit | Action |
|--------|-------------|------------|--------|
| Traderie PG database size | 2 GB | 8 GB | Review raw retention (reduce 7d → 3d) or evaluate partitioning |
| Weekly growth rate | >200 MB/week for 3 consecutive weeks | >400 MB/week | Review for unexpected source addition |
| completed_tables row count | >1M rows | >3M rows | Verify prune is running; check captured_at distribution |
| pg_dump backup directory (Mac) | 20 GB | 50 GB | Archive old dumps to cold storage |
| VPS free disk (entire host) | <20% free per shared-conventions | <10% free | Emergency cleanup per ivy-control runbook |
| Prune failure rate | >10% failure | >3 consecutive failures | Alert via health run |

These reconcile with the VPS CX23 constraints: ~38 GB total disk, ~7 GB free before cleanup, ~4 GB free after known workloads. The 8 GB hard limit for Traderie PG ensures it stays within 30% of the VPS's remaining disk, leaving room for other databases and system operations.

---

## 11. Exact Retention Proposal

| Data class / Table | VPS raw retention | VPS aggregate retention | Mac archive | Prune cadence | UI justification |
|---|---|---|---|---|---|
| `app.completed_trades` | 7 days | N/A | JSONL (indefinite) | Daily, batches of 10K | None needed — model only |
| `app.price_entries` | 7 days (CASCADE via completed_trades) | N/A | Reconstructable | Daily, CASCADE | None needed |
| `app.snapshot_runs` | 90 days | N/A | Via pg_dump | Weekly | None |
| `app.segment_run_aggregates` (proposed) | N/A | Hourly: 30d, Daily: 365d | CSV.gz (indefinite) | Daily rollup + prune | Future pricing history graphs |
| `app.segment_rune_prices` | 365 days (always compact) | N/A | Product JSON in git | Never (retain full year) | UI current prices + future trend |
| `app.ruleset_breakdowns` | 365 days | N/A | Product JSON in git | Never (retain full year) | UI metadata |
| `app.product_builds` | 365 days | N/A | Via pg_dump | Yearly cleanup | Build lineage |
| `app.sources` | Indefinite (current only) | N/A | Git | Never | UI |
| `app.segments` | Indefinite (4 rows) | N/A | Git | Never | UI/code |
| `app.rune_registry` | Indefinite (33 rows) | N/A | Git | Never | UI |
| `health.health_runs` | 90 days | N/A | Via pg_dump | Weekly | Ops |
| `health.workflow_status` | Indefinite (last state only) | N/A | Via pg_dump | Never (UPSERT) | Ops |
| health.ingestion_errors | 30 days | N/A | Via pg_dump | Weekly | Ops |
| app.prune_exclusions (proposed) | Active exclusions only | N/A | Via pg_dump | Clean expired weekly | Ops |

### Estimated steady-state VPS PG size

| Table | Steady-state rows | Steady-state size |
|-------|-------------------|-------------------|
| app.completed_trades | ~154,000 (7d @ 22K/day) | ~185 MB |
| app.price_entries | ~350,000 (7d @ 50K/day) | ~90 MB |
| app.snapshot_runs | ~1,440 (90d @ 16/day) | ~0.4 MB |
| app.segment_run_aggregates (hourly) | ~1,700,000 (30d @ 57K/day) | ~200 MB |
| app.segment_run_aggregates (daily) | ~33,580 (365d @ 92/day) | ~4 MB |
| app.segment_rune_prices | ~33,580 (365d @ 92/day) | ~8 MB |
| app.ruleset_breakdowns | ~1,460 (365d @ 4/day) | ~0.5 MB |
| app.product_builds | ~1,460 | ~1 MB |
| Other reference tables | ~100 | ~0.1 MB |
| **Total** | | **~489 MB** (~1 GB with indexes, overhead) |

This is well within the 2 GB soft budget and 8 GB hard limit, even with growth.

---

## 12. Schema Implications

### Required before first pilot (minimal)

- No schema changes. Pilot uses the existing migrations (001-009) as-is.
- The 7-day raw retention is advisory during pilot — no prune runs during the bounded test.

### Required before VPS move

1. **Create `app.segment_run_aggregates`** table (as defined in §6) — needed for the production prune cycle to work without breaking VWAP model
2. **Create `app.prune_exclusions`** table (as defined in §8) — optional safety for excluding pilot/experimental data from pruning
3. **Add prune audit log** — either a new `app.prune_audit` table or reuse `health.health_runs` with workflow='prune'

### Deferred until growth proves necessary

- Table partitioning (defer until >10M rows)
- REINDEX monitoring (handled by autovacuum)
- Specialized bloat controls
- Cloud backup

---

## 13. Strong Codex Implications

### What Strong Codex should implement in the first PG session

1. **Create `app.segment_run_aggregates` table and migration**
2. **Create aggregate generation** — post-snapshot script that upserts hourly aggregates from new completed_trades rows
3. **Create prune dry-run script** — `scripts/traderie_prune_dry_run.py` that identifies prune-eligible rows by age, reports counts, estimates reclaim
4. **Create prune execution script** — `scripts/traderie_prune.py` with --apply that follows the safety sequence in §8
5. **Add prune audit logging** — write results to `health.health_runs` or a dedicated table
6. **Update health export** — include `storage_bytes` and `storage_growth_bytes_24h` fields
7. **Add aggregate read path to model** — `calculate_rune_prices.py` reads aggregates + recent raw window instead of full scan
8. **Tests** — aggregate generation, prune dry-run, prune execution (against fixture data)
9. **Documentation** — update `docs/retention.md` to cover PG table-level retention, update `docs/backup-restore.md` to cover aggregate archive

### What must remain deferred

- Partitioning design/implementation
- Prune exclusions table (add only if a need arises during pilot)
- Cloud backup
- VACUUM FULL or reindex scheduling

---

## 14. Decision Requests for Buddy

### D1: Raw completed_trades retention window on VPS

| Option | Storage | Risk |
|--------|---------|------|
| **7 days** (recommended) | ~185 MB steady-state | Model can still work via aggregates; 7d covers the rolling 50-cap window completely |
| 14 days | ~370 MB steady-state | Safer if aggregate generation is delayed; more overlap |
| 30 days | ~800 MB steady-state | More comfortable buffer but starts consuming significant disk |
| 90 days | ~2.4 GB steady-state | Enters warning territory |

**Recommended: 7 days.** The 50-cap window means rows older than ~7 days have no new information. The model runs on aggregates plus the raw 7-day window. Product impact is zero (UI reads product JSON, not raw rows).

### D2: Hourly aggregate retention on VPS

| Option | Rows | Storage |
|--------|------|---------|
| **30 days** (recommended) | ~1.7M | ~200 MB |
| 90 days | ~5.1M | ~600 MB — acceptable but wasteful without graph UI |
| 14 days | ~0.8M | ~93 MB — too short for weekly trend analysis if graphs are added later |

**Recommended: 30 days.** Balances future graph needs against current storage budget.

### D3: Daily aggregate retention on VPS

| Option | Storage | Use |
|--------|---------|-----|
| **365 days** (recommended) | ~4 MB | Trivial storage, enables a full year of price history if graph feature is added |
| Indefinite | ~4 MB/year | Also trivial — could be kept indefinitely |
| 90 days | ~0.3 MB | Saves nothing meaningful |

**Recommended: 365 days.** Storage cost is negligible. Enables a full year of historical price reference.

### D4: Whether to implement aggregates before PG pilot or after

| Option | Risk |
|--------|------|
| **Before pilot** (recommended) | Aggregate generation is part of the initial adapter — the first data loaded is immediately aggregated. Prune can run from day one under safe conditions. |
| After pilot | Must load raw rows, then later backfill aggregates. Risk that prune-deleted raw rows create a gap in analysis. |

**Recommended: Before pilot.** Aggregates are a precondition for raw retention to work. Include them in the first Strong Codex adapter session.

---

## Report Summary

- **Report path:** `docs/TRADERIE_RETENTION_PRUNING_AND_UI_HISTORY_DECISION_20260706.md`
- **Governing ecosystem retention documents:** `vps/shared-conventions.md` §9 (backup retention) and §10 (raw artifact retention). No PG table-level rules exist yet.
- **Projected Traderie growth:** ~22K rows/day, ~27 MB/day raw JSONL, ~55 MB/day estimated PG. Unbounded: 8.5M rows, 19-39 GB at 365 days.
- **Recommended VPS retention windows:** Raw trades 7d, hourly aggregates 30d, daily aggregates 365d, health/ops 90d, reference data indefinite.
- **Recommended Mac archive:** Raw JSONL (indefinite), pg_dump (7 daily + 4 weekly), aggregate CSVs (indefinite).
- **Schema changes required before pilot:** None — existing migrations suffice.
- **Schema changes required before VPS:** `app.segment_run_aggregates`, `app.prune_exclusions`, prune audit logging.
- **Unresolved Buddy decisions:** D1 (raw retention window — recommend 7d), D2 (hourly aggregate retention — recommend 30d), D3 (daily aggregate retention — recommend 365d), D4 (aggregate timing — recommend before pilot).
- **Exact retention requirements for the Strong Codex prompt:** Include the full table-level retention proposal from §11, the aggregate table schema from §6, the prune workflow from §8, and the capacity budgets from §10. Require aggregates as a precondition for raw prune. Require prune to be dry-run-first with backup verification before any delete.
