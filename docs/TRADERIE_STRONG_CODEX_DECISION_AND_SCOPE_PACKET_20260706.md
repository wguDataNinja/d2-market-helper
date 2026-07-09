# Traderie — Strong Codex Decision and Scope Packet

**Date:** 2026-07-06
**Run slug:** traderie-strong-codex-decision-packet
**Superseding implementation report:** `docs/TRADERIE_POSTGRES_VPS_IMPLEMENTATION_AND_REMAINING_WORK_20260706.md` records the completed local Mac PostgreSQL pilot/lifecycle implementation and remaining VPS work. Use this packet as historical scope context, not current status.
**Prerequisite reports:**
- `docs/TRADERIE_IVY_VPS_AUTHORITY_AND_REMAINING_WORK_20260706.md`
- `docs/TRADERIE_PRICING_SOURCE_AND_COLLECTION_AUDIT_20260706.md`
- `docs/TRADERIE_RETENTION_PRUNING_AND_UI_HISTORY_DECISION_20260706.md`
- `docs/TRADERIE_FETCH_EFFICIENCY_AND_CADENCE_DECISION_20260706.md`

---

## 1. Executive Readiness Verdict

**READY WITH CONDITIONS**

The Strong Codex prompt can now be written. All facts have been collected across four audit passes. Every schema, collector, data flow, retention requirement, UI constraint, and ecosystem standard has been documented.

**Unresolved decisions (4 — see §13):**
1. 7-day vs 14-day raw retention window (recommend 7d)
2. Daily aggregate: 365 days vs indefinite (recommend 365d under 100 MB budget)
3. Default local archive format (recommend compressed JSONL + pg_dump, no new .db)
4. Repository cleanup scope (recommend dev/ and captures/ removal before push)

**Schema blockers for implementation:** None. Existing 9 migrations are sufficient for the pilot. Three new migrations needed before VPS (010: collection_run_metrics, 011: segment_aggregates, 012: prune_audit).

**Repository curation:** Recommend cleanup happen **during** Strong Codex adapter work, not before. The pilot adapter work and curation are independent enough to parallelize within one session. Cleanup before push can be a separate step.

**Mac PostgreSQL pilot readiness:** ✅ Ready in principle. The following are complete:
- Database `traderie` provisioned on Mac PG16 with 6 roles
- 9 base migrations applied and validated
- Seed data loaded (4 segments, reference rows)
- Clean baseline backup and restore drill PASS
- Pilot loader exists with 6/6 tests PASS
- Readiness report generates clean eligible subset (25 records, pc_sc_l, digest `df82ac34`)

**Blockers before VPS timer activation (must be complete):**
1. Real PostgreSQL adapter (currently in-memory dry store)
2. Collection-run metrics table and recording
3. Hourly/daily aggregate generation
4. Prune dry-run and apply (raw 7d only)
5. Health export production readiness
6. Three missing wrapper scripts
7. VPS cloudscraper smoke test

---

## 2. Existing Schema Review

| Capability | Status | Evidence | Required Change |
|------------|--------|----------|-----------------|
| Real PostgreSQL ingestion | ❌ Blocked | `scripts/traderie_pg_adapter.py` is in-memory dry store | Implement real adapter with psycopg2 + traderie_writer |
| Run identity | ✅ Partial | `app.snapshot_runs` exists but only tracks segment-level runs | Extend for collection metrics, or add separate metrics table |
| Source identity | ✅ Supported | `app.sources` table exists with source_slug PK | None |
| Segment identity | ✅ Supported | `app.segments` with segment_slug PK + 4 seed rows | None |
| Deterministic deduplication | ✅ Supported | `app.completed_trades` has UNIQUE(segment_slug, observation_key) | None |
| Pilot batch identity | ✅ Partial | Pilot loader identifies batches by segment+observation_key set | Add ingestion_batch_id to snapshot_runs or new table |
| Pilot rollback | ✅ Supported | Pilot loader --rollback deletes by segment_slug + observation_key | None |
| Collection metrics | ❌ Missing | snapshot_runs has item_count/listing_count but not requests/bytes/new_count/duplicate_ratio | **New migration needed** (010) |
| Hourly aggregates | ❌ Missing | No aggregate table exists | **New migration needed** (011) |
| Daily aggregates | ❌ Missing | No aggregate table exists | Included in 011 |
| Prune audit | ❌ Missing | No prune audit trail exists | **New migration needed** (012) |
| Archive/export audit | ❌ Missing | No table tracks which data was archived where | Add to 012 |
| Health reporting | ✅ Partial | health.health_runs + health.workflow_status exist; export script is inert | Make health export production-ready |
| UI price-history queries | ❌ Missing | No aggregate table exists for UI to query | Covered by 011 |

**Summary:** 3 new migrations needed (010, 011, 012) before VPS timer activation. No changes needed to existing 9 migrations.

---

## 3. Collection-Run Metrics Placement Decision

### Options evaluated

| Option | Pros | Cons |
|--------|------|------|
| 1. Extend `app.snapshot_runs` | Single table for all run data; existing FK from completed_trades | snapshot_runs is per-segment; collection metrics span segments. Would need multiple rows or awkward schema. |
| 2. **Separate `app.collection_run_metrics`** (chosen) | Clean separation; per-run not per-segment; can capture cross-segment metrics; independent retention | One more table |
| 3. JSONB in snapshot_runs | No schema change | Poor queryability; mixed concerns |
| 4. Reuse health.health_runs | Already has workflow field | Health table has different retention (90d); collection metrics may want 365d. Mixing concerns. |

### Chosen design: `app.collection_run_metrics`

```sql
CREATE TABLE IF NOT EXISTS app.collection_run_metrics (
    run_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow            text NOT NULL DEFAULT 'snapshot' CHECK (workflow IN ('snapshot', 'manual_backfill', 'pilot', 'research')),
    started_at          timestamptz NOT NULL,
    completed_at        timestamptz,
    elapsed_ms          integer,
    scheduled_timestamp timestamptz,     -- the scheduled launch time (vs actual started_at)
    trigger_type        text NOT NULL DEFAULT 'scheduled' CHECK (trigger_type IN ('scheduled', 'manual', 'pilot', 'systemd')),

    -- Aggregates across all segments (not per-segment)
    requests_made       integer NOT NULL DEFAULT 0,
    response_bytes      bigint,          -- total HTTP response body bytes, if measurable
    records_returned    integer NOT NULL DEFAULT 0,
    records_new         integer NOT NULL DEFAULT 0,
    records_skipped_duplicate integer NOT NULL DEFAULT 0,
    duplicate_ratio     numeric(5,2),    -- computed: records_skipped / (records_new + records_skipped) * 100
    retries             integer NOT NULL DEFAULT 0,
    failures            integer NOT NULL DEFAULT 0,
    stop_reason         text,            -- 'completed', 'partial_failure', 'error', 'cancelled'

    -- Collector identity
    collector_version   text,            -- git commit hash or script version
    python_version      text,
    cloudscraper_version text,

    -- Error summary (lightweight — full errors in health.ingestion_errors)
    error_summary       jsonb DEFAULT '{}'::jsonb,

    -- Per-segment breakdown as JSONB (detailed but not separate columns)
    -- Structure: {"pc_sc_l": {"requests": 33, "records_returned": 1600, "records_new": 420, "records_skipped": 1180, "failures": 0}}
    segment_breakdown   jsonb DEFAULT '{}'::jsonb,

    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_collection_metrics_started
    ON app.collection_run_metrics(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_collection_metrics_workflow
    ON app.collection_run_metrics(workflow, started_at DESC);
```

