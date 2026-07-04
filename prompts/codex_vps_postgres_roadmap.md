# Codex Prompt: Traderie VPS + PostgreSQL Infrastructure Roadmap

## Shared Conventions Reference

Before reading other context, read `/Users/buddy/projects/ivy-control/vps/shared-conventions.md`. It defines cross-repo defaults for: database isolation (database-per-project), role naming (`{project}_writer`, `{project}_reader`, `{project}_monitor`, `{project}_migrator`), migration file layout (`db/migrations/YYYYMMDD_NNN_description.sql`), environment variable naming, VPS filesystem layout, systemd naming (`{project}-{role}-{action}`), health contract format, backup destination (`~/projects/backups/postgres/{project}/`), branch/PR ownership, Hermes conventions, and gate terminology.

Align every decision with these conventions. Justify any deviation explicitly.

**Evidence hierarchy:** Treat the discovery packet as derived evidence, not proven fact. Inspect the actual repo files to confirm every claim. Clearly distinguish: (a) verified facts from repo inspection, (b) inferred conclusions, (c) open decisions requiring Buddy input.

## Mission

Inspect the discovery packet at `_outbox/codex_input_packet_2026_07_04.md` and the relevant source files in the Traderie repo, then create an implementation-level infrastructure roadmap for VPS migration and PostgreSQL integration.

## Constraints

1. The existing product roadmap (`ROADMAP.md`) is authoritative and ~85-90% complete. Do not replace, disrupt, or merge it.
2. Deterministic filtering remains authoritative. Detector/LLM outputs remain advisory.
3. D6 (detector-to-legacy-filter adapter) remains the main repo-local roadmap item. Do not expand or alter D6 scope.
4. Production detector integration is not approved. Do not plan for it.
5. Never blend cash-market prices into in-game rune values.
6. Economy segments are never merged.
7. Do not run git. Do not commit. Do not alter scheduler state. Do not change VPS configuration. Do not deploy.

## Full VPS Role Classification

Classify every meaningful Traderie workflow (API snapshot 4x daily, product regeneration, cash source parsing, hardcore segment monitoring, health check, backup, export generation) into exactly one category from shared-conventions §1 (1=VPS-ready now, 2=shadow/parity, 3=HITL gate, 4=hardening, 5=local long-term, 6=deferred, 7=unclear).

Consider more than ingestion: acquisition, normalization, deterministic enrichment, validation, regeneration, exports, notifications, static builds, branch/PR creation, health checks, backups, restore verification, retries, recovery.

## Decision Required

Choose between:

**Option A — Add infrastructure track to root ROADMAP.md**

Add a clearly separated "Infrastructure Track" section to the existing `ROADMAP.md`. Preserve all existing content (sessions 1-15 + remaining alpha items + backlog). The infrastructure section must be visually distinct (e.g., a separate heading level or divider) and explicitly scoped as a companion track that does not alter product goals.

**Option B — Create companion infrastructure roadmap**

Create `ROADMAP_INFRASTRUCTURE.md` at the repo root. This avoids any risk of damaging or obscuring the authoritative product roadmap. The companion file cross-references `ROADMAP.md` but does not edit it.

**Recommendation criteria:**
- Is the existing ROADMAP.md structured enough that an additional section would be clearly separable?
- Would adding to ROADMAP.md risk accidental edits, confusion, or loss of focus?
- Is there precedent in the repo for companion docs (e.g., BACKLOG.md is separate)?

State which option you recommend and why. Be explicit about the risk assessment.

## Required Phases

Every phase must include: **objective, exact files/directories, worker-sized tasks, reliable commands, SQL/migration artifacts, services/timers affected, tests, validation, rollback plan, dependencies, approval gates, completion criteria, and handoff notes.**

### Phase 1: Current-state verification

