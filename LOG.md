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


- date: 2026-06-22
  agent: git-steward
  task: move-ROADMAP-to-root
  files_changed:
    - docs/PROJECT_ROADMAP.md -> ROADMAP.md (renamed)
    - AGENTS.md (reference updated)
    - docs/ARCHITECTURE.md (reference updated)
    - docs/CODEX_HANDOFF.md (reference updated)
  commit: 27cf9fa
  validation: git status — working tree clean
  outcome: complete
  next: Await Buddy'''s next instruction

- date: 2026-06-22
  agent: git-steward
  task: mark-all-4-roadmap-sessions-complete
  files_changed:
    - ROADMAP.md (marked sessions 1-4 complete)
  commit: 409d6ff
  validation: git status — working tree clean
  outcome: complete
  next: Await Buddy'''s next instruction

- date: 2026-06-23
  agent: git-steward
  task: roadmap Session 1 (doc refresh) + Session 2 (AND trade decomposition)
  files_changed:
    - ROADMAP.md (roadmap modifications during execution)
    - docs/PROJECT_MEMORY.md (Section 10 replaced to point at ROADMAP.md)
    - docs/COLLECTION_RUNBOOK.md (snapshot-active text added, 2 occurrences)
    - docs/DATA_PRODUCTS.md (stale counts/timestamps: 2,570→1,151, 2026-06-20→2026-06-23)
    - data/source_manifest.json (d2stock→parser_prototype_ready, iggm/itemnow next_action updated)
    - scripts/build_traderie_dataset_from_history.py (added requested_groups and price_groups_json columns)
    - scripts/calculate_rune_prices.py (decomposes 2-item AND trades into model rows with audit flags)
    - scripts/generate_prices_json.py (caveats updated to reflect AND inclusion policy)
    - data/products/in_game_rune_values.json (regenerated with AND trades: 1,991 total modeled trades)
    - data/products/traderie_tools_prices.json (regenerated)
    - data/products/rune_prices_legacy.json (regenerated)
  commit: 169fc0b
  validation: git status — working tree clean (.agent-workflow/runs/roadmap-v2/ excluded)
  outcome: complete
  next: Await Buddy's next instruction

- date: 2026-06-23
  agent: orchestrator
  task: roadmap Sessions 3-6 (MuleFactory parser, operational hardening, hardcore probe, validation & cleanup)
  files_changed:
    - scripts/parse_mulefactory.py (created — 24 rune observations from Schema.org microdata)
    - data/external/mulefactory_cash_prices.json (created — 24 observations)
    - scripts/generate_external_cash_prices.py (updated — mulefactory added to inputs + caveats)
    - data/products/external_cash_prices.sample.json (regenerated — 295 obs, 5 sources)
    - scripts/regenerate_products.sh (created — full pipeline runner)
    - launchd/com.buddy.traderie.regenerate-products.plist (created — daily 06:00, com.buddy.traderie. namespace)
    - scripts/snapshot_traderie.py (pc_hc_nl skip list probed — 8/9 items ReadTimeout confirmed, restored)
    - logs/hardcore_probe_*.log (9 probe logs — 88.9% failure rate on pc_hc_nl skipped items)
    - BACKLOG.md (created — 6 one-line backlog entries)
    - LOG.md (updated — this entry)
    - ROADMAP.md (backlog references cleaned, checkbox text refined)
  validation: validate_source_manifest.py ✅ validate_in_game_rune_values.py ✅ validate_external_cash_prices.py (5 sources, 295 obs) ✅ npm build ✅ collection_status JSON valid ✅
  hitl_decisions:
    - Session 1: review checkpoint (confirmed)
    - Session 2: B — include AND trades, cap at 2-item requests, add audit flags
    - Session 3: review checkpoint (confirmed)
    - Session 4: B — separate daily launchd job at 06:00
    - Session 5: A — maintain skip list (confirmed API hang when no listings exist)
  outcome: complete
  next: Await Buddy's next instruction