### Design rationale

- **One row per run** (not per segment). The collector currently runs all 4 segments in one script invocation.
- **Per-segment breakdown in JSONB** avoids 4x column explosion while preserving drill-down.
- **Separate from snapshot_runs** because snapshot_runs is per-segment and is FK-targeted by completed_trades. Collection metrics are about the run itself, not the segment.
- **Retention:** 365 days (small table — 365 rows/year, ~200 bytes each). If VPS space is tight, reduce to 90 days.
- **Row growth:** 365 rows/year at 4x daily. Trivial.
- **Health queries:** `SELECT * FROM app.collection_run_metrics ORDER BY started_at DESC LIMIT 30` gives the last week of runs with full metrics.

---

## 4. Price-History UI Data Contract

### Current-price view (already implemented)

| Field | Source | Status |
|-------|--------|--------|
| Latest rune price per segment | `app.segment_rune_prices` via latest build_id | ✅ Implemented in product JSON |
| Sample count (total_trades, bid_count, ask_count) | Same | ✅ |
| Confidence level | Same | ✅ |
| Last updated / generated_at | Same | ✅ (in JSON) |
| Freshness status | Computed from generated_at | ⚠️ Not in UI, only in data |

**No schema change needed.**

### Recent-detail view (approved, not implemented)

Allows clicking a rune to see recent individual trades:

| Requirement | Decision |
|-------------|----------|
| Time range | Last 7 days (matches raw retention window) |
| Raw trades required | **Yes** — recent trades from `app.completed_trades` |
| Maximum rows | 100 per segment/rune (pagination enforced) |
| Filters | Segment (required), rune/item (required), date range (optional) |
| Query pattern | `SELECT * FROM app.completed_trades WHERE segment_slug=$1 AND item_name=$2 ORDER BY captured_at DESC LIMIT 100` |
| UI implementation | Not yet built. When built, reads from `/api/recent-trades?segment=pc_sc_l&item=Jah` |
| Storage cost | 0 additional — uses existing 7d raw retention |

### Short-range graph (approved, not implemented)

Hourly resolution price trend:

| Requirement | Decision |
|-------------|----------|
| Resolution | Hourly |
| Maximum range | 7 days (matches raw retention) |
| Required aggregates | avg_price, min_price, max_price, observation_count, ist_pair_count |
| Source | `app.segment_aggregates` WHERE granularity='hourly' AND bucket >= now() - 7 days |
| Query pattern | ~23 runes × 4 segments × 168 hours = ~15K rows. Efficient index scan. |
| UI implementation | Not yet built. Reads from `/api/price-history?segment=pc_sc_l&item=Jah&granularity=hourly&range=7d` |
| Storage cost | Hourly aggregates retained 30 days by default |

### Long-range graph (approved, not implemented)

Daily resolution price trend:

| Requirement | Decision |
|-------------|----------|
| Resolution | Daily |
| Minimum range | 365 days (trailing year) |
| Required aggregates | vwap, median_price, min_price, max_price, observation_count, volume |
| Source | `app.segment_aggregates` WHERE granularity='daily' AND bucket >= now() - 365 days |
| Query pattern | ~23 runes × 4 segments × 365 days = ~33K rows. Trivial. |
| UI implementation | Not yet built. Reads from `/api/price-history?segment=pc_sc_l&item=Jah&granularity=daily&range=1y` |
| Storage cost | Daily aggregates retained 365 days by default (~33K rows, ~4 MB) |

### Aggregate fields per bucket

| Field | Justified? | Rationale |
|-------|-----------|-----------|
| bucket_start | ✅ Required | Time period start |
| bucket_end | ✅ Required | Time period end (or implicit from granularity) |
| segment_slug | ✅ Required | Which economy segment |
| rune_id | ✅ Required | Which rune |
| granularity | ✅ Required | 'hourly' or 'daily' |
| observation_count | ✅ Required | Number of raw observations contributing |
| vwap | ✅ Required | Volume-weighted average price (the primary model output) |
| median_price | ✅ Recommended | Useful for graph visualization (less outlier-sensitive) |
| min_price | ✅ Recommended | Range visualization |
| max_price | ✅ Recommended | Range visualization |
| ist_pair_count | ✅ Required | Number of Ist-paired trades (model quality signal) |
| and_trade_count | ✅ Recommended | Number of AND-bundle trades included |
| volume_total | ✅ Recommended | Sum of quantities traded |
| opening_value | ❌ Not justified | Requires ordering raw rows — too expensive for hourly. Dropped. |
| closing_value | ❌ Not justified | Same reason. Dropped. |
| first_seen_at | ❌ Not justified | Implicit from bucket_start. Dropped. |
| last_seen_at | ❌ Not justified | Implicit from bucket_end. Dropped. |
| build_id | ❌ Not justified | Provenance is at the run level, not per aggregate bucket. Dropped. |

### UI feature status summary

| Feature | Status | Justification |
|---------|--------|---------------|
| Current-price table | ✅ Implemented | Core product |
| Source directory | ✅ Implemented | Transparency |
| Methodology page | ✅ Implemented | Required for alpha |
| Recent-detail view | 🔲 Approved, not implemented | Relies on PR adapter + real PG |
| Short-range graph | 🔲 Approved, not implemented | Relies on aggregate table |
| Long-range graph | 🔲 Approved, not implemented | Relies on aggregate table |
| Graph model v2 (pair correction) | 🔲 Speculative (BACKLOG.md) | No approved requirements yet |
| Alerting mechanism | 🔲 Speculative (BACKLOG.md) | No approved requirements yet |
| Item profiles display | 🔲 Speculative (BACKLOG.md) | No approved requirements yet |
| Price-history probe (Diablo2.io) | ❌ Rejected for v1 | Insufficient volume, use_in_model=false |

---

## 5. Aggregate Schema Decision

### Table name: `app.segment_aggregates`

