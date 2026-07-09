# Traderie — Scheduler Cutover Packet

**Date:** 2026-07-09
**Scope:** Workstream I — future Codex execution packet for final one-writer cutover.

**Status:** Plan / execution packet only. Do not execute until all preconditions are proven.

---

## 1. Preconditions (must be proven before cutover)

| # | Precondition | Evidence |
|---|---|---|
| 1 | VPS PostgreSQL installed, database `traderie` created, roles provisioned | Codex VPS task report |
| 2 | All 17 migrations applied on VPS; validation passes | Migration output + validation SQL |
| 3 | Traderie checkout on VPS at approved SHA `b3b70a0`; `git status --porcelain` is clean | SHA check + status command |
| 4 | Environment file `/home/scraper/config/traderie.env` configured; no secrets in Git | File permissions + content review |
| 5 | Mac backup taken and verified | Backup manifest + checksum |
| 6 | Bounded manual proof completed (see `repos/traderie/PHASE_B_CODEX_PACKET.md` and `docs/bounded-manual-proof.md`) | Proof report |
| 7 | Rollback procedure verified on VPS | Rollback drill output |
| 8 | Health export verified — v2 payload passes schema validation | Schema validation |
| 9 | Backup/restore proof completed on VPS — restore to isolated database passes | Restore drill report |
| 10 | Buddy explicitly approves cutover (Scheduler Gate and Database Authority Gate) | Approval record |

---

## 2. Mac scheduler inventory and disable steps

### Current Mac authority

| Scheduler | Status | Command to disable |
|---|---|---|
| launchd `com.buddy.traderie.snapshot.plist` | Disabled/not loaded (deprecated) | `launchctl bootout gui/501/com.buddy.traderie.snapshot 2>/dev/null` |
| launchd backup (legacy) | Unknown/unused | Document if found |
| Manual runs | Only active path | No automation to disable |

### Disable steps

```bash
# 1. Verify current launchd state
launchctl list | grep traderie

# 2. Unload/disbale any active launchd jobs
launchctl bootout gui/501/com.buddy.traderie.snapshot 2>/dev/null || true
launchctl bootout gui/501/com.buddy.traderie.backup 2>/dev/null || true

# 3. Confirm no Mac processes are actively writing
ps aux | grep snapshot_traderie | grep -v grep

# 4. Record evidence
launchctl list | grep traderie > /tmp/mac_scheduler_before_cutover.txt
```

---

## 3. VPS scheduler install/enable steps

```bash
# 1. Copy unit files (already in Git checkout)
sudo cp deploy/systemd/traderie-ingest-snapshot.service /etc/systemd/system/
sudo cp deploy/systemd/traderie-ingest-snapshot.timer /etc/systemd/system/
sudo cp deploy/systemd/traderie-process-products.service /etc/systemd/system/
sudo cp deploy/systemd/traderie-process-products.timer /etc/systemd/system/
sudo cp deploy/systemd/traderie-validate-products.service /etc/systemd/system/
sudo cp deploy/systemd/traderie-validate-products.timer /etc/systemd/system/
sudo cp deploy/systemd/traderie-check-health.service /etc/systemd/system/
sudo cp deploy/systemd/traderie-check-health.timer /etc/systemd/system/
# Backup and retain remain inert (manual trigger only)
sudo cp deploy/systemd/traderie-backup-postgres.service /etc/systemd/system/
sudo cp deploy/systemd/traderie-backup-postgres.timer /etc/systemd/system/
sudo cp deploy/systemd/traderie-retain-snapshots.service /etc/systemd/system/
sudo cp deploy/systemd/traderie-retain-snapshots.timer /etc/systemd/system/

# 2. Reload systemd
sudo systemctl daemon-reload

# 3. Enable and start timers (one at a time, with verification)
sudo systemctl enable traderie-ingest-snapshot.timer
sudo systemctl start traderie-ingest-snapshot.timer
```

---

## 4. Mutual-exclusion checks

Before enabling any VPS timer:

```bash
# Check no Mac launchd jobs are running
launchctl list | grep traderie

# Check no VPS timer is already active (from prior attempt)
systemctl list-timers --all | grep traderie

# Check lock directory doesn't contain stale locks
ls -la /home/scraper/data/traderie/.locks/

# Check no snapshot process is running
pgrep -f snapshot_traderie
```

---

## 5. Cutover order

