# Traderie — Ivy-Control/VPS Authority and Remaining Work

**Date:** 2026-07-06
**Run slug:** traderie-ivy-authority-discovery
**Scope:** Cross-repo (ivy-control + traderie) authority reconciliation and task inventory
**Status:** Read-only discovery artifact — no implementation authorized

---

## Executive Conclusion

**The five most authoritative Ivy-Control/VPS documents for Traderie are:**

1. `vps/IMPLEMENTATION_PROGRAM.md` — The governing execution controller. Defines worker queue, Gates, status model, and sequencing.
2. `vps/shared-conventions.md` — Default naming, roles, migration layout, backup format, health contract, systemd naming.
3. `vps/worker-control/reports/POST_FOUNDATION_TO_VPS_ROADMAP.md` — The forward roadmap from empty PostgreSQL foundation through bounded pilot to VPS cutover. Contains the authoritative Traderie pilot requirements.
4. `vps/worker-control/reports/DATABASE_AUTHORITY_GATE_EXECUTION_REPORT.md` — Proves the database exists, roles are provisioned, isolation is verified. Foundation authority evidence.
5. `vps/VPS_MIGRATION_STATUS.md` — Per-repo phase tracker showing traderie at P0-complete, P1-ready, P2-P6 not started.

**Traderie's actual readiness state:** Foundation-complete, file-backed authority, real-data pilot BLOCKED. The empty PostgreSQL `traderie` database exists on Mac PG16 with all 6 roles provisioned and 3 schemas created. All 9 migrations are authored and validated. Backup/restore drill passes. But no real data has been loaded, the PG adapter is an in-memory dry store, and no explicit real-data Gate approval has been recorded.

**The narrowest current blocker:** `scripts/traderie_pg_adapter.py` is an in-memory dry store, not a live PostgreSQL writer. The real loader (`scripts/traderie_pilot_loader.py`) exists and has 6/6 tests passing, but cannot connect to the database because the adapter layer does not implement live connection, query, upsert, or rollback methods against actual PostgreSQL.

**The authoritative next task:** Implement a real PostgreSQL adapter/loader for Traderie using `traderie_writer`, with `--dry-run`, `--plan`, `--apply`, reject reporting, rollback by `segment_slug + observation_key`, delete-and-reimport proof, and file/PG parity — per the exact requirements in `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3.

**Should any existing roadmap be updated?** No. The product `ROADMAP.md` correctly lists its 5 remaining pre-alpha items and should not be touched. The `VPS_ROADMAP.md` already correctly defers to shared conventions where they conflict. The `SESSION.md` accurately reflects the current blocked state. No roadmap needs updating before implementation continues.

---

## 1. Authority Hierarchy

```
Governing Authority (do not override)
├── vps/IMPLEMENTATION_PROGRAM.md        (2026-07-06)
├── vps/shared-conventions.md            (2026-07-05, active)
├── vps/DEPLOYMENT_WORKFLOW.md           (active)
├── vps/github-readiness-checklist.md    (active)
├── vps/repo-operating-standard.md       (active, hybrid standard)
├── vps/vps-host.md                      (active, canonical VPS identity)
└── vps/VPS_MIGRATION_STATUS.md          (2026-07-05, reconciled)

Active Execution Controller
├── vps/worker-control/reports/POST_FOUNDATION_TO_VPS_ROADMAP.md  (2026-07-06)
├── vps/worker-control/reports/REAL_DATA_PILOT_GATE_ASSESSMENT_20260706.md (2026-07-06)
└── vps/IMPLEMENTATION_PROGRAM.md (canonical worker queue, §Traderie)

