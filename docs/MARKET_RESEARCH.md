# Market Research

## Purpose

Market research informs the pricing pipeline by identifying what to model, how to model it, and where to find source data. Research outputs are qualitative and directional. They do not directly set prices.

## Phases

### Phase 1: Reddit (Complete)

**Goal:** Understand player language, trade venues, commonly traded items, and economy sentiment.

**Method:** Staged, human-gated Reddit collection using `tools/subreddit_research/`.

**Result:** 2,998 posts collected across r/D2R_Marketplace, r/Diablo_2_Resurrected, and r/diablo2. Comments were not fetched — direct market signal was too sparse to justify the API cost. See `research/memos/2026-06-20-reddit-pass-1-learnings.md` for full findings.

**Key outcomes:**
- Venue discovery: Traderie and Discord are the dominant trade venues mentioned. d2jsp/FG appears lightly on Reddit.
- Item candidates: Runewords (Enigma, Spirit, Grief) and uniques (SoJ, Arachnid Mesh, Maras) identified for profile creation.
- Currency units: PGems confirmed as relevant low-value pricing unit.
- Player language: "HR", "PGems", "PC" (price check) patterns captured in the item registry.

### Phase 2: Source/Site Discovery (Next)

Inspect downloaded pricing/trade sites to determine how rune prices and selected high-value item prices can be extracted or compared.

## Research Principles

1. **Slow collection over ban risk.** Reddit API calls are rate-limited. Comment fetching requires human approval.
2. **Staged and gated.** Posts first, browse second, comments third. Never fetch comments without a human selecting the post.
3. **Registry-backed.** All item mentions are matched against the canonical item registry (`data/item_registry/`). Unresolved terms are tracked for review.
4. **Qualitative, not quantitative.** Reddit findings inform what to model, not what price to set.
5. **Reusable tooling.** `tools/subreddit_research/` is portable. Copy it into any repo to run standalone Reddit research.

## Artifacts

| Path | Description |
|---|---|
| `research/reddit/raw/` | Raw post data (JSONL, one file per subreddit) |
| `research/reddit/selected/` | Filtered candidate lists for comment fetching |
| `research/reddit/notes/` | Analysis reports by pass |
| `research/reddit/exports/` | Exports for LLM consumption |
| `research/reddit/notes/` | Periodic summaries |
| `research/memos/` | Per-pass learning documents |
| `research/item_candidates/` | Items proposed for profile creation |
| `data/item_registry/` | Canonical item registry built from catalogue + research |

## Tools

| Path | Description |
|---|---|
| `tools/subreddit_research/` | Portable CLI for Reddit data collection (4 phases) |
| `scripts/reddit_extract_items.py` | Registry-based item term extraction |
| `scripts/validate_item_profiles.py` | Validates item profile completeness |

## Source Signals

| Source | Used For | Status |
|---|---|---|
| Traderie API | Primary pricing data (completed trades) | Active |
| Traderie catalogue | Item registry (1,328 items) | Active |
| Reddit | Venue/term discovery, item candidates, sentiment | Phase 1 complete |
| diablo2.io | Potential secondary source | Not yet evaluated |
| d2jsp | Secondary pricing reference (FG) | Research only |
| RMT sites | External cash-market reference | Research only |

## Decision Record

| Date | Decision | Rationale |
|---|---|---|
| 2026-06-20 | Defer Reddit comment fetch | 8 direct-market candidates from 2,998 posts. Expected yield too low. |
| 2026-06-20 | Next phase: site/source discovery | Downloaded pricing sites may contain structured or semi-structured price data for runes and high-value items. |
