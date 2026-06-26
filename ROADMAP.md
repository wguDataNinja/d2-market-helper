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

## Completed Sessions

| Session | Topic | Status | Key Result |
|---------|-------|--------|------------|
| 1-6 | Original roadmap (doc refresh, AND trades, MuleFactory, ops, hardcore, validation) | ✅ Done | Pipeline running, products generated |
| 7 | Game version / ruleset preservation | ✅ Done | game_version+ruleset in pipeline, products, API filter |
| 8 | Exit code hardening | ✅ Done | Softcore critical (exit 1), hardcore warning (exit 0) |
| 9 | Regen launchd plist | ✅ Done | Bootstrapped and loaded, daily 06:00 |
| 10 | GH Pages deploy prep | ✅ Done | Workflow, SPA fallback, deploy script, methodology |
| 11 | Non-Ist pair audit | ✅ Done | 4,995 trades analyzed, Jah↔Ber divergence confirmed |
| 12 | Graph pricing v1 | ⚠️ Research | scipy_nnls, Jah/Ber signal, unstable (collapsed pc_sc_nl) |
| 13 | Userscript patch | ✅ Done | Cache, segment safety, complexity labels, SPA hooks |
| 14 | G2G cash parser | ✅ Done | 33 obs, pc_sc_nl, lowest_available_ask |
| 15 | Cash vs trade audit | ✅ Done | All 6 sources, min-based ranking, G2G integrated |

---

## Remaining Before Website Alpha

1. ✅ Commit current cash/G2G/model-audit work (Git Steward)
2. 🔲 Verify launchd jobs after next scheduled runs
3. 🔲 Create/connect GitHub remote
4. 🔲 Push master and enable GitHub Pages
5. 🔲 Verify deployed site

## Post-Alpha Backlog

See `BACKLOG.md` for deferred and candidate work.