Status/Continuity Records
├── vps/worker-control/reports/DATABASE_AUTHORITY_GATE_EXECUTION_REPORT.md (2026-07-05)
├── vps/worker-control/reports/BACKUP_RESTORE_GATE_PACKAGE.md (2026-07-05)
├── vps/worker-control/reports/VPS_POSTGRES_CAPACITY_GATE_20260706.md (2026-07-06)
├── vps/worker-control/reports/STRONG_AGENTIC_EXECUTION_REPORT.md (2026-07-06)
├── vps/worker-control/reports/SJC_TRADERIE_GITHUB_AND_DOCS_READINESS.md (2026-07-06)
├── vps/worker-control/reports/RECENT_EXECUTION_LOG_AND_EVIDENCE_INDEX.md (2026-07-06)
├── vps/worker-control/reports/TRADERIE_GIT_FORENSICS.md
├── vps/worker-control/reports/THREE_REPO_GIT_CLOSURE_REPORT.md (2026-07-06)
└── vps/worker-control/reports/THREE_REPO_COMMIT_PLAN.md (2026-07-06)

Operating Conventions
├── vps/postgres/README.md (shared PG conventions)
├── vps/postgres/ENV_REFERENCE.md (env var names per project)
└── vps/postgres/ (project-specific PG files)

Traderie-Local Documents (not authoritative over ivy-control)
├── VPS_ROADMAP.md (2026-07-04 — planning artifact, superseded by shared conventions)
├── docs/VPS_CONTINUITY.md (2026-07-06 — repo-local continuity status)
├── docs/backup-restore.md (2026-07-05 — repo-local backup guide)
├── docs/retention.md (2026-07-05 — repo-local retention policy)
├── deploy/README.md (INERT — all services marked do not install)
├── SESSION.md (current state)
├── ROADMAP.md (product roadmap — untouched)
└── AGENTS.md (router for agent work)

