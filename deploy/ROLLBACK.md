# Traderie — Rollback Plan

## 1. Disable Timer (Stop Scheduled Runs)

```bash
# Disable timer (prevents future activation)
sudo systemctl disable traderie-ingest-snapshot.timer
sudo systemctl disable traderie-process-products.timer
sudo systemctl disable traderie-validate-products.timer
sudo systemctl disable traderie-check-health.timer
sudo systemctl disable traderie-backup-postgres.timer
sudo systemctl disable traderie-retain-snapshots.timer

# Stop timer (prevents next scheduled run)
sudo systemctl stop traderie-ingest-snapshot.timer
sudo systemctl stop traderie-process-products.timer
sudo systemctl stop traderie-validate-products.timer
sudo systemctl stop traderie-check-health.timer
sudo systemctl stop traderie-backup-postgres.timer
sudo systemctl stop traderie-retain-snapshots.timer
```

## 2. Revert to Mac launchd Scheduling

After disabling systemd timers, ensure Mac launchd jobs are re-enabled:

```bash
# Verify launchd jobs are loaded
launchctl list | grep traderie

# If missing, bootstrap:
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.buddy.traderie.snapshot-traderie.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.buddy.traderie.regenerate-products.plist
```

Expected jobs:
- `com.buddy.traderie.snapshot-traderie` — 4x daily (05:00, 11:00, 17:00, 23:00)
- `com.buddy.traderie.regenerate-products` — daily 06:00

## 3. Remove Systemd Unit Files (Optional)

```bash
# Remove from filesystem (reverse of cp/ln)
sudo rm /etc/systemd/system/traderie-ingest-snapshot.service
sudo rm /etc/systemd/system/traderie-ingest-snapshot.timer
sudo rm /etc/systemd/system/traderie-process-products.service
sudo rm /etc/systemd/system/traderie-process-products.timer
sudo rm /etc/systemd/system/traderie-validate-products.service
sudo rm /etc/systemd/system/traderie-validate-products.timer
sudo rm /etc/systemd/system/traderie-check-health.service
sudo rm /etc/systemd/system/traderie-check-health.timer
sudo rm /etc/systemd/system/traderie-backup-postgres.service
sudo rm /etc/systemd/system/traderie-backup-postgres.timer
sudo rm /etc/systemd/system/traderie-retain-snapshots.service
sudo rm /etc/systemd/system/traderie-retain-snapshots.timer

sudo systemctl daemon-reload
```

## 4. Revert Wrapper Script Changes

If wrapper scripts were modified for VPS paths:

```bash
# Restore from Git working tree (discard VPS-specific changes)
git checkout -- scripts/run_traderie_snapshot.sh
git checkout -- scripts/regenerate_products.sh
git checkout -- scripts/run_traderie_validate.sh
git checkout -- scripts/run_traderie_backup.sh
```

## 5. Restore Environment File

```bash
# If env file was modified
cp /home/scraper/config/traderie.env.bak /home/scraper/config/traderie.env
```

## 6. Recovery Verification

After rollback:

```bash
# Verify launchd pipeline is running
launchctl list | grep traderie

# Run a manual snapshot to confirm
cd "${TRADERIE_REPO_DIR:-/home/scraper/apps/traderie}"
python3 scripts/collection_status.py --json

# Check products are fresh
ls -la data/products/in_game_rune_values.json
```

## 7. Data Recovery (if PG was active)

If PostgreSQL was in use and needs to be rolled back:

```bash
# Restore from latest backup (requires Backup/Restore Gate)
pg_restore --format=custom --dbname=postgresql://127.0.0.1:5432/traderie \
  /home/scraper/backups/postgres/traderie/latest.dump

# Or re-seed from JSONL history files
python3 scripts/build_traderie_dataset_from_history.py --write-research
```

## 8. When to Roll Back

Roll back immediately if:
- Ingest snapshot service consistently fails (non-zero exit for softcore)
- Product regeneration produces stale or incorrect output
- Cloudscraper/browser compatibility issues on VPS
- Disk runs low (below 20% free)
- PG adapter causes data divergence during shadow mode
- Any Scheduler Gate or Backup/Restore Gate violation detected

## 9. Gates After Rollback

Rollback does NOT reset Gates:
- **Scheduler Gate** remains required before re-enabling any timer
- **Backup/Restore Gate** remains required before backup/retention operations
- **Database Authority Gate** remains required before PG adapter enablement