1. Take final Mac backup and verify.
2. Disable Mac launchd jobs (if any found active).
3. Take pre-cutover row counts on Mac PostgreSQL.
4. Copy unit files to VPS and daemon-reload.
5. Enable health timer first — verify health output is valid.
6. Enable snapshot timer — wait for first scheduled run.
7. Verify snapshot output, row counts, and health.
8. Enable product process timer — verify product files are regenerated.
9. Enable validate timer — verify validation passes.
10. Enable backup timer — verify backup runs.
11. Enable retain timer — verify dry-run prune produces no unexpected deletions.

---

## 6. Maximum allowed overlap

No overlap is allowed. If any Mac writer is active when a VPS timer fires, the cutover must be rolled back.

Maximum acceptable dual-write window: **0 seconds**. The Mac must be confirmed quiet before the first VPS timer fires.

---

## 7. Natural-run observation window

After enabling the snapshot timer, observe at least **3 natural timer-triggered runs** (18 hours at 4x daily) before considering cutover stable.

Each run must produce:
- Collection_run_metrics with `status: completed`
- Row count increases within expected range (~22K/day)
- No error_class entries
- Health payload with `status: ok`

---

## 8. Health and data-quality checks

| Check | Frequency | Action on failure |
|---|---|---|
| Health payload `status` is `ok` | After each run | Investigate, roll back if persistent |
| Freshness < 21600 seconds (6h cadence) | After each run | Warn if stale |
| `incident_state` is `none` | After each run | Investigate failed runs |
| Row count consistency | Daily | Parity check against expected growth |
| `deployed_revision` matches approved SHA | Per health check | Flag drift |
| `schema_version` is 17 | Per health check | Flag migration drift |
| Backup completes within 24h | Daily | Warn if backup overdue |
| Disk usage < 85% | Per health check | Warn if critical |

---

## 9. Duplicate-run detection

```sql
-- Check for overlapping runs within same segment+workflow
SELECT workflow, COUNT(*) AS run_count,
       MIN(started_at) AS first_start, MAX(started_at) AS last_start
FROM health.health_runs
WHERE started_at > now() - interval '24 hours'
GROUP BY workflow
HAVING COUNT(*) > 4;  -- Expected: 4 snapshot runs/day max
```

```bash
# Check for concurrent processes on VPS
ps aux | grep snapshot_traderie | grep -v grep | wc -l
```

---

## 10. Abort thresholds

| Condition | Action |
|---|---|
| Any Mac writer found active after disable step | Roll back immediately |
| First VPS snapshot fails | Roll back immediately |
| Row count delta between Mac and VPS > 0 after 24h | Roll back, investigate |
| Health payload missing required v2 fields | Roll back |
| `deployed_revision` mismatch | Roll back |
| Disk usage exceeds 85% | Roll back |
| Backup not created within 24h | Warn, do not roll back yet |
| 3+ consecutive failed runs | Roll back |

---

## 11. Rollback sequence (restoring Mac authority)

```bash
# 1. Disable VPS timers
sudo systemctl stop traderie-ingest-snapshot.timer
sudo systemctl disable traderie-ingest-snapshot.timer
sudo systemctl stop traderie-process-products.timer
sudo systemctl disable traderie-process-products.timer
sudo systemctl stop traderie-validate-products.timer
sudo systemctl disable traderie-validate-products.timer
sudo systemctl stop traderie-check-health.timer
sudo systemctl disable traderie-check-health.timer

# 2. Stop any running services
sudo systemctl stop traderie-ingest-snapshot.service

# 3. Remove unit files
sudo rm /etc/systemd/system/traderie-*.service
sudo rm /etc/systemd/system/traderie-*.timer
sudo systemctl daemon-reload

# 4. Restore Mac authority (re-enable launchd if needed)
# launchctl bootstrap gui/501 /path/to/com.buddy.traderie.snapshot.plist

# 5. Restore environment file to previous state
# cp /home/scraper/config/traderie.env.bak /home/scraper/config/traderie.env

# 6. Record rollback evidence
systemctl list-timers --all | grep traderie
```

---

## 12. Stabilization evidence

After cutover, capture and archive:

- Systemd timer list (enabled + next run time)
- Health payload (v2 JSON)
- Row counts (all tables)
- `deployed_revision` from Git
- `schema_version` from migration table
- Backup manifest + checksum
- Disk usage
- Screenshot or log of first 3 natural timer-triggered runs

Evidence stored in Mac archive under `backups/traderie/cutover/YYYY-MM-DD/`.