Archived/Superseded
├── vps/archive/root-plans/ECOSYSTEM_VPS_ROADMAP.md (superseded by IMPLEMENTATION_PROGRAM)
├── vps/archive/root-plans/CODEX_ROADMAP_PROGRAM.md (superseded)
├── vps/archive/root-plans/IVY_CONTROL_VPS_BOOTSTRAP.md (superseded)
├── vps/archive/root-plans/PORTFOLIO_REPO_STANDARD.md (superseded)
├── vps/archive/root-plans/FIRST_WAVE_DISPATCH.md (superseded)
├── vps/archive/audits/ (historical audits — reference only)
├── vps/archive/reviews/codex-prompt-automation-audit-2026-07-04.md (historical)
├── vps/archive/reviews/codex-ecosystem-planning-review-2026-07-04.md (historical)
├── vps/archive/worker-control/ (entire directory — archived)
└── vps/archive/logs/session/gpt*.md (historical session logs)
```

### Authority rules

1. `IMPLEMENTATION_PROGRAM.md` overrides `VPS_MIGRATION_STATUS.md` where they conflict (the latter was written before the Mac PG16 foundation).
2. `POST_FOUNDATION_TO_VPS_ROADMAP.md` is the forward execution road map and supersedes earlier planning roadmaps (including `VPS_ROADMAP.md` where they conflict).
3. `shared-conventions.md` naming/role/migration conventions override Traderie-local planning docs by explicit cross-reference.
4. Archived docs under `vps/archive/` are read-only references — they do not govern current work.
5. The product `ROADMAP.md` in traderie is intentionally preserved and untouched by infrastructure planning.

Documents a future Traderie agent MUST read first (in order):

1. `vps/IMPLEMENTATION_PROGRAM.md`
2. `vps/shared-conventions.md`
3. `vps/worker-control/reports/POST_FOUNDATION_TO_VPS_ROADMAP.md`
4. `Traderie/VPS_ROADMAP.md` (for repo-local context)
5. `Traderie/docs/VPS_CONTINUITY.md`
6. `Traderie/SESSION.md`
7. `Traderie/LOG.md`
8. `vps/worker-control/reports/REAL_DATA_PILOT_GATE_ASSESSMENT_20260706.md`
9. `Traderie/AGENTS.md`

---

## 2. Most Relevant Documents — Traderie-Specific Requirements

### `vps/IMPLEMENTATION_PROGRAM.md`

| Requirement for Traderie | Status |
|---|---|
| Traderie is MIGRATED (backup, manifest, SHA-256 verified) | ✅ Complete |
| TRD-001: Boundary and runtime audit | `READY` — fallback, not needed |
| TRD-002: GitHub readiness and data contract | `BLOCKED` |
| TRD-005: Local parity rehearsal | `BLOCKED` |
| TRD-006: VPS Cloudscraper/browser smoke | `GATE_REQUIRED` |
| TRD-007: Service and health templates | `PARTIAL` — backup runbook done, inert systemd units not implemented |
| TRD-008: Shadow, cutover, and fallback | `GATE_REQUIRED` |
| Traderie is downstream foundation MIGRATED | ✅ Complete (from §Downstream foundation migration) |

### `vps/shared-conventions.md`

| Requirement for Traderie | Status |
|---|---|
| Database name `traderie` | ✅ Created |
| Roles: `traderie_writer`, `traderie_reader`, `traderie_monitor`, `traderie_migrator`, `traderie_backup` | ✅ Provisioned |
| Schemas: `app`, `archive`, `health` | ✅ Created |
| Migration layout: `db/migrations/NNN_*.sql` + rollback + validation | ✅ 9 migrations present with rollbacks and checks |
| Systemd naming: `traderie-ingest-snapshot`, `traderie-process-regen` | ✅ Unit files exist (INERT) |
| Backup destination: `/Users/buddy/projects/backups/postgres/traderie/` | ✅ Clean baseline dump and manifest exist |
| Health contract per §8 | ⚠️ Partial — `scripts/traderie_health_export.py` exists, not production-ready |
| Env var naming: `TRADERIE_PG_URL` etc. | ✅ Documented in `vps/postgres/ENV_REFERENCE.md` |
| VPS file layout per §6 | ⚠️ Not yet deployed |
| Mac fallback per shadow/parity sequence §11 | ❌ Not started |

### `vps/worker-control/reports/POST_FOUNDATION_TO_VPS_ROADMAP.md`

This document contains the authoritative Traderie pilot sequence (§3):

| Required step | Status |
|---|---|
| Implement real loader using `traderie_writer` | ❌ **BLOCKER** — `traderie_pg_adapter.py` is in-memory dry store |
| Map JSONL → `app.completed_trades`, `app.price_entries`, `app.snapshot_runs` | ⚠️ Partial — `traderie_pilot_loader.py` has the mapping logic but adapter is dry-store |
| Reject report for empty price, missing key, invalid segment, etc. | ✅ `classify_records()` in readiness report |
| Keep raw snapshots/history as file authority | ✅ Already the case |
| Rollback by `segment_slug + observation_key` | ✅ Implemented in pilot loader |
| Pre-load backup and restore drill | ✅ Backup/restore drill PASS |
| Apply only eligible deterministic subset after Gate | ✅ Ready — pilot readiness report generates the subset |
| Idempotent replay | ✅ ON CONFLICT DO NOTHING |
| File/PG parity for selected keys | ✅ `--parity` mode in pilot loader |
| Expansion criteria met | ❌ Blocked on adapter |
| Evidence report | ❌ Not produced |

### `vps/VPS_MIGRATION_STATUS.md`

Traderie row (lines 126-136):

| Phase | Status |
|---|---|
| P0 Discovery | ✅ Complete |
| P1 Roadmap | 🔄 Ready for Codex (note: Codex was run, producing VPS_ROADMAP.md + migrations + adapters) |
| P2 GitHub readiness | ❌ Not started |
| P3 Shared infra | ⏳ Partial — PG server and base database exist; project migrations not applied |
| P4 VPS deployment | ❌ Not started |
| P5 Mac fallback | ❌ Not started |
| P6 Monitoring | ❌ Not started |

**Note:** This table needs clarification on P3. The statement "project migrations not applied" conflicts with the DATABASE_AUTHORITY_GATE_EXECUTION_REPORT.md which shows all 9 migrations were applied during the foundation wave. The correct state is: migrations ARE applied but they are base/schema-only (empty tables, no data). The "not applied" remark may refer to project-specific data migrations or may be stale wording.

### `vps/worker-control/reports/REAL_DATA_PILOT_GATE_ASSESSMENT_20260706.md`

Traderie Gate status: `BLOCKED`

| Finding | Detail |
|---|---|
| PG adapter is in-memory dry store | Confirmed — `scripts/traderie_pg_adapter.py` does not connect to real PG |
| No production loader | Confirmed — pilot loader exists but requires real adapter |
| No explicit Traderie real-data Gate approval | Confirmed — not recorded in any document |
| Eligible subset is clean | ✅ 25 pc_sc_l records, digest `df82ac34`, no missing fields |
| 40/40 adapter tests pass | ✅ |
| Live PG row counts unchanged | ✅ 0 rows in completed_trades, price_entries; 4 reference segment rows |

---

## 3. Existing Traderie Task Inventory

All currently defined tasks, reconciled across both repos:

### From Ivy-Control `IMPLEMENTATION_PROGRAM.md` worker queue (§Traderie)

| ID | Status | Original Wording | Prerequisite | Gate | Evidence Needed | Current State |
|---|---|---|---|---|---|---|
| TRD-001 | `READY` | Boundary and runtime audit (fallback) | None | None | Audit report | Not needed — audits already exist in ecosystem review and multiple Codex reports |
| TRD-002 | `BLOCKED` | GitHub readiness and data contract | TRD-GIT-001 preflight | GitHub Push Gate | Clean repo, README, LICENSE, CI | Partially done — CI workflow exists, env.example done, plists parameterized; no LICENSE, no remote |
| TRD-005 | `BLOCKED` | Local parity rehearsal | Real PG adapter | Database Authority Gate | parity_report.py ran successfully | **BLOCKER** — adapter is in-memory, parity cannot run against real PG |
| TRD-006 | `GATE_REQUIRED` | VPS Cloudscraper/browser smoke | TRD-002 (repo on GitHub) | VPS Capacity Gate | Manual smoke test on VPS | Not started |
| TRD-007 | `PARTIAL` | Service and health templates | None | Scheduler Gate | systemd unit files, health export | Backup runbook done (`docs/backup-restore.md`). Unit files exist in `deploy/systemd/` but are marked INERT. Health export script exists (`traderie_health_export.py`). |
| TRD-008 | `GATE_REQUIRED` | Shadow, cutover, and fallback | TRD-005, TRD-006, TRD-007 | PostgreSQL Cutover Gate, Scheduler Gate | Parity report, shadow run evidence, fallback doc | Not started |

### Additional defined tasks from other documents

| Source | Task | Status | Notes |
|---|---|---|---|
| `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 | Implement real PG adapter/loader using `traderie_writer` | ❌ **BLOCKER** | The single biggest remaining item |
| `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 | Map JSONL → completed_trades, price_entries, snapshot_runs | ⚠️ Partial | Mapping logic is in pilot loader but cannot execute against real PG |
| `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 | Add reject report | ✅ Done | In pilot loader |
| `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 | Add rollback script | ✅ Done | In pilot loader |
| `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 | Pre-load backup + restore drill | ✅ Done | Clean baseline backup exists and restore drill PASS |
| `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 | Apply eligible subset after Gate approval | ❌ Blocked | Requires adapter + Gate |
| `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 | Idempotent replay | ✅ Ready | ON CONFLICT DO NOTHING |
| `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 | File/PG parity | ⚠️ Partial | `--parity` mode exists but cannot run against real PG |
| `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 | Evidence report | ❌ Not produced | Must be produced after pilot |
| `SJC_TRADERIE_GITHUB_AND_DOCS_READINESS.md` §7 | CI workflow | ✅ Done | `.github/workflows/ci.yml` exists (commit 3b9898a) |
| `SJC_TRADERIE_GITHUB_AND_DOCS_READINESS.md` §7 | LICENSE file | ❌ Missing | Not added |
| `SJC_TRADERIE_GITHUB_AND_DOCS_READINESS.md` §7 | Rollback instructions doc | ⚠️ Partial | Covered by pilot loader CLI; no standalone doc |
| Traderie product `ROADMAP.md` | Create/connect GitHub remote | 🔲 Pending | Not done |
| Traderie product `ROADMAP.md` | Push master + enable GH Pages | 🔲 Pending | Blocked on remote |
| Traderie product `ROADMAP.md` | Verify deployed site | 🔲 Pending | Blocked on remote |
| Traderie `VPS_ROADMAP.md` | VPS cloudscraper test | ❌ Not started | Deferred |
| Traderie `VPS_ROADMAP.md` | Hardcore alert semantics decision | ❌ Not decided | Deferred |
| Traderie `VPS_ROADMAP.md` | JSONL retention after PG-primary | ❌ Not decided | Deferred |
| `deploy/README.md` | Adapt Mac scripts to VPS paths | ❌ Not started | All deploy scripts marked INERT |

