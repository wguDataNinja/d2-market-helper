# Traderie VPS Roadmap

**Date:** 2026-07-04  
**Status:** Planning artifact only. No implementation authorized.  
**Scope:** `/Users/buddy/projects/traderie`, existing launchd pipeline, future VPS systemd timers, PostgreSQL metadata/history, GitHub readiness, health, backup, and Mac fallback.

## Architecture Assessment

Verified facts:
- Traderie has an existing authoritative product `ROADMAP.md`; this companion `VPS_ROADMAP.md` preserves it.
- Current automation is Mac launchd-based: scheduled snapshot collection and product regeneration. Discovery identifies the repo as operationally mature but without VPS, PostgreSQL, offsite backup, or active remote-based delivery.
- The prompt's `traderie_production`/`traderie_development`, `traderie_admin`, `hermes_readonly`, and `/Users/buddy/backups/postgres/traderie/` examples are superseded by shared conventions where they conflict.
- `cloudscraper` viability on the VPS remains an empirical validation item, not a planning blocker.

Resolved decisions:

| Decision | Resolution | Rationale | Gate |
|---|---|---|---|
| Roadmap artifact | `VPS_ROADMAP.md` | User override; no product roadmap overwrite | None |
| Database | `traderie` on shared PostgreSQL | Database-per-project convention | Database Authority Gate |
| Roles | `traderie_writer`, `traderie_reader`, `traderie_monitor`, `traderie_migrator`, `traderie_backup` | Least privilege and Hermes read-only | Database Authority Gate |
| Product files | Continue file exports for web/dashboard consumers | Existing site/product flow remains authoritative | Merge Gate before changing public files |
| History | Dual-write/parity before any JSONL retirement | Avoid silent history loss | PostgreSQL Cutover Gate |
| Mac fallback | Keep launchd installed but disabled/monitor-triggered after VPS stability | Deterministic fetch fallback class | Scheduler Gate |
| PR model | GitHub PR automation blocked until remote exists and GitHub Push Gate clears | Repo has no verified remote in planning evidence | GitHub Push Gate |
| Cash/browser sources | Remain manual/local | Browser capture not part of v1 VPS migration | Sensitive Review Gate if changed |

Deferred decisions:

| Decision | Recommended default | Alternatives | Evidence needed | Latest point |
|---|---|---|---|---|
| VPS `cloudscraper` viability | Test on VPS before scheduler design is accepted | Keep Mac primary if blocked | Manual VPS smoke test | Before TRD-VPS-007 |
| Hardcore alert semantics | WARN on segment failures, FAIL if >50% failed for 48h | Separate hardcore lane or ignore known failures | Recent failure-rate history | Before health dashboard integration |
| JSONL retention | 30 days after PG-primary stability, then sampled/archive retention | Permanent JSONL mirror | Backup capacity and restore drill | Before TRD-VPS-010 |

## Target End State

The VPS runs deterministic Traderie snapshots and product regeneration via `traderie-*` systemd timers, writes run metadata and normalized history to PostgreSQL, preserves generated product artifacts for the current site, exposes sanitized health through ivy-control, and keeps Mac launchd as a documented fallback until retirement criteria pass.

## Workflow Classification

| Workflow | Category | Notes |
|---|---:|---|
| Traderie API snapshot | 2 shadow/parity | Existing Mac automation; VPS `cloudscraper` must be proven |
| Segment normalization/history | 2 shadow/parity | Dual-write JSONL + PG |
| Product regeneration | 2 shadow/parity | Deterministic shell/Python pipeline |
| Price JSON/export generation | 2 shadow/parity | Existing file consumer remains |
| Hardcore monitoring | 4 hardening | Needs explicit alerting and health semantics |
| Cash source parsing | 5 local/manual long term | Browser/manual capture |
| Detector/LLM/advisory outputs | 5 local/manual unless explicitly approved | Product authority must not change |
| Health report | 4 hardening | New script needed |
| Backup/restore | 4 hardening | New scripts and restore drill |
| GitHub/GHA deploy | 3 HITL gate design | Requires remote and branch/PR model |
| Mac fallback | 2 shadow/parity | Disable schedule only after VPS stable |

## PostgreSQL and Data Boundary

Database `traderie` stores:
- `items`, `segments`, `completed_trades`, `snapshot_runs`, `fetch_errors`
- `product_builds`, `export_records`, `health_records`
- optional `advisory_findings` only after product authority is explicitly locked

File-backed:
- current product JSON used by the web app
- raw/historical JSONL during parity
- large browser/HAR/manual cash artifacts
- launchd logs and transient run logs

## Worker Assignments

