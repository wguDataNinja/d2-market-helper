# Traderie — VPS Continuity Document

**Date:** 2026-07-06
**Purpose:** Provide a durable record of the repository's PostgreSQL foundation, pilot readiness, and VPS deployment path.

## Read First

A future worker should begin in this order:

1. Repo-local `AGENTS.md` — routing and safety rules
2. Repo-local `SESSION.md` — current session state
3. Repo-local `LOG.md` — durable activity log
4. **This document** (`docs/VPS_CONTINUITY.md`) — project-specific VPS status
5. `ivy-control/vps/worker-control/reports/STRONG_AGENTIC_EXECUTION_REPORT.md` — most recent execution report
6. `ivy-control/vps/worker-control/reports/REAL_DATA_PILOT_GATE_ASSESSMENT_20260706.md` — current Gate status
7. `ivy-control/vps/worker-control/reports/POST_FOUNDATION_TO_VPS_ROADMAP.md` — forward roadmap

### Where Recent Work Was Logged

| What | Path |
|------|------|
| Repo-local activity log | `LOG.md` (this repo) |
| Repo-local session state | `SESSION.md` (this repo) |
| Migration/validation evidence | `db/migrations/`, `db/validation/999_full_validation.sql` |
| Clean backup manifest | `/Users/buddy/projects/backups/postgres/traderie/manifest_clean_20260706T064435Z.yaml` |
| Restore evidence | Same manifest (restore_status: PASS, validation_status: PASS) |
| Pilot loader | `scripts/traderie_pilot_loader.py` |
| Pilot loader tests | `tests/test_traderie_pilot_loader.py` (6 tests PASS) |
| VPS continuity | This file |
| GitHub-readiness report | `ivy-control/vps/worker-control/reports/SJC_TRADERIE_GITHUB_AND_DOCS_READINESS.md` |

### Authority Rule

This document summarizes project state. Ivy-Control (`/Users/buddy/projects/ivy-control/vps/`) controls shared infrastructure, Gates, deployment workflow, and cross-project sequencing. Always check the Ivy-Control reports before making cross-project or VPS-level changes.

---

## Current Completed Work

| Work Item | Status | Evidence |
|-----------|--------|----------|
| PostgreSQL database (`traderie`) | ✅ Provisioned, Wave 1 | `ivy-control/vps/worker-control/reports/DATABASE_AUTHORITY_GATE_EXECUTION_REPORT.md` |
| 6 project roles | ✅ Provisioned | Same |
| 3 base schemas (app/archive/health) | ✅ Provisioned | Same |
| 9 schema migrations | ✅ Applied | `db/migrations/` — validated and backed up |
| `db/validation/999_full_validation.sql` | ✅ PASS | Post-migration restore drill evidence |
| Clean baseline backup + restore drill | ✅ PASS | Manifest at `/Users/buddy/projects/backups/postgres/traderie/` |
| 4 reference segment rows | ✅ Intentionally preserved | `app.segments` — pre-existing, not synthetic |
| Pilot loader (`scripts/traderie_pilot_loader.py`) | ✅ Implemented, tested (6 tests) | dry-run/plan/apply/rollback/parity modes, writer-role-only |
| File authority (JSONL snapshots) | ✅ Current source of truth | `data/` directory — not yet loaded to PG |
| Real-data ingestion | ❌ Not started | Blocked on pilot Gate approval |
| VPS deployment | ❌ Not started | No services, no timers, no checkout |

---

## Relevant Ivy-Control Documents