### Reconciliations

- **TRD-003** and **TRD-007** from earlier audits: TRD-003 (data contract) is implied by TRD-002. TRD-007 (service templates) now has unit files created but marked INERT. Both are superseded by the consolidated `IMPLEMENTATION_PROGRAM.md` queue.
- **TRD-009** (pre-GitHub hardening) was executed (commit 5a67f09) and is now COMPLETE. No separate TRD-009 entry remains in the active queue.
- **Backup/restore** is listed separately in multiple docs but the clean baseline backup, manifest, and restore drill all PASS. The gap is that no production data has been backed up yet (no data has been loaded).

---

## 4. Completion/Status Reconciliation

| Item | Document Says | Actual Evidence | Verdict |
|---|---|---|---|
| Database provisioned | ✅ Yes | `traderie` DB exists on Mac PG16, 6 roles, 3 schemas | CONFIRMED |
| Migrations applied | VPS_MIGRATION_STATUS says "not applied" | All 9 migrations exist in `db/migrations/` and were applied during foundation wave; 4 reference segment rows exist | **STALE CLAIM** — migrations ARE applied (empty base tables) |
| Backup/restore | ✅ PASS | `manifest_clean_20260706T064435Z.yaml` shows restore_status: PASS, validation_status: PASS | CONFIRMED |
| Adapter complete | SESSION.md says pilot loader blocked because adapter is in-memory | `scripts/traderie_pg_adapter.py` does not implement live PG connection | CONFIRMED — adapter is NOT complete |
| Deployment complete | deploy/README.md says INERT, do not install | Unit files exist but are INERT, no services running | CONFIRMED — deployment is NOT complete |
| Pilot ready | REAL_DATA_PILOT_GATE_ASSESSMENT says BLOCKED | Adapter is dry-store, no Gate approval | CONFIRMED — pilot is NOT ready |
| CI exists | SJC_TRADERIE_GITHUB_AND_DOCS_READINESS listed as absent | `.github/workflows/ci.yml` was added in commit 3b9898a | **UPSERT** — CI now exists |
| Hardcoded /Users/buddy/ paths | Standards-gap-summary listed as needing fix | Shell scripts parameterized via `TRADERIE_REPO_DIR`. Plists still use absolute paths (by design for launchd). | Partially resolved — intentional launchd constraint |
| Product ROADMAP.md items | 3 items marked 🔲 pending | None of the 3 (verify launchd, create remote, push/enable Pages) are done | CONFIRMED — still pending |

