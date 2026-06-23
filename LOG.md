- date: 2026-06-21
  agent: orchestrator
  task: bootstrap-standard-files
  files_changed:
    - AGENTS.md (created)
    - SESSION.md (created)
    - LOG.md (created)
  validation: manual
  outcome: complete
  next: Await Buddy's next instruction

- date: 2026-06-21
  agent: orchestrator
  task: patch-agent-routing-contracts
  files_changed:
    - ~/.config/opencode/agents/orchestrator.md (Fast Path Routing + Git Routing sections)
    - ~/.config/opencode/agents/git-steward.md (objective, file classification, blockers protocol)
    - AGENTS.md (routing table updated)
  validation: frontmatter validated on both agent configs
  outcome: complete
  next: Buddy reviewing; remaining items: stale SESSION/LOG (now fixed), ~55 untracked files, PROJECT_MEMORY next actions out of date

- date: 2026-06-21
  agent: orchestrator
  task: review-recent-work-and-todos
  files_changed: none
  validation: manual
  outcome: deferred
  next: Buddy reviewing synthesized state below


- date: 2026-06-22
  agent: git-steward
  task: commit-pipeline-hardening
  files_changed:
    - data/products/in_game_rune_values.json
    - data/products/traderie_tools_prices.json
    - data/source_manifest.json
    - docs/COLLECTION_RUNBOOK.md
    - docs/DATA_PRODUCTS.md
    - docs/LAUNCHD_SETUP.md
    - docs/PRICING_MODEL.md
    - docs/PROJECT_MEMORY.md
    - docs/SOURCE_MANIFEST.md
    - scripts/calculate_rune_prices.py
    - scripts/fetch_completed_trades.py
    - scripts/generate_prices_json.py
    - scripts/snapshot_traderie.py
    - web/tsconfig.app.json
  commit: 4da026d
  validation: git status clean after commit
  outcome: complete

- date: 2026-06-22
  agent: git-steward
  task: commit-new-artifacts
  files_changed:
    - docs/OVERLAY_FEED_CONTRACT.md
    - docs/TRADERIE_COMPLETED_TRADES_AUDIT.md
    - docs/TRADERIE_NORMALIZED_SCHEMA.md
    - docs/TRADERIE_OVERLAY_PATCH_PLAN.md
    - docs/TRADERIE_TOOLS_INTEGRATION.md
    - docs/USERSCRIPT.md
    - scripts/build_traderie_dataset_from_history.py
    - scripts/collection_status.py
    - scripts/capture_with_camoufox.py
    - scripts/test_userscript_parse.py
    - data/products/rune_prices_legacy.json
    - research/memos/2026-06-20-*.md (10 files)
    - web/src/assets/hero.png
    - web/src/assets/vite.svg
  commit: ec026aa
  validation: git status clean after commit
  outcome: complete

- date: 2026-06-22
  agent: git-steward
  task: commit-agent-config
  files_changed:
    - AGENTS.md
    - SESSION.md
    - LOG.md
  commit: b5982e7
  validation: git status clean after commit
  outcome: complete

- date: 2026-06-22
  agent: git-steward
  task: commit-gitignore-update
  files_changed:
    - .gitignore (modified)
  commit: 9bd06c2
  validation: git status — working tree clean
  outcome: complete
  next: Await Buddy's next instruction

- date: 2026-06-22
  agent: orchestrator
  task: sync-tracking-files
  files_changed:
    - LOG.md (updated)
    - SESSION.md (updated)
  validation: manual
  outcome: complete

- date: 2026-06-22
  agent: git-steward
  task: commit-replace-roadmap
  files_changed:
    - docs/PROJECT_ROADMAP.md (replaced with concrete work sessions)
  commit: 14a7435
  validation: git status — working tree clean for committed file; scripts/snapshot_traderie.py remains unstaged
  outcome: complete

- date: 2026-06-22
  agent: orchestrator
  task: commit-snapshot-traderie-fixes
  files_changed:
    - scripts/snapshot_traderie.py (jitter + reduced hardcore attempts)
  validation: python compiles clean
  outcome: complete
  next: Await Buddy's next instruction

- date: 2026-06-22
  agent: git-steward
  task: commit-jitter-and-hardcore-attempts
  files_changed:
    - scripts/snapshot_traderie.py (jitter via random.uniform(0,2) on per-item delay; HARDCORE_REQUEST_MAX_ATTEMPTS=2)
    - LOG.md (updated)
  commit: 687e14b
  validation: git status — working tree clean; python compiles clean
  outcome: complete
  next: Await Buddy's next instruction