| Document | Path | Purpose |
|----------|------|---------|
| Database Authority Gate execution report | `ivy-control/vps/worker-control/reports/DATABASE_AUTHORITY_GATE_EXECUTION_REPORT.md` | Live PostgreSQL state, roles, schemas, privileges |
| Deployment workflow | `ivy-control/vps/DEPLOYMENT_WORKFLOW.md` | Canonical Mac→GitHub→VPS deployment model |
| Post-foundation roadmap | `ivy-control/vps/worker-control/reports/POST_FOUNDATION_TO_VPS_ROADMAP.md` | Current forward roadmap with Traderie pilot sequence |
| Real-data pilot Gate assessment | `ivy-control/vps/worker-control/reports/REAL_DATA_PILOT_GATE_ASSESSMENT_20260706.md` | Traderie Gate status and pilot candidate definition |
| SJC/Traderie readiness report | `ivy-control/vps/worker-control/reports/SJC_TRADERIE_GITHUB_AND_DOCS_READINESS.md` | Pilot loader, GitHub readiness, docs inventory |
| Backup/restore Gate package | `ivy-control/vps/worker-control/reports/BACKUP_RESTORE_GATE_PACKAGE.md` | Template for backup/restore drills |
| Implementation program | `ivy-control/vps/IMPLEMENTATION_PROGRAM.md` | Layered implementation ledger with reconciliation sections |

---

## Historical Context

| Document | Useful Facts | Superseded Facts | Still-Open Work |
|----------|-------------|------------------|-----------------|
| Codex Session 1 Architecture | Traderie schema design, growth/retention architecture, adapter boundary | PG host assumption | Service/timer template activation |
| Codex Session 1 Implementation Queue | Task breakdown for TRD-003 through TRD-008 | Task statuses | TRD-008 (VPS shadow run) remains gated |
| Evidence Wave 1 (TRD-001) | Original runtime audit, 2.7GB data with no backup, 100-150MB/day growth | Backup exists now | Data growth management |
| Traderie backup/retention prep | 9-class retention policy, backup runbook, disk inventory | None | Retention enforcement after real-data ingest |

---

## Authority Boundaries

| Material | Travel Path | Notes |
|----------|-------------|-------|
| Code and migrations | GitHub → reviewed PR → approved SHA → VPS checkout | Exact SHAs, not branches |
| Secret values | Outside Git entirely | Stored in `~/.local/secure/ivy-control/postgres/` |
| Live PostgreSQL state | pg_dump/restore or deterministic importer | Not through normal Git history |
| JSONL snapshots (source authority) | Not committed for deployment convenience | Source stays in repo `data/` for development |
| Real data | Does not belong in normal Git history | Use importer or controlled dump/restore |
| Services/timers | Activatable only after Scheduler Gate | No activation without Gate approval |

---

## Next Repository-Local Steps

1. Dry-run and plan verification: `python3 scripts/traderie_pilot_loader.py --dry-run --json`
2. Pilot Gate approval (Buddy)
3. Fresh pre-load backup
4. Bounded pilot: `python3 scripts/traderie_pilot_loader.py --apply --limit 25 --eligible-only`
5. Parity: `python3 scripts/traderie_pilot_loader.py --parity`
6. Rollback proof: `python3 scripts/traderie_pilot_loader.py --rollback`
7. Delete-and-reimport proof
8. Git cleanup and CI addition
9. Reviewed commits + GitHub push
10. Exact-SHA VPS deployment preparation
11. Shadow operation (VPS health-only timers)
12. Later cutover after evidence

---

## Pilot Loader Quick Reference

```bash
# Dry run (no mutation)
python3 scripts/traderie_pilot_loader.py --dry-run --json

# Plan (expanded evidence, no mutation)
python3 scripts/traderie_pilot_loader.py --plan --json

# Apply (requires Gate approval + recent backup)
python3 scripts/traderie_pilot_loader.py --apply --limit 25 --eligible-only

# Rollback (delete pilot rows by observation_key set)
python3 scripts/traderie_pilot_loader.py --rollback

# Parity (compare file counts vs PG counts)
python3 scripts/traderie_pilot_loader.py --parity
```

## CI / GitHub Readiness

Current gaps:
- No GitHub Actions workflow (needs Python syntax, tests, migration checks, dry-run)
- No deploy/ directory
- Pilot-readiness documentation needs formalizing

See `ivy-control/vps/worker-control/reports/SJC_TRADERIE_GITHUB_AND_DOCS_READINESS.md` for full readiness status.