### Stale/Conflicting Claims

1. **VPS_MIGRATION_STATUS.md says traderie P3 "project migrations not applied."** This conflicts with DATABASE_AUTHORITY_GATE_EXECUTION_REPORT.md which shows migrations applied and validation run. The phrase likely means "project data migrations not applied" (i.e., no real data loaded) — the wording is ambiguous. The correct status is: **schema migrations applied, data not loaded.**

2. **SJC_TRADERIE_GITHUB_AND_DOCS_READINESS.md listed CI workflow as absent.** The report was generated before `.github/workflows/ci.yml` was committed. CI now exists (commit 3b9898a).

3. **VPS_ROADMAP.md references `traderie_admin` role name.** The shared-conventions standard uses `traderie_migrator`, not `traderie_admin`. The `VPS_ROADMAP.md` explicitly acknowledges this self-corrects ("superseded by shared conventions where they conflict").

4. **deploy/README.md says ingest-snapshot runs "Every 15 min."** The actual schedule from launchd is 4x daily (05, 11, 17, 23), not every 15 minutes. The deploy README describes a proposed VPS schedule, not the current one. This is intentional for VPS planning but could cause confusion.

5. **BACKLOG.md in ivy-control BACKUP_RESTORE_GATE_PACKAGE.md lists traderie backup/restore as all ❌.** The clean baseline backup and restore drill DO exist and PASS. The backup/restore gate package template was written before the foundation wave and was never updated per-project.

