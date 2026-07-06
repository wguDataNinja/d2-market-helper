# db/ — Traderie PostgreSQL Schema and Migrations

**Authority:** `vps/shared-conventions.md` §4 (Migration File Layout)
**Architecture:** `ivy-control/vps/worker-control/reports/CODEX_SESSION_1_ARCHITECTURE.md` §12-13
**Status:** Inert — no database connection authorized.

## Directory Layout

```
db/
  README.md
  migrations/
    YYYYMMDD_NNN_description.sql          # Forward migration
    rollback/
      YYYYMMDD_NNN_description_down.sql   # Rollback SQL
    validation/
      YYYYMMDD_NNN_description_check.sql  # Validation/invariant queries
  fixtures/
    seed.sql                               # Small synthetic test data
```

## Database

- **Name:** `traderie`
- **Schemas:** `app` (application state), `health` (private health), `archive` (optional manifests)
- **Role pattern:** `traderie_writer`, `traderie_reader`, `traderie_monitor`, `traderie_migrator`, `traderie_backup`

## Storage Boundary

PostgreSQL stores normalized operational state + deduped completed-trade history only.
Raw and normalized snapshots remain filesystem/archive objects with bounded retention.

## Database Authority Gate

No migration in this directory may be applied to a live PostgreSQL instance until:

1. Architecture accepted (CODEX_SESSION_1_ARCHITECTURE.md §12-13)
2. TRD-003 implementation approved
3. Database Authority Gate granted by Buddy
4. Backup/Restore evidence exists for current 2.7 GB data

## Conventions

- Forward-only migrations with rollback SQL
- All timestamps as `timestamptz`
- CHECK constraints instead of PostgreSQL enums
- Migration tracking via `app.traderie_migrations`
