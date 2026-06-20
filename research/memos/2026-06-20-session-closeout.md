# Session Closeout — 2026-06-20

## Summary

This session covered Reddit pass 1 closure, item registry + profile creation, source discovery via static and browser captures, and the first external cash-price parser prototype.

## Key Deliverables

### Pipeline & Data Layer
- Item registry: 1,328 canonical items + 35 aliases (`data/item_registry/`)
- Item profiles: 12 draft profiles (`data/item_profiles/`)
- External cash price parser: IGGM, 30 runes (`data/external/iggm_cash_prices.json`)
- Normalized product file: `data/products/external_cash_prices.sample.json`
- Source manifest: 20 sources (`data/source_manifest.json`)
- `.gitignore` configured for raw/research/private data

### Research Artifacts
- Reddit pass 1: 2,998 posts across 3 subreddits. Comments not fetched — direct market signal too thin.
- Source discovery: 10 cash-market sites inspected. 5 browser captures completed.
- Source manifest: 20 seeded sources with status, priority, and extraction methods.
- Captures saved under `research/sources/captures/` (6 capture directories).

### IGGM Rune Prices (Focused Capture)

**URL:** https://www.iggm.com/d2-resurrected-items
**Segment:** PC / Non-Ladder / Softcore / ROTW
**Segment confidence:** low → high (improved during session)
**Row count:** 30 runes

| Rune | Cash Price |
|---|---|
| Zod | $8.99 |
| Cham | $4.99 |
| Jah | $7.90 |
| Ber | $7.29 |
| Sur | $4.29 |
| Lo | $2.79 |
| Ohm | $1.79 |
| Vex | $0.89 |
| Gul | $0.39 |
| Ist | $0.49 |
| Mal | $0.29 |
| Um | $0.19 |
| Pul | $0.22 |
| Lem–Ko–Fal–Lum | $0.12 |
| Hel–Nef (10 low runes) | $0.09 |

**Caveat:** Cash-market comparison only. Not in-game ratio data. Prices are asking prices, not completed sales.

### Validation Results
- `validate_source_manifest.py`: ✅ 20 sources valid
- `validate_external_cash_prices.py`: ✅ All checks passed
- `validate_item_profiles.py`: ✅ 12 profiles valid

### Source Manifest Status (Key Sources)

| Source | Status | Priority |
|---|---|---|
| traderie | integrated | tier_1 |
| iggm | parser_prototype_ready | tier_2 |
| items7 | captured_static | tier_2 |
| g2g | captured_browser | tier_2 |
| playerauctions | captured_browser | tier_2 |
| odealo | captured_browser | tier_3 |
| yesgamers | deferred | tier_3 |

## Docs Created/Updated

| Doc | Purpose |
|---|---|
| `docs/PROJECT_ROADMAP.md` | Product vision, 5 phases, invariants |
| `docs/ARCHITECTURE.md` | Segment model, evidence classes, data flow, directory tree |
| `docs/PRICING_MODEL.md` | Pricing principles, current model, future improvements |
| `docs/DATA_PRODUCTS.md` | 6 planned output schemas with consumer matrix |
| `docs/CODEX_HANDOFF.md` | Codex opening prompt, invariants, files to inspect, first tasks |
| `docs/MARKET_RESEARCH.md` | Research methodology, phases, decision record |
| `docs/SOURCE_DISCOVERY.md` | Source comparison table, extraction summary, priority |
| `docs/SOURCE_MANIFEST.md` | Manifest docs, status lifecycle, evidence class definitions |
| `docs/ITEM_REGISTRY.md` | Registry schema, source priority, LLM policy |
| `docs/ITEM_PROFILES.md` | Profile schema, confidence levels, usage |
| `docs/REDDIT_RESEARCH_PLAN.md` | Reddit collection policy, item profile extraction |

## Next-Session Checklist

1. **items7 browser capture** — Render per-rune prices. The static capture lacks extractable data. 30-second Camoufox capture likely yields clean prices. This is the last hole in external_cash_prices v0.

2. **IGGM segment variation** — Capture a different filter combination (e.g. PC Ladder Hardcore) to test whether segment filters affect displayed prices.

3. **Odealo rune category page** — Capture `/games/diablo-2/marketplace/runes` to verify per-rune prices render (prices were visible on the general items page).

4. **PlayerAuctions rune search** — Capture a rune-specific URL to see listing prices (homepage showed navigation items, not rune data).

5. **G2G LoD/RoTW ambiguity** — Deferred. Offer detail pages caused browser errors. Category page works but segment labels are ambiguous.

6. **Diablo2.io evaluation** — Visit and classify. Not yet inspected.

7. **d2jsp evaluation** — Research whether price-check forum is accessible without login.

## Session Stats

- Pipeline scripts: 3 (extract, calculate, check) — unchanged
- Pipeline runs: tested, working
- Browser captures: 6 (G2G ×2, PlayerAuctions, YesGamers, Odealo, IGGM ×2)
- Capture artifacts: ~5 MB total (HTML + screenshots + metadata)
- Parser scripts: 3 (IGGM, items7, external cash prices generator)
- Validator scripts: 3 (item profiles, source manifest, external cash prices)
- New documentation: 10 docs + 5 source reports + 5 memos