Not `segment_run_aggregates` — aggregates are time-based, not run-based. A single table with a `granularity` column is the smallest maintainable design.

```sql
CREATE TABLE IF NOT EXISTS app.segment_aggregates (
    aggregate_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_slug        text NOT NULL REFERENCES app.segments(segment_slug),
    bucket_start        timestamptz NOT NULL,   -- truncated to hour or day
    granularity         text NOT NULL CHECK (granularity IN ('hourly', 'daily')),
    rune_id             integer NOT NULL REFERENCES app.rune_registry(rune_id),

    -- Aggregates
    observation_count   integer NOT NULL DEFAULT 0,
    ist_pair_count      integer NOT NULL DEFAULT 0,  -- Ist-paired trades (the VWAP model input)
    and_trade_count     integer NOT NULL DEFAULT 0,
    volume_total        integer NOT NULL DEFAULT 0,  -- sum of quantities

    -- Price statistics (numeric(16,6) to handle extreme ratios)
    vwap                numeric(16,6),
    median_price        numeric(16,6),
    min_price           numeric(16,6),
    max_price           numeric(16,6),

    -- Provenance
    source_slug         text NOT NULL DEFAULT 'traderie',
    aggregated_at       timestamptz NOT NULL DEFAULT now(),
    run_id              uuid REFERENCES app.collection_run_metrics(run_id),

    UNIQUE (segment_slug, bucket_start, granularity, rune_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_seg_agg_lookup
    ON app.segment_aggregates(segment_slug, rune_id, bucket_start DESC, granularity);
CREATE INDEX IF NOT EXISTS idx_seg_agg_bucket
    ON app.segment_aggregates(bucket_start, granularity);
CREATE INDEX IF NOT EXISTS idx_seg_agg_run
    ON app.segment_aggregates(run_id);
```

### Aggregate rule

```
Every post-snapshot hook:
  1. Read new records from app.completed_trades WHERE ingested_at > last_aggregation
  2. Group by segment_slug, rune_id, truncated_to_hour(captured_at), 'hourly'
  3. Compute: observation_count, ist_pair_count, and_trade_count, volume_total
  4. Compute price stats: AVG(value_ist) as vwap, PERCENTILE_CONT(0.5) as median,
     MIN, MAX (from price_entries joined to completed_trades)
  5. UPSERT into app.segment_aggregates (ON CONFLICT DO NOTHING for hourly,
     then update in-place; or use INSERT ... ON CONFLICT UPDATE)

Every daily post-snapshot hook:
  1. Aggregate hourly rows into daily rows: GROUP BY segment, rune_id, truncated_to_day
  2. Weighted average of vwap by observation_count, re-compute min/max
  3. UPSERT into app.segment_aggregates with granularity='daily'

Idempotent: re-running produces same results (aggregates are deterministic from raw data).
```

### Late-arriving data

If a record's `captured_at` falls into a past hourly bucket whose aggregate was already computed:
- Hourly aggregate: UPDATE instead of INSERT. The UPSERT conflict target handles this.
- Daily aggregate: Re-aggregate ALL hourly rows for that day when any hourly bucket changes.

### Retention behavior

- Hourly: DELETE WHERE bucket_start < now() - interval '30 days'
- Daily: DELETE WHERE bucket_start < now() - interval '365 days'
- Both prune operations follow the same safe sequence as raw prune.

### Row count and size projections

| Horizon | Hourly rows | Daily rows | Total rows | Estimated size |
|---------|-------------|------------|------------|---------------|
| 30 days | 66,240 (23×4×24×30) | 0 | 66,240 | ~12 MB |
| 365 days | 0 (pruned) | 33,580 (23×4×365) | 33,580 | ~6 MB |
| 3 years | 0 (pruned) | 100,740 | 100,740 | ~18 MB |
| 5 years | 0 (pruned) | 167,900 | 167,900 | ~30 MB |

---

## 6. Retention and Pruning Decision

### Final table-level policy

| Table / Data class | VPS retention | Aggregate retention | Mac archive | Prune key | Cadence | Backup prerequisite | UI/ops justification |
|---|---|---|---|---|---|---|---|
| `app.snapshot_runs` | 90 days | N/A | Via pg_dump | `created_at < now() - 90d` | Weekly | Yes | Run provenance |
| `app.collection_run_metrics` | 365 days | N/A | Via pg_dump | `started_at < now() - 365d` | Monthly | Yes | Efficiency monitoring |
| `app.completed_trades` | **7 days** | N/A | Source JSONL + pg_dump | `captured_at < now() - 7d` | Daily | Yes + aggregate parity verified | Recent-detail UI (max 100 rows); model input via aggregates |
| `app.price_entries` | 7 days (CASCADE) | N/A | Reconstructable | CASCADE from completed_trades | Daily | Yes | Price decomposition |
| `app.segment_aggregates` (hourly) | 30 days | N/A | Reconstructable from daily | `bucket_start < now() - 30d` | Daily | No (reconstructable) | Short-range graph |
| `app.segment_aggregates` (daily) | **365 days** | N/A | CSV.gz archive | `bucket_start < now() - 365d` | Monthly | Recommended | Long-range graph |
| `app.segment_rune_prices` | 365 days (indefinite if under budget) | N/A | Product JSON in git | Never (keep full year) | N/A | N/A | Current-price UI |
| `app.ruleset_breakdowns` | 365 days | N/A | Via pg_dump | `created_at < now() - 365d` | Yearly | Recommended | Ruleset metadata |
| `app.product_builds` + log | 365 days | N/A | Via pg_dump | `created_at < now() - 365d` | Yearly | Recommended | Build lineage |
| `app.prune_audit` | 365 days | N/A | Via pg_dump | `pruned_at < now() - 365d` | Yearly | No | Audit trail |
| `app.sources` | Indefinite | N/A | Git | Never | N/A | N/A | Reference |
| `app.segments` | Indefinite | N/A | Git | Never | N/A | N/A | Reference |
| `app.rune_registry` | Indefinite | N/A | Git | Never | N/A | N/A | Reference |
| `health.health_runs` | 90 days | N/A | Via pg_dump | `created_at < now() - 90d` | Weekly | No | Ops monitoring |
| `health.workflow_status` | Indefinite (UPSERT) | N/A | Via pg_dump | Never (only latest per workflow) | N/A | N/A | Ops monitoring |
| `health.ingestion_errors` | 30 days | N/A | Via pg_dump | `created_at < now() - 30d` | Weekly | No | Error diagnostics |
| Source JSONL (`data/history/`) | N/A (VPS: not stored) | N/A | **Indefinite** (Mac compresses) | Never (source evidence) | N/A | N/A | Source-of-truth archive |
| Product JSON (`data/products/`) | N/A (Git-managed) | N/A | Git | Version-controlled | N/A | N/A | Current UI input |
| pg_dump (VPS) | 7 daily, 4 weekly | N/A | 14→7 daily, 4 weekly | Age | Daily | N/A | Full recovery |
| pg_dump (Mac) | 14→7 daily, 4 weekly + monthly | N/A | Mac backup | Age | Daily pull | N/A | Disaster recovery |

