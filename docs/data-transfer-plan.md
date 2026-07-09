# Mac-to-VPS Data Transfer and Parity Plan

**Date:** 2026-07-09
**Scope:** Workstream D — deterministic Mac-to-VPS data transfer without data loss or split-brain.

**Status:** Plan only. Do not execute until PostgreSQL foundation and VPS checkout exist.

---

## 1. Source datasets and authoritative locations

| Dataset | Source | Format | Size | Notes |
|---|---|---|---|---|
| PostgreSQL dump | Mac PostgreSQL (`traderie` database) | `pg_dump -Fc -Z 9` | ~9.7 MB | Full database dump including schemas, data, roles (if pg_dumpall --globals) |
| Product JSONs | `data/products/*.json` | JSON | ~529 KB (4 files) | Deterministic exports, regenerable from DB |
| Raw snapshots | `data/raw/` | JSONL | Varies | Needs bounded retention; not required for VPS bootstrap |
| History JSONL | `data/history/` | JSONL (compressed) | Varies | Cold archive; not transferred to VPS operational storage |

---

## 2. Export format

```bash
pg_dump "postgresql://traderie_backup@localhost:5432/traderie" \
  --format=custom --compress=9 \
  --file=traderie_YYYYMMDD_HHMMSS.dump
```

Checksum: `sha256sum traderie_YYYYMMDD_HHMMSS.dump > traderie_YYYYMMDD_HHMMSS.dump.sha256`

---

## 3. Checksums and row counts

Pre-export row counts (captured before dump):

```sql
SELECT 'completed_trades' AS tbl, COUNT(*) FROM app.completed_trades
UNION ALL SELECT 'price_entries', COUNT(*) FROM app.price_entries
UNION ALL SELECT 'collection_run_metrics', COUNT(*) FROM app.collection_run_metrics
UNION ALL SELECT 'segment_aggregates', COUNT(*) FROM app.segment_aggregates
UNION ALL SELECT 'prune_audit', COUNT(*) FROM app.prune_audit
UNION ALL SELECT 'snapshot_runs', COUNT(*) FROM app.snapshot_runs
UNION ALL SELECT 'segment_rune_prices', COUNT(*) FROM app.segment_rune_prices
UNION ALL SELECT 'product_builds', COUNT(*) FROM app.product_builds
UNION ALL SELECT 'health_runs', COUNT(*) FROM health.health_runs
UNION ALL SELECT 'segments', COUNT(*) FROM app.segments
UNION ALL SELECT 'items', COUNT(*) FROM app.items
UNION ALL SELECT 'sources', COUNT(*) FROM app.sources
UNION ALL SELECT 'traderie_migrations', COUNT(*) FROM app.traderie_migrations;
```

Post-restore counts must match pre-export counts exactly.

---

## 4. Timestamp and timezone handling

- All timestamps in the Traderie schema use `timestamptz` (PostgreSQL with timezone).
- Dump format preserves timezone.
- No conversion needed — both Mac and VPS run in UTC-aligned environments.
- Confirmed by checking column types: `SELECT table_schema, table_name, column_name, data_type FROM information_schema.columns WHERE data_type LIKE '%time%' ORDER BY table_schema, table_name;`

---

## 5. Null and enum normalization

- All nullable columns use SQL null.
- Status enums (`ok`, `warn`, `fail`, `skip`) are consistent.
- Boolean columns use true/false.
- No custom enum types exist — all enums are text/varchar with application-level constraints.

---

## 6. Import ordering

```bash
# 1. Create database and roles on VPS (Codex: VPS task)
# 2. Apply 17 migrations in order (db/migrations/)
# 3. Run validation SQL (db/validation/999_full_validation.sql)
# 4. pg_restore the data dump
# 5. Re-run validation
```

Migration-first, restore-second ordering ensures the schema exists before data import.

---

## 7. Duplicate handling

- `pg_restore --clean --if-exists` will drop and recreate objects.
- `ON CONFLICT` upsert logic exists in application code but not needed for dump-based restore.
- After restore, run duplicate detection:
  ```sql
  SELECT observation_key, COUNT(*)
  FROM app.completed_trades
  GROUP BY observation_key
  HAVING COUNT(*) > 1;
  ```

---

## 8. Referential-integrity checks

Run after restore:

```sql
-- Check foreign keys are valid
SELECT COUNT(*) AS broken_fks
FROM (
  SELECT 1 FROM app.price_entries pe
  LEFT JOIN app.completed_trades ct ON ct.trade_observation_id = pe.trade_id
  WHERE ct.trade_observation_id IS NULL
) broken;
```

Also run `db/validation/999_full_validation.sql` which covers 17+ structural checks.

---

## 9. Parity queries

After both Mac and VPS databases have identical data:

| Check | Query |
|---|---|
| Row count | Compare pre-export row count table with post-restore counts |
| PK comparison | `SELECT observation_key FROM app.completed_trades ORDER BY observation_key` — diff the full key list |
| Date range | `SELECT MIN(captured_at), MAX(captured_at) FROM app.completed_trades` |
| Segment coverage | `SELECT segment_slug, COUNT(*) FROM app.completed_trades GROUP BY segment_slug` |
| Reject records | No dedicated reject table — all accepted data paths are idempotent |
| Derived/export | Product JSONs are regenerable, not compared directly |

---

## 10. Expected tolerances

| Metric | Tolerance | Action if exceeded |
|---|---|---|
| Row count delta | 0 | Abort — do not proceed |
| PK delta | 0 | Abort — do not proceed |
| Date range delta | 0 | Warn — investigate |
| Segment coverage | Must include all 4 segments | Abort if segment missing |
| Duplicate count | 0 | Investigate before proceeding |
| Broken FK count | 0 | Abort |

---

## 11. Failure thresholds

| Condition | Action |
|---|---|
| Source dump file size < 1 MB | Abort — likely empty dump |
| Checksum mismatch after transfer | Retry transfer; abort on second failure |
| `pg_restore` exit code != 0 | Abort — review error |
| Row count delta > 0 | Abort — parity failed |
| Broken FK > 0 | Abort — data integrity issue |
| Validation SQL returns failures | Abort — schema mismatch |

---

## 12. Abort conditions

Abort immediately if:

- Pre-export row count cannot be captured.
- Source Mac PostgreSQL is unreachable.
- Target VPS PostgreSQL is unreachable.
- Migration order validation fails.
- Any parity check exceeds tolerance.
- Any backup cannot be verified.

On abort: keep Mac data untouched. Delete or truncate the VPS target database. Document the failure. Re-plan transfer.

---

## 13. Rollback behavior

- Mac data is never deleted — always the authoritative fallback.
- VPS target database can be dropped and recreated if transfer fails.
- Pre-transfer Mac backup is taken and verified before any VPS work.
- Mac remains the writer during transfer — no writes are frozen.

---

## 14. Write freeze during transfer

Mac writes should be paused only during the final sync before cutover, not during routine transfer for the initial VPS bootstrap.

For initial bootstrap: run the snapshot after the last Mac write, produce the dump, and transfer. No Mac write freeze needed because the Mac is the single writer and the dump is a point-in-time snapshot.

---

## 15. One-writer authority preservation

- Mac remains the sole writer before, during, and after initial data transfer.
- VPS receives only a read-only snapshot.
- No VPS writer role is configured or enabled during transfer.
- Cutover (disabling Mac writer, enabling VPS writer) is a separate, later action covered by `docs/scheduler-cutover-packet.md`.