- Verify both launchd jobs are loaded and have recent successful runs.
- Verify all 4 product files are current and valid.
- Check `git status` is clean.
- Document the current `data/history/`, `data/snapshots/`, `data/research/` sizes.
- Capture the current pipeline's behavior (exit codes, error patterns, hardcore status).
- Verify cloudscraper works on target VPS (Ubuntu 24.04 LTS, Hetzner CX23).

### Phase 2: Existing-roadmap preservation

- Archive a snapshot of `ROADMAP.md` (read-only copy) before any modifications (if Option A chosen).
- Document the pre-migration state in a durable reference doc.
- Lock the existing product roadmap's authority in a doc: no infrastructure change can alter product pricing, segment separation, or cash/trade separation.

### Phase 3: GitHub-readiness cleanup

- Create `README.md` (public-facing, minimal — repo purpose, status, usage).
- Add LICENSE (MIT recommended).
- Verify `.gitignore` covers: `data/history/`, `data/snapshots/`, `data/research/`, `logs/`, `web/dist/`, `research/sources/captures/`, `.run/`.
- Remove any `/Users/buddy/` hardcoded paths from committed files (plists, scripts) or document them as Mac-local.
- Verify no secrets in git history.
- Run the GitHub Readiness Checklist from `ivy-control/ivy-vps/github-readiness-checklist.md`.
- Create the GitHub remote (`buddyowens/traderie`) — do NOT push yet (deferred).

### Phase 4: Data-contract stabilization

- Define explicit schemas for each data class (see discovery packet §9).
- Create `docs/data-contract.md` with table-like definitions for PostgreSQL planning.
- Identify which fields are required for dual-write parity.
- Identify which fields are advisory/detector-specific (must be clearly separated).
- Define `evidence_class` enum values.
- Define `segment_slug` validation constraints.

### Phase 5: PostgreSQL infrastructure prerequisites

- Install PostgreSQL on Mac (test/dev) and VPS (production).
- Create databases: `traderie_production` (VPS), `traderie_development` (Mac).
- Create least-privilege roles: `traderie_writer`, `traderie_reader`, `traderie_admin`, `hermes_readonly`, `dashboard_public`.
- Create migration directory: `data/migrations/`.
- Set up `psql` connection configs (separate `.env` for each environment, gitignored).

### Phase 6: Schema and migration design

- Design tables per discovery packet §9:
  - `sources` (source_slug PK, display_name, category, priority, extraction_method, evidence_classes, caveats)
  - `segments` (segment_slug PK, platform, mode, ladder, hardcore)
  - `items` (item_id PK, name, category, traderie_api_id)
  - `observations` (id UUID PK, source_slug FK, segment_slug FK, item_name, listing_id, seller, price JSONB, game_version, ruleset, platform, mode, ladder, captured_at, fetched_at, evidence_class, source_confidence, raw_payload_ref, content_hash SHA256, schema_version)
  - `completed_trades` (id UUID PK, observation_id FK, segment_slug FK, item_name, buyer, seller, prices JSONB, trade_date, listing_id UNIQUE, captured_at, fetched_at, evidence_class, content_hash)
  - `price_snapshots` (id UUID PK, segment_slug FK, generated_at, product_version, price_data JSONB, model_params JSONB, run_id FK)
  - `ingestion_runs` (id UUID PK, job_type enum(snapshot, regen, manual), segment_slug, started_at, completed_at, duration_seconds, items_fetched, items_succeeded, items_failed, exit_code, poetry_lock_version)
  - `fetch_errors` (id UUID PK, run_id FK, segment_slug FK, item_name, error_class, error_message, url, http_status, timestamp, resolved BOOLEAN default false)
  - `detector_findings` (id UUID PK, observation_id FK, detector_name, finding_type, confidence, detail JSONB, created_at, reviewed BOOLEAN default false, human_review_notes)
  - `deterministic_decisions` (id UUID PK, decision_type, parameters JSONB, applied_at, affected_range, run_id FK)
  - `advisory_classifications` (id UUID PK, observation_id FK, classifier_name, classification, confidence, model_version, created_at)
  - `review_outcomes` (id UUID PK, finding_id FK, reviewer, outcome enum(accept, reject, escalate), notes, reviewed_at)
  - `health_records` (id UUID PK, check_type, result JSONB, checked_at, healthy BOOLEAN)
  - `exports` (id UUID PK, product_slug, generated_at, content_hash SHA256, size_bytes, record_count, segments_included)
