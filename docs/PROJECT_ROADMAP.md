# D2R Market Helper — Project Roadmap

## Product Vision

Multi-source market intelligence hub for Diablo II: Resurrected traders.
Traderie-normalized in-game rune values + multi-source external cash comparison
+ source transparency ledger.

### Core Rules

- In-game values and cash prices are always separate.
- Never blend cash-market prices into in-game rune ratios.
- Economy segments (PC SC L, PC SC NL, PC HC L, PC HC NL) are never merged.
- Every displayed number visibly tied to segment, source, evidence class, and confidence.
- Cash observations always `use_in_model=false`.

---

## Progress Summary

| Area | Status |
|------|--------|
| Traderie pipeline | Active — 4 segments, 4x daily snapshots, 3+ days of accumulated history |
| External cash parsers | ItemNow ✅, D2Stock ✅, IGGM ✅, items7 ⏳ |
| Source manifest | 20 sources, all validated |
| Snapshot/history infrastructure | Active — raw, normalized, history JSONL per source |
| Collection status script | Active |
| Website (Vite + React) | Scaffolded — 0 tsc errors, production ~100KB gzip |
| Agent routing contracts | Updated — Fast Path Routing, Git Routing, git-steward objective |

---

## Proposed Work Sessions

### Session 1 — Regenerate Products from Accumulated History

History has grown massively since the last product generation (2026-06-20).
Regenerate using the full accumulated dataset.

- [ ] Run `build_traderie_dataset_from_history.py --write-research`
- [ ] Run `calculate_rune_prices.py --input-dir data/research`
- [ ] Run `generate_prices_json.py`
- [ ] Compare observation counts vs last generation
- [ ] Validate output: `validate_in_game_rune_values.py`
- [ ] Validate output: `validate_external_cash_prices.py`
- [ ] #driver: worker

### Session 2 — Hardcore Segment Reliability

Despite the retry/backoff fix and 30s timeout, hardcore segments still fail
intermittently (16 ReadTimeouts, exit code 1 on recent runs).

- [ ] Monitor 2-3 launchd cycles after jitter + reduced-attempts fix
- [ ] If still failing: add skip list for items that consistently time out on hardcore
- [ ] Collect timeout stats per item to identify problem items
- [ ] Consider reducing hardcore timeout further (20s) if items either respond or don't
- [ ] #driver: orchestrator → git-steward for monitoring, worker for code changes

### Session 3 — Cash Source Snapshot Integration

D2Stock and IGGM parsers don't call `snapshot_io` yet. Adding snapshot
integration gives them the same history accumulation as Traderie and ItemNow.

- [ ] Add `snapshot_io.write_raw_snapshot()` to `parse_d2stock_rss.py`
- [ ] Add `snapshot_io.write_normalized_snapshot()` to `parse_d2stock_rss.py`
- [ ] Add `snapshot_io.append_history()` to `parse_d2stock_rss.py`
- [ ] Same for `parse_iggm_offline.py`
- [ ] Re-run both parsers, verify history files created
- [ ] Update `collection_status.py` to detect new cash source snapshots
- [ ] #driver: worker

### Session 4 — UI Polish

The Vite + React dashboard is scaffolded but minimal. Priority additions:

- [ ] Source freshness indicators (last snapshot time per source)
- [ ] Confidence tooltips on rune prices (high/medium/low/unavailable)
- [ ] Segment selector persistence via URL
- [ ] Responsive layout fixes (test at mobile widths)
- [ ] Cash price comparison panel (read-only, labeled)
- [ ] #driver: worker

### Session 5 — Optional: MuleFactory/Eldorado Cash Parsers

Cash coverage is already strong (271 obs). Add only if specific segment gaps emerge.

- [ ] Evaluate need: which segments lack cash coverage?
- [ ] If needed: write offline parser for MuleFactory (static microdata)
- [ ] If needed: write offline parser for Eldorado (rendered HTML)
- [ ] #driver: worker (only if gaps exist)

### Session 6 — Optional: Diablo2.io Price-History Probe

The `misc/jah-t43.html` page shows "Total results: 2812" — potentially more data
than the sold-search surface (max 14 rows). Low priority.

- [ ] Scope the price-history page format
- [ ] Compare row quality vs sold-search surface
- [ ] If viable: write explorer script
- [ ] #driver: worker (low priority)

---

## Invariants

- Never merge segments. PC SC L is a separate economy from PC SC NL.
- Never blend cash/RMT prices into in-game rune values. Cash is comparison-only.
- Every price observation must carry segment metadata (platform, mode, ladder, hardcore).
- Missing segment metadata lowers confidence or excludes the observation.
- Reddit/community mentions are qualitative only — not pricing data.
- Active listings are not completed trades.
- Public-facing data must be schema-versioned.
- Raw and intermediate data stay private (gitignored).
- Do not run launchctl mutations unless explicitly asked.
