# Source Manifest

## What It Is

`data/source_manifest.json` is the canonical ledger of every known D2R pricing and trade source. It tracks discovery status, extraction method, segment support, and next actions for each source.

## How to Add a New Source

1. Add an entry to `data/source_manifest.json` with all required fields.
2. Create a source notes file at `research/sources/{source_slug}.md` with detailed findings.
3. If static capture is possible, download the page and save to `research/sources/downloads/`.
4. If browser capture is required, create a capture artifact directory.
5. Run `python scripts/validate_source_manifest.py` to verify.
6. Run `python scripts/validate_source_manifest.py` after any update.

## Status Lifecycle

```
discovered → captured_static → offline_parse_candidate → parser_prototype_ready → integrated
          ↘ captured_browser ↗                                        ↘ rejected
          ↘ deferred (blocked or deferred)
          ↘ rejected (not usable)
```

| Status | Meaning |
|---|---|
| `discovered` | URL known, not yet downloaded or captured |
| `captured_static` | Static HTML downloaded to `research/sources/downloads/` |
| `captured_browser` | Rendered page captured via Camoufox to `research/sources/captures/` |
| `offline_parse_candidate` | Saved artifacts can be parsed for price data |
| `parser_prototype_ready` | Working parser script exists in `scripts/` |
| `integrated` | Source data flows into a production data product |
| `deferred` | Not currently actionable — revisit later |
| `rejected` | Not usable for this project |

## Source Surface Checklist

A mandatory source surface checklist that every source must pass before classification:

- active listings surface
- sold/completed listings surface
- price-check/history surface
- item-specific page surface
- search/filter URL params
- segment filters
- accepted consideration / sold-for field
- seller/buyer/time fields
- pagination/window behavior
- static/rendered/API parseability

D2R-specific search terms:
- sold
- completed
- recent trades
- price check
- historical prices
- WTS SOLD
- WTB SOLD
- sold for
- active
- ladder
- non-ladder
- hardcore
- softcore
- ROTW

## Evidence Class Definitions

| Class | Description | Example |
|---|---|---|
| `completed_player_trades` | Actual completed trades between players | Traderie API |
| `active_player_listings` | Current active listings asking for trades/sales | Traderie active listings |
| `forum_trade_posts` | Forum posts offering or seeking trades | d2jsp |
| `cash_market_listings` | Real-money marketplace listings (asking prices) | G2G, PlayerAuctions |
| `community_discussion` | Qualitative discussion about items, prices, economy | Reddit, Discord |
| `source_directory` | A directory or aggregator of other sources | d2stock |

## Segment Filter Rules

- Sources with segment filters can provide segment-specific prices.
- Sources without segment filters produce blended prices that may not reflect any real segment.
- Segment metadata: platform, ladder, hardcore, softcore, season, region.
- Missing segment metadata lowers confidence or excludes the observation.
- Do not merge segment data across sources unless explicitly modeling blended averages.

## Cash-Market Separation

Cash-market sources (G2G, PlayerAuctions, items7, etc.) are **comparison-only**:

- They show asking prices from sellers, not completed transactions.
- Prices may include transaction fees, minimum floors, and profit margins.
- They are not blended into the in-game rune value model.
- They are displayed on the website with clear labels: "Cash listing price — not in-game trade value."

## Completed-Trade / History Surface Tracking

Every source should track its completed-trade/history discovery status. The following fields are planned for future `data/source_manifest.json` schema expansion (not yet in validation — documented here as forward reference):

| Field | Type | Values |
|---|---|---|
| `completed_history_confidence` | string | `unknown`, `low`, `medium`, `medium_high`, `high` |
| `completed_history_last_checked` | string | ISO date or `none` |
| `completed_history_probe_status` | string | `not_started`, `partial`, `complete`, `gated`, `blocked` |
| `completed_history_notes` | string | Free-text finding summary |

Until these fields are added to the manifest JSON schema and validator, record completed-trade/history findings in the source notes file at `research/sources/{source_slug}.md` and in the memo `research/memos/2026-06-20-completed-trade-source-confidence-plan.md`.

## Agent Update Rules

When updating the manifest:

- Do not change status from `integrated` or `rejected` without review.
- Do not add sources without evidence artifacts (download, capture, or screenshot).
- Do not set `parser_prototype_ready` without a working parser script in `scripts/`.
- Add caveats for any known limitations (login required, dynamic prices, no segments).
- Run validation after every change.