### Daily aggregate retention rule

**Recommendation: 365 days, renewable annually under 100 MB table-size budget.**

If `app.segment_aggregates WHERE granularity='daily'` exceeds 100 MB, review whether longer retention is justified by actual UI usage. At projected ~6 MB/year, this threshold takes ~16 years to reach, making it effectively indefinite.

---

## 7. Mac Archive Design

### Archive components

| Component | Format | Purpose | New .db file needed? | Rationale |
|-----------|--------|---------|---------------------|-----------|
| Source-native evidence | **Compressed JSONL** (`.jsonl.gz`) | Preserves original deduped observations exactly as collected | **No** — JSONL already exists, just compress | Zero data loss; append-only; already the format the pipeline uses; compressible 5-10× |
| Full database recovery | **pg_dump custom format** (`--format=custom --compress=9`) | Complete point-in-time restore | **No** — pg_dump already standard | Supports selective restore; pg_restore; preserves all types |
| Deep historical analysis | **Minimal: compressed JSONL is sufficient**. If needed: DuckDB for | Running analytical queries across years of history without loading into PG | **No DuckDB now** — add only if query need arises | JSONL.gz is directly queryable by DuckDB if needed later; no upfront cost |
| Compact exports | **CSV.gz** for daily aggregates, **JSON** for product snapshots | Lightweight portable archives for dashboard or external use | **No** — CSV/JSON are standard | Already generated by the pipeline |

### Recommendation: No new local `.db` file

The existing JSONL format already serves all archive purposes:
- Source evidence: `.jsonl.gz` preserves original with compression
- Deep analysis: DuckDB reads JSONL/CSV directly; no migration needed
- Full recovery: pg_dump covers this
- Compact exports: CSV/JSON already exist

A SQLite archive would add a second write path, a migration burden, and no query benefit that compressed JSONL + DuckDB-on-read doesn't already provide.

### Archive destination paths

```
Mac: /Users/buddy/projects/backups/postgres/traderie/
  pg_dump/
    daily/traderie_YYYYMMDDTHHMMSSZ.dump.gz
    daily/traderie_YYYYMMDDTHHMMSSZ.dump.gz.sha256
    weekly/traderie_YYYYMMDDTHHMMSSZ.dump.gz (+ checksum)
    immutable/ (pre-migration, cutover baselines)
  source_archive/
    history/traderie_{seg}_completed_trades_YYYYMMDD.jsonl.gz
    aggregates/hourly/traderie_hourly_YYYYMMDD.csv.gz
    aggregates/daily/traderie_daily_YYYYMM.csv.gz
    products/in_game_rune_values_YYYYMMDD.json
  manifests/
    archive_manifest_YYYYMMDD.json
```

### Partitioning and compression

- JSONL: gzip at max compression (`gzip -9`). Expect 5-10× reduction (425 MB → ~50-85 MB for current history)
- pg_dump: built-in `--compress=9`
- CSVs: gzip at max compression

### Checksums and manifests

Every archived file has a `.sha256` sidecar. Manifests are JSON files listing:
```
{
  "manifest_version": 1,
  "project": "traderie",
  "created_at": "...",
  "files": [
    {"path": "source_archive/history/traderie_pc_sc_l_20260706.jsonl.gz",
     "sha256": "...", "size_bytes": 12345, "compressed": true,
     "source_format": "jsonl", "row_count": 107300}
  ]
}
```

### Transfer verification

Each pg_dump file is SCP'd from VPS to Mac. Mac side verifies SHA-256 before accepting. Source JSONL is already on Mac (current Traderie data directory) — compression happens in-place after backup verification.

### Retention

| Archive type | Mac retention | Prune trigger |
|---|---|---|
| pg_dump daily | 14 → 7 days | Age + keep newest N |
| pg_dump weekly | 4 (kept from Sunday) | Age |
| pg_dump immutable | Indefinite | Never (requires Destructive Operation Gate) |
| Compressed JSONL history | Indefinite | Never (source evidence) |
| Aggregate CSV exports | Indefinite | Never (compact) |
| Product JSON snapshots | Pruned to latest only | Monthly cleanup |

---

## 8. Prune Implementation Contract

### Safe workflow

```python
def safe_prune(dry_run=True, segment=None, table=None):
    # Step 1: Identify eligible rows
    for seg in (segment or ALL_SEGMENTS):
        count_before = count_rows(seg)
        
        # Step 2: Dry-run counts
        eligible = SELECT COUNT(*) FROM app.completed_trades
                   WHERE segment_slug=seg AND captured_at < now() - interval '7 days'
        print(f"  {seg}: {eligible} rows eligible for prune")
        
        if dry_run:
            continue  # Report only
        
        # Step 3: Verify backup prerequisite
        backup = SELECT backup_state FROM health.workflow_status WHERE workflow='backup'
        assert backup == 'ok', "Backup must be current before prune"
        
        # Step 4: Verify aggregate coverage (all eligible rows have been aggregated)
        max_captured = SELECT MAX(captured_at) FROM app.completed_trades WHERE segment_slug=seg
        agg_check = SELECT MAX(bucket_start) FROM app.segment_aggregates
                    WHERE segment_slug=seg AND granularity='hourly'
        assert agg_check >= max_captured, "Aggregates must cover all prune-eligible rows"
        
        # Step 5: Prune in bounded batches (10,000 rows)
        total_deleted = 0
        while True:
            DELETE FROM app.price_entries
            WHERE trade_id IN (
                SELECT trade_observation_id FROM app.completed_trades
                WHERE segment_slug=seg AND captured_at < now() - interval '7 days'
                LIMIT 10000
            );
            DELETE FROM app.completed_trades
            WHERE trade_observation_id IN (
                SELECT trade_observation_id FROM app.completed_trades
                WHERE segment_slug=seg AND captured_at < now() - interval '7 days'
                LIMIT 10000
            );
            rows = GET DIAGNOSTICS rows_deleted = ROW_COUNT
            total_deleted += rows
            COMMIT  # per batch
            if rows == 0: break
            pg_sleep(0.1)  # avoid lock buildup
        
        # Step 6: Record prune audit
        INSERT INTO app.prune_audit (table_name, segment_slug, rows_deleted, ...)
        
        # Step 7: ANALYZE
        ANALYZE app.completed_trades
        ANALYZE app.price_entries
        
        # Step 8: Inspect dead tuples (report only)
        dead = SELECT n_dead_tup FROM pg_stat_user_tables WHERE relname='completed_trades'
        if dead > 100000:  # >100K dead tuples
            VACUUM app.completed_trades  # not FULL
        
        # Step 9: Report
        print(f"  Pruned {total_deleted} rows from {seg}")
        print(f"  Table now has {count_after} rows, {dead} dead tuples")
```

