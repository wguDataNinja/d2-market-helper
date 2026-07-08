# Traderie — VPS Deployment

**Status:** INERT — do not install or enable without Scheduler Gate approval.

**Current implementation plan:** The current VPS capacity evidence and deployment plan are in `repos/traderie/PHASE_B_CODEX_PACKET.md` in the `ivy-control-vps` repository. VPS PostgreSQL is the operational target; Mac PostgreSQL is the archive/backup/restore authority.

## Architecture

Traderie runs as a set of `oneshot` systemd services triggered by systemd timers on the VPS (`ih-market-vps`, `46.224.146.164`). All services run as the `scraper` user.

## Service Inventory

| Service | Timer Schedule | Timeout | Lock | Purpose |
|---------|---------------|---------|------|---------|
| `traderie-ingest-snapshot` | 4x daily | 5 min | `snapshot.lock` | Fetch completed trades from Traderie API (4 segments) |
| `traderie-process-products` | Daily 06:00 | 5 min | `process-products.lock` | Rebuild product JSONs from accumulated history |
| `traderie-validate-products` | Daily 06:30 | 5 min | `validate-products.lock` | Run all product validators |
| `traderie-check-health` | Every 30 min | 2 min | `check-health.lock` | Produce sanitized health JSON export |
| `traderie-backup-postgres` | Daily 07:00 | 30 min | `backup-postgres.lock` | INERT — pg_dump + checksum + manifest |
| `traderie-retain-snapshots` | Weekly Sun 03:00 | 5 min | `retain-snapshots.lock` | INERT — prune expired artifacts |

## Prerequisites

### VPS

- User `scraper` exists on `ih-market-vps`
- Repository checked out at `/home/scraper/apps/traderie`
- Python virtual environment at `/home/scraper/apps/traderie/.venv`
- Environment file at `/home/scraper/config/traderie.env` (see `env.example`)
- Lock directory: `/home/scraper/data/traderie/.locks/` (created by ExecStartPre)
- Health output directory: `$(dirname ${TRADERIE_HEALTH_OUTPUT})`
- Backup directory: `${TRADERIE_BACKUP_ROOT}`

### Wrapper Scripts

These scripts must exist on VPS (adapt from Mac counterparts):

| Service | Script | Source |
|---------|--------|--------|
| ingest-snapshot | `scripts/run_traderie_snapshot.sh` | VPS paths, systemd lock owned by unit |
| process-products | `scripts/regenerate_products.sh` | Adapt from existing (replace Mac paths with VPS paths) |
| validate-products | `scripts/run_traderie_validate.sh` | Create — runs all 4 validators + collection_status.py --json |
| check-health | `scripts/traderie_health_export.py` | Sanitized health export; `--pg` records one health row |
| backup-postgres | `scripts/run_traderie_backup.sh` | pg_dump + SHA-256 checksum + manifest (INERT) |
| retain-snapshots | Referenced via `traderie_disk_inventory.py` | Already exists — dry-run default (INERT) |

### Database

VPS PostgreSQL is the operational authority. The PostgreSQL adapter (`TRADERIE_PG_ADAPTER_ENABLED=true`) is used when PG is available; services fall back to file-based storage when PG is unavailable. See `db/` for schema and migration files. Mac PostgreSQL is the archive/backup/restore authority.

## PG-Disabled Fallback

When `TRADERIE_PG_ADAPTER_ENABLED=false` (default):
- **ingest-snapshot**: writes JSONL history to filesystem (data/history/traderie/{seg}/)
- **process-products**: reads from JSONL files, writes product JSONs
- **validate-products**: validates filesystem artifacts only
- **check-health**: reports `backup_state=not_applicable`, no PG health fields
- **backup-postgres**: no-op — writes health record with `backup_state=not_applicable`
- **retain-snapshots**: operates on filesystem artifacts only (PG data not affected)

## Security

- Service runs as `scraper` (non-root)
- Env file at `/home/scraper/config/traderie.env` (chmod 600, outside repo tree)
- No credentials in Git (all secrets in VPS-local env file)
- PostgreSQL adapter disabled by default — no DB credentials loaded at import time
- Retain-snapshots defaults to `--dry-run` until Destructive Operation Gate

## Gate Sequence

1. **SHARED-004** VPS Capacity Gate — confirm disk/RAM headroom before any install
2. **Scheduler Gate** — approve timer installation
3. **Database Authority Gate** — before PG role/database creation
4. **Backup/Restore Gate** — before backup-postgres, retain-snapshots, or any destructive operation
5. **Destructive Operation Gate** — before removing --dry-run from retain-snapshots

## Related Documents

| Document | Path |
|----------|------|
| Architecture | `ivy-control-vps/docs/PORTFOLIO_CONVENTIONS.md` |
| Health contract | `ivy-control-vps/docs/PORTFOLIO_CONVENTIONS.md` (health contract section) |
| Backup/restore | `docs/backup-restore.md` |
| Retention policy | `docs/retention.md` |
| Schema/migrations | `db/README.md` |
| Shared conventions | `ivy-control-vps/docs/PORTFOLIO_CONVENTIONS.md` |
| Repository control | `ivy-control-vps/repos/traderie/CONTROL.md` |
