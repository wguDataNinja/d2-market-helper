# Backup and Restore — Traderie

**Version:** 1.0  
**Scope:** PostgreSQL dumps, file artifact manifests, restore drills  
**Based on:** SHARED-002 evidence standard, Codex Session 1 §7

**Latest implementation evidence:** See `docs/TRADERIE_POSTGRES_VPS_IMPLEMENTATION_AND_REMAINING_WORK_20260706.md` for the local Mac PG pilot, migration, validation, and lifecycle command results. This file remains the backup/restore runbook.

---

## 1. Backup Method

**Command:**
```bash
pg_dump --format=custom --compress=9 \
  --dbname="postgresql://traderie_backup@localhost/traderie" \
  --file="traderie_YYYYMMDDTHHMMSSZ.dump"
```

**Format:** `pg_dump --format=custom --compress=9` (compressed custom format, not plain SQL)

## 2. Filename Convention

| Artifact | Format | Example |
|----------|--------|---------|
| Dump | `traderie_YYYYMMDDTHHMMSSZ.dump` | `traderie_20260705T060000Z.dump` |
| Checksum | `traderie_YYYYMMDDTHHMMSSZ.dump.sha256` | `traderie_20260705T060000Z.dump.sha256` |
| Manifest | `traderie_YYYYMMDDTHHMMSSZ.manifest.json` | `traderie_20260705T060000Z.manifest.json` |

## 3. Checksum Format

```bash
sha256sum traderie_YYYYMMDDTHHMMSSZ.dump > traderie_YYYYMMDDTHHMMSSZ.dump.sha256
```

Contents: `<sha256_hex>  traderie_YYYYMMDDTHHMMSSZ.dump`

Verification command:
```bash
sha256sum -c traderie_YYYYMMDDTHHMMSSZ.dump.sha256
```

## 4. Manifest Schema

```json
{
  "project": "traderie",
  "database": "traderie",
  "dump_file": "traderie_20260705T060000Z.dump",
  "checksum_sha256": "<64 hex chars>",
  "created_at": "2026-07-05T06:00:00Z",
  "created_by_role": "traderie_backup",
  "postgres_version": "16.x",
  "schema_version": "1.0",
  "migration_version": "20260705_001_initial",
  "source_host_label": "ih-market-vps",
  "source_cluster_label": "main-pg16",
  "file_size_bytes": 1234567,
  "tables_included": [
    "app.segments",
    "app.items",
    "app.sources",
    "app.snapshot_runs",
    "app.completed_trades",
    "app.price_entries",
    "app.product_builds",
    "app.segment_rune_prices",
    "app.ruleset_breakdowns",
    "app.rune_registry",
    "health.health_runs",
    "health.workflow_status"
  ],
  "off_host_copy_status": "pending",
  "restore_drill_status": "not_performed",
  "retention_class": "pg_dump_daily",
  "notes_redacted": ""
}
```

## 5. Backup Locations

| Location | Path | Retention |
|----------|------|-----------|
| VPS local | `/home/scraper/backups/postgres/traderie/` | 7 daily + 4 weekly |
| Mac off-host | `/Users/buddy/projects/backups/postgres/traderie/` | 14 daily (cutover) → 7 daily + 4 weekly |
| Mac off-host (immutable) | `/Users/buddy/projects/backups/postgres/traderie/immutable/` | Never pruned |

Transport: `scp` over SSH (already encrypted). Post-copy verification via SHA-256.

## 6. Restore Procedure

```bash
pg_restore --format=custom --clean --if-exists \
  --dbname="postgresql://traderie_writer@localhost/traderie_restore" \
  traderie_YYYYMMDDTHHMMSSZ.dump
```

**Restore target:** Temporary local/Mac PostgreSQL database (e.g. `traderie_restore`), never production.

## 7. Restore-Evidence Checklist (18+ fields)

Based on SHARED-002 evidence standard:

| # | Field | Description | Pass/Fail |
|---|-------|-------------|-----------|
| 1 | Source inventory | List of backed-up artifacts (dump, checksum, manifest) | |
| 2 | Backup scope | Full `traderie` database, all schemas | |
| 3 | Dump method | `pg_dump --format=custom --compress=9` | |
| 4 | Timestamp | `YYYYMMDDTHHMMSSZ` format, matches file dates | |
| 5 | Source/destination identity | VPS host + Mac path verified | |
| 6 | File size | Dump size matches manifest `file_size_bytes` | |
| 7 | Checksum (SHA-256) | `sha256sum -c` passes on both VPS and Mac | |
| 8 | Off-host copy | SCP destination exists, checksum matches source | |
| 9 | Retention class | Manifest `retention_class` field populated | |
| 10 | Encryption/permissions | SSH transport; dump readable by backup group only | |
| 11 | Restore target | Temporary DB identity (host, port, dbname) | |
| 12 | Restore command | `pg_restore` command recorded (redacted) | |
| 13 | Restore validation | Row counts, timestamps, key queries pass | |
| 14 | Artifact parity | Trade count per segment matches pre-backup counts | |
| 15 | Rollback decision | Documented in LOG.md with restore-drill report path | |
| 16 | Evidence location | `logs/restore-drills/YYYY-MM-DD-traderie-restore.md` | |
| 17 | Responsible owner | Operator (Buddy) | |
| 18 | Gate approval | Backup/Restore Gate approval reference | |

**Traderie-specific evidence:**

| # | Field | Description | Pass/Fail |
|---|-------|-------------|-----------|
| 19 | Trade count per segment | Row count IN `app.completed_trades` GROUP BY segment_slug | |
| 20 | Product value parity | Latest `in_game_rune_values.json` values within 0.001 Ist of pre-backup | |
| 21 | Max `captured_at` | MAX(captured_at) per segment within 1 second of expected | |
| 22 | Unique listing count | COUNT(DISTINCT listing_id) per segment matches pre-backup | |

## 8. Restore-Drill Report Template

```markdown
# Restore Drill Report — Traderie

**Date:** YYYY-MM-DDTHH:MM:SSZ
**Operator:** Buddy
**Backup source:** /home/scraper/backups/postgres/traderie/traderie_YYYYMMDDTHHMMSSZ.dump
**Restore target:** localhost:5432/traderie_restore

## Evidence

- [ ] Checksum verified on source
- [ ] Checksum verified after SCP
- [ ] pg_restore exit code: 0
- [ ] Row counts per segment match pre-backup
- [ ] MAX(captured_at) per segment within 1s
- [ ] Product value parity within 0.001 Ist
- [ ] Unique listing count matches

## Row Counts

| Segment | Pre-backup | Restored | Match |
|---------|-----------|----------|-------|
| pc_sc_l | N | N | ✅ |
| pc_sc_nl | N | N | ✅ |
| pc_hc_l | N | N | ✅ |
| pc_hc_nl | N | N | ✅ |

## Product Value Parity

| Rune | Pre-backup (Ist) | Restored (Ist) | Delta |
|------|-----------------|----------------|-------|
| Jah  | X.XXX           | X.XXX          | 0.000 |

## Result

- **PASS / FAIL**
- **Gate approval:** Backup/Restore Gate reference
- **LOG.md entry:** [link]
```

## 9. Gate Annotations

| Operation | Gate | Evidence artifact |
|-----------|------|-------------------|
| Backup (live) | Backup/Restore | Dump + checksum + manifest; LOG.md entry |
| Backup (archive copy) | Backup/Restore | Off-host copy checksum verification |
| Restore drill | Backup/Restore | Restore-drill report in `logs/restore-drills/` |
| Pruning (any class) | Backup/Restore + Destructive Operation | Dry-run report + backup evidence + restore evidence |
| Cutover (PG→primary) | Backup/Restore + Authority | Immutable dump + restore drill evidence |
| Retire immutable artifacts | Destructive Operation | Buddy explicit decision in LOG.md |