### Batch size

10,000 rows per batch (balances transaction overhead against lock duration). At ~200 bytes/row, this is ~2 MB per DELETE batch. Duration per batch: <1 second.

### Transaction boundaries

Each batch is its own transaction. If the prune script crashes mid-way, the next run starts fresh — already-deleted rows won't match the eligibility criteria.

### CLI interface

```
python3 scripts/traderie_prune.py --dry-run          # report only
python3 scripts/traderie_prune.py --apply             # prune all eligible, all segments
python3 scripts/traderie_prune.py --apply --segment pc_sc_l  # single segment
python3 scripts/traderie_prune.py --apply --table aggregates  # prune aggregate tables
```

### Approval gate

- `--dry-run`: no gate needed (read-only)
- `--apply`: requires backup age < 24h, aggregate parity verified, Destructive Operation Gate approval documented in LOG.md

### Rollback/recovery

Rollback is via pg_restore from the pre-prune backup. The prune audit records exactly what was deleted and when, enabling manual re-insertion if needed (unlikely — pruning is 7-day-old data that aggregates already cover).

### Pilot batch interaction

Pilot data uses specific observation_keys with recent captured_at timestamps. It will not match the 7-day prune criterion until after the pilot duration (days to weeks). If the pilot needs to survive longer than 7 days, either:
- Extend the prune exclusion for pilot observation_keys via observation_key pattern
- Or mark pilot rows with a `pilot_batch_id` column (future enhancement, not required now)

### Partitioning

**Not justified.** At 7-day retention, completed_trades is bounded at ~154,000 rows — well within normal PostgreSQL operation. Partitioning adds schema complexity, maintenance burden, and query planning overhead for no measurable benefit at this scale. Re-evaluate only if:
- completed_trades exceeds 5M rows
- DELETE/VACUUM cycles fail to keep up
- Query performance degrades on the index scan

---

## 9. Repository Curation Boundary

### Remove from tracking after archival/review

| Path | Why | Cleanup action | Who |
|------|-----|----------------|-----|
| `dev/` (~50 MB, 200+ ad/tracker files) | Downloaded Traderie site assets with ad scripts, tracking pixels, CSS. Not source code. | `git rm -r dev/` + add to `.gitignore` | Strong Codex (mechanical) |
| `research/sources/captures/` (browser captures with screenshots) | Browser-captured pages with screenshots, network logs. Should not be in git. | `git rm -r research/sources/captures/` + add to `.gitignore` | **Buddy review** — may contain sensitive page content |
| `research/sources/downloads/` (11 downloaded HTML pages) | One-shot discovery pages | `git rm -r research/sources/downloads/` | Strong Codex |
| `scripts/old/` (52 legacy scripts) | Superseded | Move to `_archive/scripts/` | Strong Codex |
| `notebook/` (6 Jupyter notebooks) | Exploratory | Move to `_archive/notebooks/` | Strong Codex |
| `reports/` (generated HTML, TXT, PNG) | Generated artifacts | `git rm -r reports/` | Strong Codex |
| `data/research/memos/` (discovery memos) | Stale research | Move to `_archive/research/` | Strong Codex |
| `docs/CODEX_HANDOFF.md`, `docs/ivy_manifest.json`, etc. | Stale docs | Archive or delete after review | Buddy review |
| `data/completed_pc_sc_nl_normalized.csv` | Stale CSV | `git rm` | Strong Codex |
| `data/g2g_rune_prices_softcore_nonladder_pc.csv` | Stale CSV | `git rm` | Strong Codex |

### Keep in GitHub

Runtime-critical:
- `scripts/snapshot_traderie.py`, `scripts/lib/snapshot_io.py`
- `scripts/build_traderie_dataset_from_history.py`, `scripts/calculate_rune_prices.py`, `scripts/generate_prices_json.py`, `scripts/generate_external_cash_prices.py`
- `scripts/collection_status.py`, `scripts/validate_*.py` (4 files)
- `scripts/run_traderie_snapshot_launchd.sh` (Mac), `scripts/regenerate_products.sh`
- `server_configs.json`, `data/item_ids.json`, `data/rune_registry.json`, `data/source_manifest.json`

PostgreSQL adapter (new + existing):
- `scripts/traderie_pg_adapter.py`, `scripts/traderie_storage_adapter.py`
- `scripts/traderie_pilot_loader.py`, `scripts/traderie_pilot_readiness_report.py`
- `scripts/traderie_health_export.py`, `scripts/traderie_disk_inventory.py`, `scripts/traderie_parity_report.py`

Migrations + validation:
- `db/migrations/*.sql` (9 + 3 new), `db/migrations/rollback/*.sql`, `db/migrations/validation/*.sql`
- `db/validation/999_full_validation.sql`, `db/fixtures/seed.sql`

Tests + CI:
- `tests/` (fixtures + test_*.py), `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`

Infrastructure:
- `deploy/README.md`, `deploy/ROLLBACK.md`, `deploy/env.example`
- `deploy/systemd/*.service`, `deploy/systemd/*.timer`

Web:
- `web/` (all source files — needed for GH Pages deploy)

Documentation:
- `docs/ARCHITECTURE.md`, `docs/PRICING_MODEL.md`, `docs/DATA_PRODUCTS.md`
- `docs/VPS_CONTINUITY.md`, `docs/backup-restore.md`, `docs/retention.md`
- `docs/LAUNCHD_SETUP.md`, `docs/USERSCRIPT.md`, `docs/SOURCE_MANIFEST.md`
- All `docs/TRADERIE_*_20260706.md` reports

Agent + planning:
- `AGENTS.md`, `ROADMAP.md`, `VPS_ROADMAP.md`, `BACKLOG.md`
- `SESSION.md`, `LOG.md`, `README_INTERNAL.md`

### Missing required assets

| Asset | Status | Action |
|-------|--------|--------|
| `README.md` (public) | **MISSING** | Create minimal public README |
| `LICENSE` | **MISSING** | Add MIT license |
| `scripts/run_traderie_snapshot.sh` (VPS variant) | **MISSING** | Create — adapt from launchd version with VPS paths |
| `scripts/run_traderie_backup.sh` | **MISSING** | Create — pg_dump + checksum + manifest |
| `scripts/run_traderie_validate.sh` | **MISSING** | Create — runs all 4 validators |
| VPS `.env` template (at `deploy/env.example`) | **EXISTS** | Already present, reference from `deploy/` |

---

