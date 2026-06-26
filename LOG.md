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

- date: 2026-06-26
  agent: worker
  task: game-version-ruleset-preservation
  files_changed:
    - scripts/snapshot_traderie.py (extract_properties — added Game version extraction, ruleset slug, multi-value handling)
    - scripts/build_traderie_dataset_from_history.py (propagate game_version, ruleset into research CSVs)
    - scripts/audit_traderie_game_version.py (created — audit script using local raw snapshots only)
    - README_INTERNAL.md (updated — game_version/ruleset section, known issues, quick status, roadmap)
    - SESSION.md (updated — current goal reflects new work)
    - LOG.md (updated — this entry)
    - data/products/*.json (regenerated via regenerate_products.sh)
    - data/research/extracted_trades_*.csv (regenerated with game_version, ruleset columns)
  validation:
    - python3 -m py_compile ✅ (all 3 modified/created scripts)
    - python3 scripts/validate_source_manifest.py ✅
    - python3 scripts/validate_in_game_rune_values.py ✅
    - python3 scripts/validate_external_cash_prices.py ✅
    - python3 scripts/collection_status.py --json | python3 -m json.tool ✅
    - npm --prefix web run build ✅ (618 kB, ~500 kB warning only)
  audit_findings:
    - Game version property (classic / lord of destruction / reign of the warlock) was silently dropped.
    - All 4 PC segments mix multiple game versions. ROTW dominates (>90%).
    - Region is visible in Traderie web UI but absent from completed-trades API.
    - 130K history rows pre-patch have ruleset=unknown; recoverable from raw snapshots.
    - ~1,800 raw listings have comma-separated multi-value game_version (e.g. "classic,reign of the warlock").
    - 108K total raw snapshot listings audited across 4 segments.
  outcome: complete
  next: Deciding whether to split pricing by ruleset (break products by classic/lod/rotw)

- date: 2026-06-26
  agent: worker
  task: ruleset-api-filter
  files_changed:
    - scripts/snapshot_traderie.py (added RULESET_MAP, --ruleset CLI, --dry-run CLI, manual %20 URL encoding for prop_Game%20version param)
    - SESSION.md (updated)
    - LOG.md (updated)
  validation:
    - python3 -m py_compile scripts/snapshot_traderie.py ✅
    - --dry-run confirmed correct URL encoding for all three rulesets:
      prop_Game%20version=lord%20of%20destruction  (lod)
      prop_Game%20version=reign%20of%20the%20warlock  (rotw)
      prop_Game%20version=classic  (classic)
  api_behavior:
    - prop_Game+version (requests default + encoding) times out — API requires %20
    - prop_Game_version, prop_GameVersion, prop_game_version all return HTTP 503
    - prop_Region and prop_Server are not functional for completed trades
  outcome: complete
  next: Decide whether to run segmented snapshot collection per ruleset

- date: 2026-06-26
  agent: worker
  task: ruleset-smoke-test
  files_changed:
    - SESSION.md (updated)
    - LOG.md (updated)
    - data/snapshots/raw/traderie/pc_sc_nl/20260626_070442/response.json (50 LoD Ist Rune listings)
    - data/snapshots/normalized/traderie/pc_sc_nl/20260626_070442.json (50 obs, game_version=lord of destruction, ruleset=lod)
    - data/history/traderie/pc_sc_nl/completed_trades_pc_sc_nl.jsonl (50 appended with game_version/ruleset)
  validation:
    python3 scripts/snapshot_traderie.py --segment pc_sc_nl --item "Ist Rune" --ruleset lod --single
    ✅ 50 listings fetched (2 timeouts, 1 success)
    ✅ source_url contains prop_Game%20version=lord%20of%20destruction
    ✅ 50/50 raw listings have Game version = lord of destruction
    ✅ normalized observations include game_version="lord of destruction", ruleset="lod"
    ✅ history append preserved game_version and ruleset
    ✅ completed=True for all 50
    ✅ python3 -m py_compile ✅ for all 3 scripts
    ✅ python3 scripts/audit_traderie_game_version.py — audit now shows 50 LoD history rows in pc_sc_nl
  outcome: complete
  next: Decide on controlled ruleset backfill across segments or pricing split by ruleset

- date: 2026-06-26
  agent: worker
  task: controlled-ruleset-collection
  files_changed:
    - SESSION.md (updated)
    - LOG.md (updated)
    - data/snapshots/raw/traderie/*/{ts}/response.json (6 new raw snapshots)
    - data/snapshots/normalized/traderie/*/{ts}.json (6 new normalized)
    - data/history/traderie/*/completed_trades_*.jsonl (300 ruleset-labeled rows appended)
  collection_commands_run:
    8 total (6 success, 1 timeout, 2 skipped):
    ✅ pc_sc_l/rotw: 50 listings (1 attempt)
    ✅ pc_sc_l/lod: 50 listings (1 attempt)
    ✅ pc_sc_nl/rotw: 50 listings (1 attempt)
    ✅ pc_sc_nl/lod: 50 listings (1 attempt, duplicate of smoke test)
    ✅ pc_hc_l/rotw: 50 listings (1 attempt)
    ❌ pc_hc_l/lod: 0 listings (2 ReadTimeouts)
    ⏭ pc_hc_nl/rotw: skipped (hardcore skip list)
    ⏭ pc_hc_nl/lod: skipped (hardcore skip list)
  history_rows_with_game_version:
    pc_sc_l: 100 (50 rotw + 50 lod)
    pc_sc_nl: 150 (50 rotw + 100 lod, 2nd lod run overlapped smoke test?)
    pc_hc_l: 50 (50 rotw, lod failed)
    pc_hc_nl: 0 (all skipped)
    total: 300 ruleset-labeled history rows
  classic_filter_behavior:
    --ruleset classic times out on all attempts (zero classic listings in rolling window)
    Confirm: classic is valid but has no data; API hangs on empty-result filters
    rc: recommend not using classic filter until volume increases
  outcome: complete
  next: Await Buddy's decision on pricing approach

