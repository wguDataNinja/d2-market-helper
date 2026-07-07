# Retention Policy — Traderie

**Version:** 1.0  
**Scope:** PostgreSQL dumps, raw snapshots, normalized snapshots, history JSONL, derived products, research artifacts  
**Gates:** Backup/Restore Gate, Destructive Operation Gate

**Latest implementation evidence:** See `docs/TRADERIE_POSTGRES_VPS_IMPLEMENTATION_AND_REMAINING_WORK_20260706.md` for the key-limited pilot prune dry-run/apply, archive audit proof, and health retention output. This file remains the policy reference.

---

## 1. Retention-Class Definitions

| Class | Artifacts | Retention | Pruning trigger | Notes |
|-------|-----------|-----------|----------------|-------|
| `pg_dump_daily` | PostgreSQL dumps | 7 daily (VPS) | Age > 7 days, keep newest 7 | 14 daily on Mac during active cutover |
| `pg_dump_weekly` | PostgreSQL dumps | 4 weekly (VPS) | Keep Sunday dump, prune others | Sunday checkpoint, keep 4 most recent |
| `raw_snapshot` | `data/snapshots/raw/traderie/{seg}/{ts}/response.json` | 14 days after PG parity | Age > 14 days, unless immutable | Covers all 4 segments |
| `normalized_snapshot` | `data/snapshots/normalized/traderie/{seg}/{ts}.json` | 30 days after PG parity | Age > 30 days, or align with raw if disk pressure | |
| `history_jsonl` | `data/history/traderie/{seg}/*.jsonl` | Indefinite (compressed cold archive) | Never pruned automatically | Compress to `.jsonl.gz` when archive budget requires |
| `product_json` | `data/products/*.json` | Git / product artifact policy | Managed by version control | Keep latest + history per Git |
| `research_csv_json` | `data/research/*`, `data/prices/*.csv`, `data/raw/*` | Latest + 7 days after product parity | Age > 7 days post-parity | |
| `immutable_migration` | Pre-migration, cutover, pre-destructive-op snapshots | Never pruned | Only on explicit Buddy retirement | Immutable class — requires Destructive Operation Gate to retire |
| `immutable_cutover` | Cutover baseline snapshots | Never pruned | Only on explicit Buddy retirement | Frozen at authority-transfer point |

## 2. Retention Schedule (Post-PG-Parity)

**VPS** (`/home/scraper/backups/postgres/traderie/`):
- Daily dump: keep newest 7
- Weekly dump (Sunday): keep newest 4
- Raw snapshots: keep newest 14 days
- Normalized snapshots: keep newest 30 days (or align with raw under disk pressure)
- History JSONL: keep indefinitely (compressed archive)

**Mac** (`/Users/buddy/projects/backups/postgres/traderie/`):
- Daily dump: keep 14 during active cutover, then 7
- Weekly dump: keep 4
- Monthly dump: keep latest (post-cutover steady state)

## 3. Proposed Archive Layout

```
VPS: /home/scraper/backups/postgres/traderie/
  pg_dump/
    daily/
      traderie_YYYYMMDDTHHMMSSZ.dump
      traderie_YYYYMMDDTHHMMSSZ.dump.sha256
      traderie_YYYYMMDDTHHMMSSZ.manifest.json
    weekly/
      traderie_YYYYMMDDTHHMMSSZ.dump
      traderie_YYYYMMDDTHHMMSSZ.dump.sha256
      traderie_YYYYMMDDTHHMMSSZ.manifest.json
    immutable/
      traderie_YYYYMMDDTHHMMSSZ.dump
      traderie_YYYYMMDDTHHMMSSZ.dump.sha256
      traderie_YYYYMMDDTHHMMSSZ.manifest.json
  artifacts/
    snapshots_raw/
    snapshots_normalized/
    history/

Mac: /Users/buddy/projects/backups/postgres/traderie/
  pg_dump/
    daily/
    weekly/
    immutable/
  artifacts/
    snapshots_raw/
    snapshots_normalized/
    history/
```

## 4. Dry-Run Pruning Report Template

```
=== Traderie Dry-Run Pruning Report ===
Date: {YYYY-MM-DDTHH:MM:SSZ}
Mode: dry-run (no files altered)

Retention class: raw_snapshot
  Files eligible: {N}
  Disk to be reclaimed: {SIZE}
  Oldest retained: {DATE}
  Newest retained: {DATE}
  Examples:
    {path} (age {days}d)
    {path} (age {days}d)

Retention class: normalized_snapshot
  Files eligible: {N}
  Disk to be reclaimed: {SIZE}

Retention class: pg_dump_daily (VPS)
  Files eligible: {N}
  Disk to be reclaimed: {SIZE}
  Keeping:
    {path} (newest 7)

Retention class: research_csv_json
  Files eligible: {N}
  Disk to be reclaimed: {SIZE}

Immutable class: snapshot_migration_{Y-m-d}
  Files: {N}
  Status: FROZEN — not eligible for pruning

=== Summary ===
Total disk used by class: {SIZE}
Total reclaimable: {SIZE}
Total immutable: {SIZE}
Classes with eligible files: {N}
After pruning estimate: {SIZE} consumed

=== Gates Required ===
Before execution:
  [ ] Backup/Restore Gate — verify latest backup is < 24h old
  [ ] Restore drill evidence exists — restore-drill-report-{DATE}.md
  [ ] Destructive Operation Gate — explicit approval required

To confirm pruning, rerun with --apply after:
  1. Backup/Restore Gate approval
  2. Destructive Operation Gate approval
  3. All three sign-offs documented in LOG.md
```

## 5. Gate Annotations

| Operation | Gate required | Evidence needed |
|-----------|---------------|-----------------|
| Live backup | Backup/Restore | Dump path, checksum, manifest, off-host copy |
| Archive (compress/move) | Backup/Restore | Manifest update, checksum re-verification |
| Restore drill | Backup/Restore | Row counts, timestamps, key queries, command transcript |
| Dry-run pruning | None (read-only) | Report output |
| Apply pruning | Backup/Restore + Destructive Operation | Dry-run report, backup evidence, restore drill evidence, explicit approval |
| Retire immutable class | Destructive Operation | Buddy explicit retirement decision documented in LOG.md |