---

## 5. Authoritative Remaining To-Do List

### Must complete before pilot approval

1. **Implement real PostgreSQL adapter**
   - Why: `scripts/traderie_pg_adapter.py` must connect to live `traderie` database using `traderie_writer`, not be an in-memory dry store.
   - Governing source: `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 item 1, `REAL_DATA_PILOT_GATE_ASSESSMENT_20260706.md` §Traderie Assessment
   - Exact completion evidence: Adapter tests pass against Mac PG16 `traderie` database; `traderie_pilot_loader.py --apply` with `--dry-run=false` successfully inserts the 25-record pilot subset and rollback deletes them.
   - Buddy approval required? Yes — explicit real-data Gate approval must be recorded before pilot apply.

2. **Record explicit real-data Gate approval**
   - Why: REAL_DATA_PILOT_GATE_ASSESSMENT explicitly requires documented Gate approval before any live ingest.
   - Governing source: `REAL_DATA_PILOT_GATE_ASSESSMENT_20260706.md` §"Result" and §"Blocking conditions"
   - Exact completion evidence: A `docs/REAL_DATA_PILOT_GATE.md` or ivy-control Gate record stating "Traderie real-data pilot approved for bounded 25-record pc_sc_l subset, digest df82ac34e7ccb..."
   - Buddy approval required? Yes — this IS the Buddy approval gate.

3. **Add LICENSE file**
   - Why: GitHub readiness requires LICENSE. Codex recommendation is MIT.
   - Governing source: `repo-operating-standard.md`, `github-readiness-checklist.md`
   - Exact completion evidence: `LICENSE` file present at repo root.
   - Buddy approval required? Yes — Buddy must confirm MIT or other license choice.

### Must complete during bounded pilot

4. **Run bounded pilot load (25 records, pc_sc_l)**
   - Why: First real-data verification that the adapter → loader → PG pipeline works end-to-end.
   - Governing source: `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 item 7
   - Exact completion evidence: Pilot loader --apply succeeds; row counts verified in `app.completed_trades` and `app.price_entries`; pre- and post-load backup manifests recorded.
   - Buddy approval required? Yes — Gate approval from #2 must be in place first.

5. **Idempotent replay proof**
   - Why: Verify ON CONFLICT DO NOTHING prevents duplicates on re-run.
   - Governing source: `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 item 8
   - Exact completion evidence: Running pilot loader --apply twice produces identical row counts.

6. **Rollback proof**
   - Why: Demonstrate rollback by segment_slug + observation_key deletes only pilot rows.
   - Governing source: `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 (rollback requirement)
   - Exact completion evidence: After --rollback, `app.completed_trades` and `app.price_entries` return to pre-load counts.

7. **Delete-and-reimport proof**
   - Why: Verify delete → re-apply produces same digest.
   - Governing source: `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 item 9
   - Exact completion evidence: Second apply produces identical row counts and stable_digest.

8. **File/PG parity report**
   - Why: Compare PG-backed output to file-backed source of truth for selected records.
   - Governing source: `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 item 9, `REAL_DATA_PILOT_GATE_ASSESSMENT_20260706.md` §Traderie Assessment
   - Exact completion evidence: parity_report.py (or pilot_loader --parity) outputs zero mismatches for required fields.