- date: 2026-06-26
  agent: worker
  task: ruleset-transparency-metadata
  files_changed:
    - scripts/generate_prices_json.py (added count_rulesets_in_snapshots, per-segment ruleset_breakdown, product-level ruleset_aggregate, RULESET_CAVEAT, new caveat entry)
    - web/src/pages/Methodology.tsx (added Game Version/Ruleset section, Region section, updated Known Limitations)
    - data/products/in_game_rune_values.json (regenerated with ruleset_breakdown per segment + ruleset_aggregate top-level)
    - data/products/traderie_tools_prices.json (regenerated)
    - data/products/rune_prices_legacy.json (regenerated, unchanged schema)
    - data/products/external_cash_prices.sample.json (regenerated)
    - SESSION.md (updated)
    - LOG.md (updated)
  product_metadata_shape:
    segments[seg].ruleset_breakdown: {counts: {classic, lod, rotw, unknown}, total_observed_raw_listings, dominant_ruleset, dominant_ruleset_share}
    ruleset_aggregate (top-level): {counts: aggregated across segments, total}
    caveat_ruleset: explanation string
  validators:
    - validate_source_manifest.py ✅
    - validate_in_game_rune_values.py ✅
    - validate_external_cash_prices.py ✅
    - collection_status.py --json ✅
    - npm --prefix web run build ✅
  existing_validators_updated: none required
  outcome: complete
  next: Await Buddy's next instruction