| ID | Class | Title | Objective | Rationale | Prerequisites | Working directory | Allowed files/systems | Explicit exclusions | Expected changes/artifacts | Commands or inspections expected | Validation/tests | Completion criteria | Rollback/recovery | Gates | Required worker report | Stop-and-escalate | Unlocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TRD-VPS-001 | inspection or documentation only | Preserve product roadmap | Verify product authority and infrastructure boundaries | Prevent D6/product scope drift | Roadmap accepted | `/Users/buddy/projects/traderie` | Docs/read-only scripts | No source edits, no launchd changes | Gap note if authorized | `rg` product roadmap, docs, launchd plists | No tests | Product/VPS boundaries reported | None | None | Product areas protected, contradictions | Product roadmap absent or active conflict | TRD-VPS-002 |
| TRD-VPS-002 | GitHub preparation | GitHub readiness preflight | Identify tracked mutable data, local paths, missing remote tasks | PR automation depends on GitHub readiness | TRD-VPS-001 | same | Docs, `.gitignore`, `.env.example`, CI drafts if later authorized | No push, no history rewrite | Readiness patch or report | `git status --short`, `rg /Users/buddy`, inspect `.github` | Secret scan tool if available | GitHub blockers listed | Revert docs/templates | GitHub Push Gate before remote | Remote status, dirty state, safe paths | Secret or large tracked data | TRD-VPS-003 |
| TRD-VPS-003 | local code change with no runtime mutation | Data contract | Document product/file/PG contract | Schema should follow actual outputs | TRD-VPS-001 | same | `docs/`, no generated product mutation | No DB, no fetch | `docs/vps-data-contract.md` | Inspect `docs/DATA_PRODUCTS.md`, `snapshot_io.py`, generators | Static review | Contract maps every product/history artifact | Revert doc | None | Tables, file authority, gaps | Product authority unclear | TRD-VPS-004 |
| TRD-VPS-004 | database preparation | Migration skeleton | Create empty-DB schema migrations and validation | Enables dev PG work | TRD-VPS-003 | same | `db/` only | No live DB, no data import | SQL, rollback, validation, README | Inspect schema docs/scripts | SQL lint if available | Schema reviewed and roles aligned | Drop empty dev DB if applied later | Database Authority Gate before apply | SQL paths, assumptions | Need production history sample outside repo | TRD-VPS-005 |
| TRD-VPS-005 | local code change with no runtime mutation | PG adapter behind flag | Add optional writer interface without changing default JSONL behavior | Dual-write needs low-risk seam | TRD-VPS-004 | same | `scripts/lib/`, tests | No runtime env, no default behavior change | Adapter module/tests | `python -m py_compile`, targeted unit tests | Existing behavior unchanged | Feature flag off by default | Revert adapter | None | Tests, default-mode proof | Default output changes | TRD-VPS-006 |
| TRD-VPS-006 | shadow or parity validation | Local dual-write rehearsal | Compare JSONL output to PG/dev output | Prevent history divergence | TRD-VPS-005 | same | Local dev DB only if approved; ignored runtime reports | No production DB/VPS | Parity report | Run sample migration/import against fixture or copied dev data | Row counts and checksum summaries | Known diffs only | Drop dev tables; JSONL unchanged | Database Authority Gate if dev DB used | Counts, mismatches, config | Requires live production data | TRD-VPS-007 |
| TRD-VPS-007 | infrastructure preparation | VPS viability smoke | Prove `cloudscraper` and Python env on VPS without scheduler | Anti-bot behavior is empirical | TRD-VPS-006 | VPS clone later | Manual VPS smoke script/report | No timers, no production authority | Smoke report | Python version, import `cloudscraper`, one bounded GET if approved | Exit code and sample response metadata | Viability accepted or fallback path chosen | Remove smoke files | Scheduler Gate for any VPS run | Command, response status, rate limits | Cloudflare blocks or credentials needed | TRD-VPS-008 |
| TRD-VPS-008 | infrastructure preparation | Systemd templates | Draft `traderie-*` service/timer units | Review before install | TRD-VPS-007 | repo | `deploy/` or `vps/` templates | Do not install/enable | Service/timer/env templates | Static inspect | Shellcheck/template review | Units disabled and parameterized | Delete templates | Scheduler Gate before install | Unit names, schedules, env | Path/secrets unresolved | TRD-VPS-009 |
| TRD-VPS-009 | shadow or parity validation | VPS shadow run | Run VPS snapshot/regeneration in shadow | Prove production-like behavior | TRD-VPS-008 | VPS clone later | Shadow outputs, logs | No authority transfer, no PR/push | Shadow evidence | `systemctl --user start` only after Gate or manual wrapper | Compare product files/counts | 7-day or accepted shorter shadow report | Disable/remove unit; Mac remains primary | Scheduler Gate | Runs, failures, freshness, fallback state | Segment failures exceed threshold | TRD-VPS-010 |
| TRD-VPS-010 | production cutover | VPS primary with Mac fallback | Make VPS primary and Mac fallback notify/run per policy | Completes runtime migration | TRD-VPS-009, restore drill | VPS + Mac launchd later | Approved timers and fallback scripts | No launchd deletion, no JSONL retirement | Timer/fallback status | systemd/launchctl status by explicit labels | 7-day no-fallback window | VPS primary stable | Disable VPS timers; re-enable Mac launchd | Scheduler Gate, PostgreSQL Cutover Gate | Timer state, fallback triggers, product freshness | Missed export or data divergence | TRD-VPS-011 |
| TRD-VPS-011 | destructive or cleanup operation | Legacy JSONL retirement | Reduce duplicate history only after stability | Avoid unbounded storage | TRD-VPS-010 + 30 days stable | same | Retention scripts/docs | No deletion before backup/restore | Cleanup plan and later execution evidence | Dry-run first | Dry-run lists only expected files | Retention applied or deferred | Restore from backup/keep JSONL | Backup/Restore Gate, Destructive Operation Gate | Dry-run, deleted paths, restore point | Any path ambiguity | Ecosystem implementation |

## Implementation Stop Conditions

Stop on any need for live scheduler mutation, VPS deploy, remote push, production DB access, production data movement, or destructive history cleanup without Buddy approval. Do not use the VPS as primary until `cloudscraper`, backup restore, parity, and fallback evidence are accepted.