- Create initial migration: `data/migrations/001_initial_schema.sql`.
- Add schema version tracking table.
- Define indexes: observation timestamps, segment_slug lookup, listing_id unique, run timing queries.

### Phase 7: Historical-data migration

- Write migration script: `scripts/migrate_history_to_postgres.py` that reads `data/history/traderie/*/completed_trades_*.jsonl` and inserts into PostgreSQL.
- Write migration script: `scripts/migrate_snapshots_to_postgres.py` for normalized snapshots.
- Write import script for `data/source_manifest.json` → `sources` table.
- Handle deduplication (existing JSONL dedup key survives).
- Log import stats (rows read, inserted, skipped, errors).
- Validate row counts match between PostgreSQL and JSONL.

### Phase 8: Dual-write or parity validation

- Modify `snapshot_io.py` to dual-write to both JSONL and PostgreSQL.
- Add `ingestion_runs` record on each snapshot/regen run.
- Add `fetch_errors` records on each failed item.
- Run shadow mode for minimum 7 days.
- Compare product generation output (pre- and post-dual-write) is identical.
- Parity check script: `scripts/check_jsonl_pg_parity.py` — compares observation counts, content hashes, newest timestamps.

### Phase 9: VPS deployment decision

- Test cloudscraper on VPS (Ubuntu 24.04, Python 3.12+).
- Deploy Traderie code to VPS: `/home/scraper/apps/traderie/` (clone from GitHub).
- Deploy PostgreSQL on VPS.
- Deploy snapshot wrapper as a systemd timer (4x daily) or cron.
- Deploy regen wrapper as systemd timer (daily).
- Wire logging: VPS launchd-equivalent output.
- Wire Mac fallback: Mac monitors VPS export/health and runs snapshot if VPS misses 2 consecutive cycles.
- Keep Mac launchd jobs as fallback (disable schedule, keep loaded).

### Phase 10: Scheduler migration or retention

- **Recommendation: Migrate to systemd timers on VPS for production; keep Mac launchd as fallback.**
- Create `scripts/deploy/vps/traderie-snapshot.service` + `.timer` (4x daily).
- Create `scripts/deploy/vps/traderie-regen.service` + `.timer` (daily at 07:00 UTC, after snapshot).
- Mac launchd: disable schedule but keep loaded. Mac detects VPS export freshness and runs fallback if stale.
- Fallback threshold: VPS export older than 26 hours → Mac runs fallback snapshot.

### Phase 11: Backup and restore

- VPS PostgreSQL: `pg_dump` daily via systemd timer → gzip → SCP to Mac.
- Mac: store compressed dumps in `/Users/buddy/backups/postgres/traderie/`.
- Retention: keep last 30 daily dumps, 12 monthly.
- Restore procedure: `pg_restore` on Mac dev DB.
- Document restore steps in `docs/DISASTER_RECOVERY.md`.

### Phase 12: Health/dashboard integration

- Create health endpoint or export: `scripts/health_report.py` → JSON → served or synced.
- Required metrics: last snapshot timestamp per segment, last regen timestamp, product staleness hours, error count (last 24h), hardcore success rate, history size, snapshot size.
- Wire data into `ivy-control` health dashboard (reference `ivy-control/docs/idlehacker_dashboard.md`).
- Wire Hermes read-only access to health data (future).

### Phase 13: Hermes integration

- Hermes can read: `health_records`, `ingestion_runs`, `fetch_errors` (read-only, via `hermes_readonly` role).
- Hermes can: open GitHub issues if hardcore failure rate >50% for 48h, if product staleness >48h, if PostgreSQL backup age >30h.
- Document Hermes access pattern in `docs/HERMES_ACCESS.md`.
- Hermes integration is optional and non-blocking. Deploy without Hermes first.