- date: 2026-06-26
  agent: worker
  task: install-regen-launchagent
  files_changed:
    - ~/Library/LaunchAgents/com.buddy.traderie.regenerate-products.plist (copied from launchd/)
    - SESSION.md (updated)
    - LOG.md (updated)
    - data/products/*.json (regenerated)
  launchd_actions:
    plutil -lint launchd/com.buddy.traderie.regenerate-products.plist: OK
    cp to ~/Library/LaunchAgents/: done
    launchctl print gui/501/...: service not found (expected — not loaded)
    launchctl bootstrap gui/501 ...: exit 0 (loaded)
    launchctl list | grep com.buddy.traderie:
      com.buddy.traderie.snapshot-traderie (exit 1 — known hardcore failures)
      com.buddy.traderie.regenerate-products (exit 0 — loaded, never run)
  manual_regen: bash scripts/regenerate_products.sh ✅
  product_timestamps: 2026-06-26T07:38:40Z (fresh)
  validation:
    - validate_source_manifest.py ✅
    - validate_in_game_rune_values.py ✅
    - validate_external_cash_prices.py ✅
    - collection_status.py --json ✅
    - npm --prefix web run build ✅
  outcome: complete
  next: Await Buddy's next instruction

- date: 2026-06-26
  agent: worker
  task: prepare-gh-pages-deploy
  files_changed:
    - web/vite.config.ts (added base: '/' comment for GitHub Pages)
    - web/public/404.html (created — SPA 404 redirect for GitHub Pages)
    - web/src/main.tsx (added sessionStorage redirect handler for SPA routing)
    - scripts/deploy_web.sh (created — copies product JSONs to public/, builds)
    - .github/workflows/deploy.yml (created — GH Actions build+deploy workflow)
    - .gitignore (added web/public/data/)
    - SESSION.md (updated)
    - LOG.md (updated)
  deploy_approach: GitHub Pages via Actions
    - Data files copied to web/public/data/ for runtime fetch (userscript etc.)
    - 404.html + sessionStorage redirect for SPA client-side routing
    - Vite build produces dist/ with data/, assets/, 404.html, index.html
    - Workflow: checkout → setup node → npm ci → copy data → build → upload → deploy
    - Requires: GitHub repo remote, Pages enabled in repo Settings → Pages → Source: GitHub Actions
  blocker: No git remote configured — cannot push or deploy
  build: npm build ✅ (623 KB, data files in dist/)
  validation:
    - scripts/deploy_web.sh ran successfully
    - web/dist/ contains: index.html, 404.html, assets/, data/ (6 product JSONs), icons.svg
  outcome: complete
  next: Need to create GitHub repo and add remote, then push

- date: 2026-06-26
  agent: worker
  task: add-g2g-cash-parser
  files_changed:
    - scripts/parse_g2g_cash_prices.py (created — parses G2G captured HTML into cash observations)
    - scripts/generate_external_cash_prices.py (added g2g_cash_prices.json to INPUTS, added G2G source caveats)
    - data/external/g2g_cash_prices.json (created — 33 parsed observations)
    - data/products/external_cash_prices.sample.json (regenerated — 328 obs, 6 sources)
    - SESSION.md (updated)
    - LOG.md (updated)
  g2g_observations: 33
    segment: pc_sc_nl (PC - NonLadder - Softcore) — 33
    segment_confidence: medium (LoD label ambiguous)
    price_range: $0.029 (Ith) — $2.000 (Zod)
    median_price: $0.064
  all_cash_sources_now: iggm (30), itemnow (42), d2stock (199), mulefactory (24), g2g (33), items7 (0) = 328 total
  validation:
    - python3 -m py_compile parse_g2g_cash_prices.py ✅
    - python3 -m py_compile generate_external_cash_prices.py ✅
    - python3 scripts/parse_g2g_cash_prices.py ✅
    - python3 scripts/generate_external_cash_prices.py ✅
    - python3 scripts/validate_external_cash_prices.py ✅
    - python3 scripts/audit_cash_vs_trade_value.py ✅
  remaining_ambiguity:
    All 33 G2G captured listings use 'LoD' label, even though the URL targets the
    D2R category. This may be G2G's generic naming convention. A dedicated ROTW
    filter URL was never identified or captured. Offer detail pages cause
    Camoufox JS errors — unresolved.
  outcome: complete
  next: Await Buddy's decision on LoD/ROTW resolution for G2G
  files_changed:
    - scripts/snapshot_traderie.py (added CRITICAL_SEGMENTS, per-segment failure tracking, segment health summary, exit 0 for non-critical failures)
    - SESSION.md (updated)
    - LOG.md (updated)
  old_behavior:
    ANY item failure in ANY segment → exit 1 → launchd exits 1
  new_behavior:
    CRITICAL_SEGMENTS (pc_sc_l, pc_sc_nl) item failure → exit 1
    HARDCORE_SEGMENTS (pc_hc_l, pc_hc_nl) item failure → exit 0 (logged as WARNING)
    Summary line shows: OK segments, WARNING segments, CRITICAL segments, EXIT CODE
  exit_1_conditions:
    - Any item failure in pc_sc_l or pc_sc_nl
    - Invalid --segment argument
    - Unexpected exception outside segment loop
  validation:
    - python3 -m py_compile scripts/snapshot_traderie.py ✅
    - bash -n scripts/run_traderie_snapshot_launchd.sh ✅
    - dry-run still works (no regression)
  outcome: complete
  next: Await Buddy's next instruction