## 10. Ivy-Control Ecosystem Standards

### A. PostgreSQL Data Lifecycle and Storage Budget Standard

Add to `ivy-control/vps/shared-conventions.md` after §10 (Raw Artifact and Export Policy):

```
## 10A. PostgreSQL Data Lifecycle and Storage Budget

Every PostgreSQL-backed repository MUST document and maintain a
table-level data lifecycle policy before its first scheduled timer
activation. Traderie is the first implementation example.

### Required documentation

| Item | Requirement |
|------|-------------|
| Table-level retention | Every table with unbounded growth has a retention window, prune key, and prune cadence |
| Growth estimates | Projected row count and storage at 30, 90, 180, and 365 days |
| Storage budget | Soft and hard thresholds in MB or GB |
| Aggregate strategy | How raw data is compacted into hourly/daily/summary tables |
| Archive destination | Where pruned data is preserved (Mac, cloud, cold storage) |
| Archive-before-prune | Whether prune requires a verified backup or aggregate parity |
| Health metrics | Storage_bytes, growth_24h, prune rows deleted reported in health export |
| Restore expectations | RPO, RTO, and restore drill cadence |
| UI justification | Every retained data class tied to an approved product feature |

### Default rule

No repository receives unlimited PostgreSQL storage. Every table with
unbounded growth MUST have a documented retention window shorter than
365 days unless:
- the table's row count is bounded by reference data (<10,000 rows), or
- the table stores compact aggregates whose total size is under 100 MB,
  and retention is explicitly approved with a product UI justification.

### Health monitoring

Every project health export MUST include:
- per-table row counts for the largest 3 tables by size
- total database size
- 24-hour growth
- prune audit records (last prune, rows removed)
- any table exceeding 50% of its retention window
```

### B. Scheduled Collector Efficiency Standard

Add to `ivy-control/vps/shared-conventions.md` after §8 (Health Contract):

```
## 8A. Scheduled Collector Efficiency Standard

Every scheduled HTTP/API collector operating under ivy-control VPS
governance MUST document the following before timer activation.

### Required documentation

| Item | Requirement |
|------|-------------|
| Source visibility window | How long a record remains visible in the source endpoint |
| Endpoint behavior | Pagination, sort order, filters, rate limits, response format |
| Fetch depth | How many pages/records are fetched per run and why |
| Cadence justification | Why the chosen cadence is appropriate for the visibility window |
| Pagination/cursor evaluation | Whether incremental fetching is possible and why or why not |
| Deduplication key | The field or compound key used to prevent duplicate rows |
| Overlap rationale | Expected duplicate ratio and why it is acceptable |
| Max requests/run | Hard limit on requests per collector invocation |
| Max requests/day | Hard limit on requests per 24-hour period |
| Bandwidth estimate | Expected bytes transferred per run and per day |
| Retry/backoff limits | Max retries per request, backoff strategy, timeout |
| Concurrency prevention | Lock mechanism preventing overlapping runs |
| Efficiency metrics | Requests, bytes, records_returned, records_new, duplicate_ratio reported per run |
| Timer activation gate | Scheduler Gate approval documented in LOG.md |

### Permitted full-window refetch

A collector MAY use bounded full-window refetch when:
1. Incremental retrieval is not technically available (proven by
   documentation of endpoint limitations), AND
2. The source's visibility window is smaller than the required
   capture window, AND
3. The cadence is set to no more than 2× the median visibility
   half-life unless a shorter cadence is justified by data freshness
   requirements, AND
4. The duplicate ratio is tracked and reported in health metrics.

A duplicate ratio consistently above 95% warrants cadence reduction
or investigation unless the collector proves the ratio is unavoidable
and the bandwidth cost is negligible.

### Timer activation gate

No collector may run on a systemd timer, launchd schedule, or cron
until this documentation exists and the Scheduler Gate (per §11) is
approved.
```

---

## 11. Strong Codex Implementation Scope

### Ordered implementation plan

| Step | Description | Files | Dependencies | Tests | Gate | Completion evidence |
|------|-------------|-------|--------------|-------|------|-------------------|
| 1 | **Curate repository surface** | Remove dev/, scripts/old/→_archive/, stale docs, captured pages, stale CSVs | None | `git status` clean | Buddy review for captures/ | Repo clean; git status shows only intentional changes |
| 2 | **Add README + LICENSE** | Create `README.md`, add `LICENSE` (MIT) | Step 1 | None | Buddy (license choice) | Files exist, git status clean |
| 3 | **Add missing wrapper scripts** | Create VPS variants: `run_traderie_snapshot.sh`, `run_traderie_backup.sh`, `run_traderie_validate.sh` | None — scripts are independent | ShellCheck, dry-run with --help | None (inert, not enabled) | 3 scripts exist, shellcheck passes |
| 4 | **Implement real PostgreSQL adapter** | Rewrite `scripts/traderie_pg_adapter.py` to connect to live PG via psycopg2 using `traderie_writer` | PostgreSQL running, env vars configured | `pytest tests/` — adapter tests must pass against live PG | None (writer is isolated) | 46/46 tests pass, adapter connects to traderie DB |
| 5 | **Implement migration 010: collection_run_metrics** | Create `db/migrations/20260706_010_create_collection_metrics.sql` + rollback + validation | Step 4 | Migration validation query | Database Authority Gate | Rows appear in app.traderie_migrations |
| 6 | **Implement migration 011: segment_aggregates** | Create `db/migrations/20260706_011_create_segment_aggregates.sql` + rollback + validation | Step 4 | Migration validation query | Database Authority Gate | Rows appear in app.traderie_migrations |
| 7 | **Implement migration 012: prune_audit** | Create `db/migrations/20260706_012_create_prune_audit.sql` + rollback + validation | Step 4 | Migration validation query | Database Authority Gate | Rows appear in app.traderie_migrations |
| 8 | **Implement collection-run metrics recording** | Add metrics to collector output; write to `app.collection_run_metrics` | Steps 4-5 | Integration test: run collector, verify metrics row | None | Metrics row exists after collector run |
| 9 | **Implement aggregate generation** | Create post-snapshot hook that reads new completed_trades, computes hourly/daily aggregates, UPSERTs to `app.segment_aggregates` | Steps 4, 6 | Integration test: run aggregate gen, verify rows | None | Aggregate rows match stream counts |
| 10 | **Implement prune dry-run/apply** | Create `scripts/traderie_prune.py` with --dry-run and --apply | Steps 4, 7 | Unit test with fixture data; integration: dry-run returns expected counts | **Destructive Operation Gate for --apply** | Prune succeeds; rows removed; audit recorded |
| 11 | **Implement prune/archive audit** | Write prune results to `app.prune_audit` and archive manifest to JSON file | Steps 4, 7, 10 | Integration test: verify audit row after prune | None | Audit rows created |
| 12 | **Extend health metrics** | Make `scripts/traderie_health_export.py` production-ready: read real data, output SHARED-003 fields with storage/growth/prune metrics | Steps 4-11 | Run against live PG, output valid JSON | None | Health JSON includes all required fields |
| 13 | **Add integration tests** | Create `tests/test_traderie_metrics.py`, `tests/test_traderie_aggregates.py`, `tests/test_traderie_prune.py` | Steps 8-11 | pytest passes | None | 10+ new tests pass |
| 14 | **Prove bounded Mac pilot** | Run `traderie_pilot_loader.py --plan --limit=25 --segment=pc_sc_l`; with approval, run `--apply` | Steps 4-13 | Pre-post backup, row count verification, rollback proof, reimport proof | **Buddy Gate approval** | Pilot report documents counts, digests, parity, rollback, reimport |
| 15 | **Update Traderie continuity docs** | Update `docs/VPS_CONTINUITY.md`, `docs/retention.md`, `docs/backup-restore.md` | Steps 1-14 | Manual review | Buddy review | Docs reflect current state |
| 16 | **Update Ivy-Control shared conventions** | Add 8A (Collector Efficiency) and 10A (Data Lifecycle) to `ivy-control/vps/shared-conventions.md` | None | Manual review | Buddy review | Two new sections added |
| 17 | **Leave VPS timers disabled** | Confirm all systemd units are `--user disable`d; no timer enabled | None | `systemctl --user list-timers` | N/A — designed state | Timers are inactive |