### Phase 14: Legacy-path retirement

- After 30 days of confirmed parity:
  - Stop JSONL writes from `snapshot_io.py` (keep reading for back-compat).
  - Archive `data/history/` to cold storage.
  - Archive `data/snapshots/` (keep last N raw snapshots for debugging).
  - Update `snapshot_io.py` to PostgreSQL-only mode.
- Document legacy data removal in `LOG.md`.

### Phase 15: Production cutover gates

Each gate requires explicit human approval:

| Gate | Criteria | Approver |
|------|----------|----------|
| G1: GitHub ready | All Phase 3 checks pass | Buddy |
| G2: Schema approved | All PostgreSQL tables reviewed, indexes correct | Buddy + Codex review |
| G3: Dual-write parity | 7 days of parity, zero data loss | Buddy |
| G4: VPS ready | VPS tests pass, systemd timers loaded | Buddy |
| G5: VPS primary | VPS running 7 days with Mac fallback untriggered | Buddy |
| G6: Backup verified | Restore test passes on Mac dev DB | Buddy |
| G7: Legacy retire | 30 days of stable PostgreSQL-primary operation | Buddy |

## Output Format

Return the chosen roadmap file as a complete `ROADMAP.md` update (Option A) or new `ROADMAP_INFRASTRUCTURE.md` (Option B). Include:

1. Your recommendation and reasoning for Option A vs B.
2. The complete roadmap file content.
3. A diff summary showing what would change (if Option A).
4. A dependency graph between phases (which phases can run in parallel vs sequential).
5. Estimated effort per phase (Small: <2h, Medium: 2-8h, Large: 8-40h).
6. Risk rating per phase (Low/Medium/High).
7. Any conflicts with the existing product roadmap.
8. Any unanswered questions that blocked your recommendation.

## Files to Inspect

Read the discovery packet first, then inspect these Traderie source files:

```
ROADMAP.md                — Existing roadmap structure
BACKLOG.md                — Post-alpha backlog
README_INTERNAL.md        — Comprehensive internal state
AGENTS.md                 — Agent contract
SESSION.md                — Current state
LOG.md                    — Activity history
launchd/*.plist           — Launchd job definitions
scripts/snapshot_traderie.py    — Primary collector
scripts/lib/snapshot_io.py      — I/O patterns
scripts/regenerate_products.sh  — Regen pipeline
scripts/calculate_rune_prices.py   — Pricing logic
scripts/generate_prices_json.py    — Product generation
scripts/generate_external_cash_prices.py — Cash gen
scripts/collection_status.py    — Health reporting
scripts/deploy_web.sh           — Deploy script
data/products/in_game_rune_values.json        — Primary product
data/products/external_cash_prices.sample.json — Cash product
data/source_manifest.json       — Source manifest
server_configs.json             — Segment config
docs/DATA_PRODUCTS.md           — Product schemas
docs/ARCHITECTURE.md            — Architecture
docs/PROJECT_MEMORY.md          — Repo state
.gitignore                      — Current ignores
.github/workflows/deploy.yml    — GH Actions (never run)
```

And these ecosystem context files:

```
_outbox/codex_input_packet_2026_07_04.md       — THIS PACKET
ivy-control/vps/README.md                      — VPS transition plan
ivy-control/vps/vps-host.md                    — VPS identity
ivy-control/vps/shared-conventions.md          — Shared conventions
ivy-control/vps/VPS_MIGRATION_STATUS.md        — Migration sequencing
ivy-control/repo-operating-standard.md         — Repo standard
ivy-control/github-readiness-checklist.md      — GitHub gate
```

## Do Not

- Do not run any code or commands.
- Do not modify any files.
- Do not create any GitHub remote.
- Do not deploy anything.
- Do not change any scheduler or VPS state.
- Do not alter detector/filter authority.
- Do not push to git.
- Do not commit.
- Do not execute Codex.