9. **Pilot evidence report**
   - Why: Durable record of what was done, counts, digests, backup, rollback, parity.
   - Governing source: `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 "Definition of done"
   - Exact completion evidence: Report committed to repo-local LOG.md or docs/ directory.

10. **Create GitHub remote + push master (or defer to post-pilot)**
    - Why: Required for deployment. Can be done before or after pilot, but is the top product roadmap item.
    - Governing source: Traderie product `ROADMAP.md` remaining items 3-5
    - Exact completion evidence: `gh repo create buddyowens/traderie && git remote add origin ... && git push`
    - Buddy approval required? Yes — GitHub Push Gate.

### Must complete before VPS service activation

11. **VPS cloudscraper smoke test**
    - Why: Verify cloudscraper works on Ubuntu 24.04 Hetzner CX23 before designing systemd timers.
    - Governing source: `VPS_ROADMAP.md` deferred decisions, `TRD-006`
    - Exact completion evidence: Manual `python3 -c cloudscraper` smoke test on VPS succeeds.
    - Buddy approval required? Yes — VPS access required.

12. **Adapt VPS wrapper scripts**
    - Why: Mac launchd scripts have Mac paths. VPS needs parameterized versions.
    - Governing source: `deploy/README.md` §Wrapper Scripts
    - Exact completion evidence: `scripts/run_traderie_snapshot.sh` (VPS variant) exists and passes shellcheck.
    - Buddy approval required? No (mechanical work).

13. **VPS systemd timer dry-run (manual)**
    - Why: Manually run each systemd service/timer pair to verify it works before enabling automation.
    - Governing source: `IMPLEMENTATION_PROGRAM.md` Gate matrix (Scheduler Gate), `deploy/README.md`
    - Exact completion evidence: Each service runs to completion manually; logs are clean.
    - Buddy approval required? Yes — Scheduler Gate.

### Must complete before timer enablement

14. **Systemd timer enablement**
    - Why: Move from manual/test to scheduled operation.
    - Governing source: `IMPLEMENTATION_PROGRAM.md` Scheduler Gate, `shared-conventions.md` §7
    - Exact completion evidence: `systemctl --user enable --now traderie-ingest-snapshot.timer` and similar.
    - Buddy approval required? Yes — Scheduler Gate.

15. **Health export production readiness**
    - Why: `scripts/traderie_health_export.py` must produce reliable, sanitized JSON for monitoring.
    - Governing source: `shared-conventions.md` §8, `IMPLEMENTATION_PROGRAM.md` TRD-007
    - Exact completion evidence: Health export runs and produces valid JSON with §8-required fields.
    - Buddy approval required? No (can be done in parallel).

16. **Mac fallback activation**
    - Why: Disable launchd schedules, keep loaded for fallback triggers.
    - Governing source: `shared-conventions.md` §11 authority transfer sequence
    - Exact completion evidence: Mac launchd jobs have disabled schedules; Mac monitors VPS export freshness.
    - Buddy approval required? Yes — PostgreSQL Cutover Gate, Scheduler Gate.

### Deferred / non-blocking

| Item | Why deferred | Approximate target |
|---|---|---|
| JSONL legacy retirement | Requires 30 days of stable PG-primary operation | 30+ days after pilot success |
| Full history migration | Beyond bounded pilot scope | After pilot expansion approved |
| VPS PostgreSQL deployment | Blocked on capacity Gate (ih-market-vps 89% disk) | After dedicated DB VPS or host resize |
| Reverse SSH tunnel | Only needed when VPS PG is deployed | After VPS PG decision |
| Hermes integration | Optional, non-blocking | After VPS monitoring stable |
| Cash/browser source automation | Requires browser capture on VPS | Deferred — not in v1 VPS migration |
| Public portfolio dashboard | Depends on health-schema standards | Deferred |

---

## 6. Single Recommended Next Assignment

**Assignment ID:** TRD-010 (new — implement real PostgreSQL adapter)

**Scope:** Replace `scripts/traderie_pg_adapter.py` in-memory dry store with a live PostgreSQL adapter using the existing `traderie_writer` role against Mac PG16 `traderie` database on `127.0.0.1:5432`.

**Objective:** Unblock the Traderie real-data pilot by providing a real PG connection layer that `scripts/traderie_pilot_loader.py` can use for `--dry-run`, `--plan`, `--apply`, `--rollback`, and `--parity` modes.

**Prerequisites:**
- `IMPLEMENTATION_PROGRAM.md` read and understood
- `shared-conventions.md` read and understood
- `POST_FOUNDATION_TO_VPS_ROADMAP.md` §3 read and understood
- `REAL_DATA_PILOT_GATE_ASSESSMENT_20260706.md` read and understood
- `vps/postgres/ENV_REFERENCE.md` read for env var conventions
- Credentials for `traderie_writer` from `/Users/buddy/.local/secure/ivy-control/postgres/` (via Buddy)

**Exclusions:**
- Do not load real data (pilot remains BLOCKED until Gate approval recorded)
- Do not modify product files
- Do not change VPS state
- Do not enable systemd timers
- Do not run git commit

---

## 7. Files Inspected

### Ivy-Control
```
vps/IMPLEMENTATION_PROGRAM.md
vps/shared-conventions.md
vps/VPS_MIGRATION_STATUS.md
vps/README.md
vps/vps-host.md
vps/DEPLOYMENT_WORKFLOW.md
vps/github-readiness-checklist.md
vps/repo-operating-standard.md
vps/postgres/README.md
vps/postgres/ENV_REFERENCE.md
vps/worker-control/reports/POST_FOUNDATION_TO_VPS_ROADMAP.md
vps/worker-control/reports/REAL_DATA_PILOT_GATE_ASSESSMENT_20260706.md
vps/worker-control/reports/DATABASE_AUTHORITY_GATE_EXECUTION_REPORT.md
vps/worker-control/reports/BACKUP_RESTORE_GATE_PACKAGE.md
vps/worker-control/reports/SJC_TRADERIE_GITHUB_AND_DOCS_READINESS.md
vps/worker-control/reports/RECENT_EXECUTION_LOG_AND_EVIDENCE_INDEX.md
vps/worker-control/reports/TRADERIE_GIT_FORENSICS.md
vps/worker-control/reports/THREE_REPO_GIT_CLOSURE_REPORT.md
vps/worker-control/reports/THREE_REPO_COMMIT_PLAN.md
vps/worker-control/reports/STRONG_AGENTIC_EXECUTION_REPORT.md
vps/worker-control/reports/REVERSE_TUNNEL_PACKAGE.md
vps/worker-control/reports/HERMES_GOVERNANCE_ARCHITECTURE.md
vps/worker-control/reports/VPS_POSTGRES_CAPACITY_GATE_20260706.md
vps/archive/root-plans/ECOSYSTEM_VPS_ROADMAP.md (superseded)
vps/archive/root-plans/CODEX_ROADMAP_PROGRAM.md (superseded)
vps/archive/logs/session/gpt1.md (historical)
vps/archive/logs/session/gpt2.md (historical)
```

### Traderie
```
README_INTERNAL.md
AGENTS.md
ROADMAP.md
VPS_ROADMAP.md
SESSION.md
LOG.md
BACKLOG.md
docs/VPS_CONTINUITY.md
docs/backup-restore.md
docs/retention.md
deploy/README.md
deploy/ROLLBACK.md
deploy/env.example
deploy/systemd/ (6 service + timer pairs)
db/README.md
db/migrations/20260705_001-009*.sql
db/migrations/rollback/*.sql
db/migrations/validation/*.sql
db/fixtures/seed.sql
db/validation/999_full_validation.sql
scripts/traderie_pg_adapter.py
scripts/traderie_storage_adapter.py
scripts/traderie_pilot_loader.py
scripts/traderie_pilot_readiness_report.py
scripts/traderie_health_export.py
scripts/traderie_parity_report.py
scripts/traderie_disk_inventory.py
scripts/snapshot_traderie.py
scripts/run_traderie_snapshot_launchd.sh
scripts/regenerate_products.sh
tests/test_traderie_adapter.py
tests/test_traderie_pilot_loader.py
.github/workflows/ci.yml
.github/workflows/deploy.yml
.env.example
requirements.txt
.gitignore
```