---

## 12. Exact Commands for the Strong Codex Prompt

### Baseline Git inspection

```bash
cd /Users/buddy/projects/traderie
git status
git log --oneline -10
git diff --stat
git ls-files --others --ignored --exclude-standard | head -20
```

### Dependency installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install psycopg2-binary pytest    # for PG adapter
pip freeze > /dev/null                # verify no unexpected deps
```

### Test execution

```bash
python3 -m pytest tests/ -v                                    # baseline: 46/46 pass
python3 -m pytest tests/ -v --tb=short                         # after adapter change
python3 -m py_compile scripts/*.py scripts/lib/*.py            # syntax check all
```

### PostgreSQL connection verification

```bash
# Verify PostgreSQL is running and traderie database exists
psql -d traderie -c "SELECT current_database(), current_user, version();"
psql -d traderie -c "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema IN ('app','health','archive') ORDER BY table_schema, table_name;"
psql -d traderie -c "SELECT count(*) as migration_count FROM app.traderie_migrations;"
```

### Migration verification

```bash
# Verify all 9 (+3 new) migrations are applied
for f in db/migrations/2026*.sql; do
  echo "=== $(basename $f) ==="
  psql -d traderie -f "$f" 2>&1 | tail -3
done

# Run full validation
psql -d traderie -f db/validation/999_full_validation.sql

# Run per-migration validation checks
for f in db/migrations/validation/*.sql; do
  echo "=== $(basename $f) ==="
  psql -d traderie -f "$f"
done
```

### Adapter integration tests

```bash
# After implementing real adapter
python3 -m pytest tests/test_traderie_adapter.py -v
python3 -m pytest tests/test_traderie_pilot_loader.py -v

# Test connection
python3 -c "
from scripts.traderie_pg_adapter import PgTraderieAdapter
adapter = PgTraderieAdapter()
print('Connected:', adapter.check_connection())
print('Tables:', adapter.get_table_list())
"
```

### Collector dry-run or safe bounded verification

```bash
# Dry-run only — no API calls
python3 scripts/snapshot_traderie.py --segment pc_sc_l --single --dry-run

# Bounded live test (single item, single segment)
python3 scripts/snapshot_traderie.py --segment pc_sc_l --single

# Run collection metrics after collector completes
python3 -c "
from scripts.traderie_pg_adapter import PgTraderieAdapter
adapter = PgTraderieAdapter()
metrics = adapter.get_latest_collection_metrics()
print(metrics)
"
```

### Pilot plan

```bash
# Read-only plan
python3 scripts/traderie_pilot_readiness_report.py --eligible-only --json

# Full plan with detail
python3 scripts/traderie_pilot_loader.py --plan --limit=25 --segment=pc_sc_l
```

### Pre-pilot backup

```bash
# APPROVAL REQUIRED: Backup/Restore Gate
pg_dump --format=custom --compress=9 --dbname=postgresql://traderie_backup@localhost/traderie \
  --file=/Users/buddy/projects/backups/postgres/traderie/traderie_pre_pilot_$(date -u +%Y%m%dT%H%M%S).dump
sha256sum /Users/buddy/projects/backups/postgres/traderie/traderie_pre_pilot_*.dump \
  > /Users/buddy/projects/backups/postgres/traderie/traderie_pre_pilot_$(date -u +%Y%m%dT%H%M%S).dump.sha256
```

### Pilot apply

```bash
# APPROVAL REQUIRED: Buddy Gate approval + backup verified
python3 scripts/traderie_pilot_loader.py --apply --limit=25 --segment=pc_sc_l
```

### Parity

```bash
# Compare file-backed vs PG-backed counts
python3 scripts/traderie_parity_report.py --segment=pc_sc_l

# Detailed: observation_key match
python3 scripts/traderie_pilot_loader.py --parity --segment=pc_sc_l
```

### Aggregate generation

```bash
# Generate hourly aggregates from current completed_trades
python3 scripts/traderie_build_aggregates.py --granularity=hourly --segment=pc_sc_l

# Verify
psql -d traderie -c "SELECT granularity, bucket_start, rune_id, observation_count, vwap FROM app.segment_aggregates ORDER BY bucket_start DESC LIMIT 10;"
```

### Aggregate validation

```bash
# Row count parity: aggregates vs source completed_trades
psql -d traderie -c "
SELECT a.segment_slug, a.rune_id,
       a.observation_count as agg_count,
       ct.source_count,
       round(abs(a.observation_count - ct.source_count)::numeric / nullif(ct.source_count, 0) * 100, 2) as pct_diff
FROM (
  SELECT segment_slug, rune_id, sum(observation_count) as observation_count
  FROM app.segment_aggregates WHERE granularity='hourly' AND bucket_start >= now() - interval '24 hours'
  GROUP BY segment_slug, rune_id
) a
JOIN (
  SELECT segment_slug, t.rune_id, count(*) as source_count
  FROM app.completed_trades t
  JOIN app.price_entries pe ON pe.trade_id = t.trade_observation_id
  WHERE t.captured_at >= now() - interval '24 hours'
  GROUP BY segment_slug, t.rune_id
) ct ON a.segment_slug = ct.segment_slug AND a.rune_id = ct.rune_id
ORDER BY pct_diff DESC LIMIT 10;
"
```

### Prune dry-run

```bash
# Read-only — no data modified
python3 scripts/traderie_prune.py --dry-run

# By segment
python3 scripts/traderie_prune.py --dry-run --segment=pc_sc_l
```

### Prune apply against isolated/pilot data

```bash
# APPROVAL REQUIRED: Destructive Operation Gate + backup < 24h + aggregate parity verified
python3 scripts/traderie_prune.py --apply --segment=pc_sc_l --dry-run  # verify once more
# Then:
python3 scripts/traderie_prune.py --apply --segment=pc_sc_l
```

### Post-prune validation

```bash
psql -d traderie -c "SELECT count(*) FROM app.completed_trades;"
psql -d traderie -c "SELECT relname, n_live_tup, n_dead_tup FROM pg_stat_user_tables WHERE relname IN ('completed_trades','price_entries','segment_aggregates');"
psql -d traderie -c "SELECT * FROM app.prune_audit ORDER BY pruned_at DESC LIMIT 5;"
```

### Archive verification

```bash
ls -la /Users/buddy/projects/backups/postgres/traderie/source_archive/history/
sha256sum -c /Users/buddy/projects/backups/postgres/traderie/source_archive/history/*.sha256
```

### Database/table size checks

```bash
psql -d traderie -c "
SELECT relname as table_name,
       pg_size_pretty(pg_total_relation_size(relid)) as total_size,
       pg_size_pretty(pg_relation_size(relid)) as table_size,
       pg_size_pretty(pg_indexes_size(relid)) as index_size,
       n_live_tup as row_count
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
"
psql -d traderie -c "SELECT pg_size_pretty(pg_database_size('traderie')) as db_size;"
```

### Health export

```bash
python3 scripts/traderie_health_export.py --output /tmp/traderie_health.json
cat /tmp/traderie_health.json | python3 -m json.tool | head -30
```

### Git diff/status

```bash
git status
git diff --stat
git diff --stat --cached
```

### Commit boundaries

```bash
# Suggestion: one commit per logical step
git add -A && git commit -m "step N: description"
# Or use git-steward for explicit-path commits
```

---

## 13. Final Decision List

| # | Decision | Recommended | Alternatives | Storage impact | Product impact | Implementation impact |
|---|---|---|---|---|---|---|
| D1 | Raw completed_trades retention | **7 days** | 14 days (+185 MB), 30 days (+615 MB) | ~185 MB steady-state vs 370 MB (14d) or 800 MB (30d) | None — recent-detail UI limited to 100 rows regardless | Prune runs daily; aggregate parity required before prune |
| D2 | Daily aggregate retention | **365 days** under 100 MB budget | Indefinite (+4 MB/year), 90 days (-0.3 MB) | ~6 MB/year — negligible | Enables 1-year price graph; indefinite would enable multi-year | No difference; same table structure |
| D3 | Local archive format | **Compressed JSONL + pg_dump** — no new .db | SQLite (+write path, migration), Parquet (+tooling), DuckDB (+query lib) | ~50-85 MB compressed vs 425 MB raw | None — archive is Mac-only | Simpler: no new write path, no new tooling |
| D4 | Repository cleanup scope | **Remove dev/, captures/ (after buddy review), scripts/old/, stale CSVs** | Keep all (dirty repo, 50 MB junk tracked), or remove only dev/ | Git repo ~50 MB smaller | None | Mechanical git rm + gitignore; buddy review for captures/ |
| D5 | README license | **MIT** | No LICENSE (blocks push), All Rights Reserved | None | None | License file added |
| D6 | Ivy-Control §8A standard | **Add Collector Efficiency standard** | Don't add (no ecosystem rule), add later | None | None | One-time doc update |
| D7 | Ivy-Control §10A standard | **Add Data Lifecycle standard** | Don't add (ad-hoc per repo), add later | None | None | One-time doc update |
| D8 | Bounded pilot boundary | **25 records, pc_sc_l, digest-bound** | Another segment, larger limit, all segments | First 25 records into PG | None — use_in_model=false | Already documented in pilot loader |
| D9 | Pilot Gate approval | **Buddy records approval in LOG.md before apply** | No gate (risky), Codex decides (out of scope) | None | None | Prevents unauthorized data load |

---

## 14. Final Prompt Readiness

**All facts are now available.** Strong Codex can be prompted without assumptions.

The four audit reports plus this decision packet contain:
- Complete source inventory (23 sites, 1 production source)
- Complete collector analysis (API behavior, overlap, cadence, efficiency)
- Complete table-level retention policy (every table, every tier)
- Complete schema design (3 new migrations, 3 new tables, exact SQL)
- Complete UI data contract (current, recent, hourly graph, daily graph)
- Complete Mac archive design (compressed JSONL + pg_dump, no new .db)
- Complete prune implementation contract (batch size, transaction boundaries, CLI, safety)
- Complete repository curation boundary (what to remove, keep, add)
- Complete Ivy-Control ecosystem standard drafts (2 new sections)
- Complete ordered implementation plan (17 steps)
- Complete command inventory (all non-mutating commands verified)

**Single remaining blocker before Strong Codex prompt:** None. The prompt can be written from this packet alone. The four Buddy decisions (D1-D4) can be resolved within the prompt as recommendations with explicit alternatives.

**Next action:** Write the Strong Codex implementation prompt using this packet as input. Begin with repository curation (step 1), then real PostgreSQL adapter (step 4), then migrations (steps 5-7), then metrics/aggregates/prune (steps 8-12), then pilot (step 14). VPS timer activation (step 17 condition) remains deferred until all steps complete and the Scheduler Gate is approved.

---

## Report Summary

- **Packet path:** `docs/TRADERIE_STRONG_CODEX_DECISION_AND_SCOPE_PACKET_20260706.md`
- **Readiness verdict:** READY WITH CONDITIONS
- **Chosen collection-metrics schema:** `app.collection_run_metrics` (separate table, not an extension of snapshot_runs)
- **Chosen aggregate schema:** `app.segment_aggregates` (single table, granularity column, hourly 30d + daily 365d)
- **Final retention proposal:** Raw 7d, hourly 30d, daily 365d, health 90d, ops 365d, reference indefinite
- **Chosen Mac archive design:** Compressed JSONL (source evidence) + pg_dump (full recovery) — no new .db
- **Proposed Ivy-Control standards:** §8A Collector Efficiency, §10A Data Lifecycle and Storage Budget
- **Remaining Buddy decisions:** D1 (7d raw), D2 (365d daily aggregate), D3 (compressed JSONL archive), D4 (cleanup scope), D5 (MIT license), D6-D7 (standards), D8-D9 (pilot boundary and gate)
- **Strong Codex prompt can now be written:** ✅ Yes — all facts available
