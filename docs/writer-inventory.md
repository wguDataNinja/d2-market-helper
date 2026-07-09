# Traderie — Writer and Scheduler Inventory

**Date:** 2026-07-09
**Scope:** Workstream B — every process that can write or mutate Traderie state.

---

## Writer authority matrix

| # | Writer / Scheduler | Host | Entry point | Schedule | Mutations | Idempotent | Safe for VPS? | Mac-only? | Authority |
|---|---|---|---|---|---|---|---|---|---|
| W1 | `snapshot_traderie.py` (capture) | Mac (current), VPS (future) | `scripts/snapshot_traderie.py` | On demand or 4x daily | Writes raw JSONL, history JSONL, DB `app.completed_trades`, `app.price_entries`, `app.collection_run_metrics` | Yes — upsert by `observation_key` | Yes | No — target is VPS | **Authoritative** |
| W2 | `traderie_aggregate_generation.py` | Mac (current), VPS (future) | `scripts/traderie_aggregate_generation.py` | After snapshot | Writes `app.segment_aggregates`, `app.snapshot_runs` | Yes — upsert by segment/timestamp | Yes | No — target is VPS | **Authoritative** |
| W3 | `regenerate_products.sh` | Mac (any) | `scripts/regenerate_products.sh` | On demand, post-snapshot | Updates `data/products/*.json` files | Yes | Yes | No | **Authoritative** |
| W4 | `traderie_prune.py` | Mac (current), VPS (future) | `scripts/traderie_prune.py` | Weekly (on demand) | Deletes expired records from `app.completed_trades`, `app.segment_aggregates`; writes `app.prune_audit`, `archive.prune_archive_audit` | Yes — dry-run default, bounded key list | Yes | No | **Authoritative** |
| W5 | `traderie_health_export.py --pg` | Mac (current), VPS (future) | `scripts/traderie_health_export.py` | On demand or 30-min timer | Writes `health.health_runs` | Yes — insert per run | Yes | No — target is VPS | **Advisory** (health reporting, not production data) |
| W6 | Mac `launchd` snapshot wrapper | Mac | `launchd/com.buddy.traderie.snapshot.plist` | Manual/Future | Launches W1 | N/A (launcher) | No — Mac-specific | Yes | **Deprecated** (being replaced by VPS systemd) |
| W7 | VPS `systemd` snapshot service/timer | VPS (future) | `deploy/systemd/traderie-ingest-snapshot.*` | 4x daily (inert) | Launches W1 via `run_traderie_snapshot.sh` | N/A (launcher) | Yes (planned) | No | **Planned** — inert, not installed |
| W8 | VPS `systemd` product process service/timer | VPS (future) | `deploy/systemd/traderie-process-products.*` | Daily 06:00 (inert) | Launches W3 via `run_traderie_snapshot.sh` | N/A (launcher) | Yes (planned) | No | **Planned** — inert, not installed |
| W9 | VPS `systemd` validate service/timer | VPS (future) | `deploy/systemd/traderie-validate-products.*` | Daily 06:30 (inert) | No DB writes — validates product files | N/A (validator) | Yes (planned) | No | **Planned** — inert, not installed |
| W10 | VPS `systemd` health check service/timer | VPS (future) | `deploy/systemd/traderie-check-health.*` | Every 30 min (inert) | Launches W5 | N/A (launcher) | Yes (planned) | No | **Planned** — inert, not installed |
| W11 | VPS `systemd` backup service/timer | VPS (future) | `deploy/systemd/traderie-backup-postgres.*` | Daily 07:00 (inert) | `pg_dump` to backup directory | N/A (backup) | Yes (planned) | No | **Planned** — inert, not installed |
| W12 | VPS `systemd` retain service/timer | VPS (future) | `deploy/systemd/traderie-retain-snapshots.*` | Weekly Sun 03:00 (inert) | Launches W4 with dry-run default | Yes (dry-run) | Yes (planned) | No | **Planned** — inert, not installed |
| W13 | `traderie_pilot_loader.py` | Mac (adhoc) | `scripts/traderie_pilot_loader.py` | Manual only | Inserts seed data into `app.completed_trades`, `app.price_entries` | Yes — upsert | Yes (one-shot) | No — target is VPS | **Advisory** — one-time bootstrap |
| W14 | `traderie_pg_adapter.py` | Mac (adhoc) | Imported by other scripts | On demand | Writes via upsert path | Yes | Yes | No | **Advisory** — storage layer, not independent |
| W15 | Manual SQL / DBeaver | Mac (adhoc) | Any SQL client | Manual | Any mutation (uncontrolled) | Manual | N/A | Yes | **Uncontrolled** — operators only |
| W16 | Mac backup script | Mac | `run_traderie_backup.sh` | On demand | `pg_dump` to backup directory | Yes | No — Mac-only | Yes | **Authoritative** — Mac backup authority |
| W17 | Mac `launchd` backup | Mac | launchd (legacy) | Unknown | `pg_dump` | Unknown | No — Mac-only | Yes | **Deprecated** — replaced by manual backup |

---

## One-writer authority

Currently:

- **Mac** is the authoritative writer for snapshots, aggregates, product generation, and prune.
- **Mac** is the backup authority.
- **VPS** has no writer, no scheduler, no database.
- The `TraderieTools` userscript is **read-only** — it never writes to the Traderie API, Traderie database, or any Traderie file system. It reads `rune_prices.json` from GitHub and stores browser-local state in `localStorage`.

---

## Duplicate-writer risks

| Risk | Scenario | Mitigation |
|---|---|---|
| Mac + VPS both running snapshots | Cutover period where both are active | `flock` lock files prevent concurrent runs on same host. Shadow mode has separate timers. Mac launchd must be disabled before VPS systemd is enabled. |
| Manual SQL mutations | Operator writes directly via DBeamer | Detected by health checks, parity reports, and drift detection. Not automated — requires operator discipline. |
| Userscript writing to Traderie API | Userscript makes unauthorized `GM_xmlhttpRequest` POST | Userscript uses only `GET` from `raw.githubusercontent.com`. No Traderie API endpoints. Code reviewed. |

---

## Scheduler authority

| Current | Future |
|---|---|
| No active Mac scheduler (launchd disabled/deprecated) | VPS systemd timers (inert, not installed) |
| No active VPS scheduler | One-writer authority after cutover packet approval |
| Manual runs only | 4x daily snapshot, daily product/validate, 30-min health, daily backup, weekly retain |

---

## Unknowns

| Item | Status |
|---|---|
| Whether any shadow/test/temporary scheduler exists on Mac | No evidence found. Launchd inventory shows only snapshot and backup entries. |
| Whether any cron job exists | No evidence of `crontab` entries for Traderie. |
| Whether any other machine writes to the Traderie database | No — Mac PostgreSQL is the only instance. VPS has no PostgreSQL. |
| Userscript side-effects on `traderie.com` data | Userscript is read-only in the browser. No API mutations. No file system writes beyond `localStorage`. |
