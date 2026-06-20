# Source Discovery

Last updated: 2026-06-20

## Purpose

This document tracks pricing/trade sources that have been inspected, their utility for the project, and whether they should be integrated into the pricing pipeline.

## Source Ratings

| Source | Type | Rune Prices | Item Prices | Segments | Rating |
|---|---|---|---|---|---|
| **Traderie API** | Completed trades | Yes (structured) | Some | Yes | **Production** |
| Traderie (web) | Trade platform | No (dynamic) | No | — | Not needed (API covers it) |
| PlayerAuctions | Cash marketplace | Yes (listing data) | Yes | Yes | **Cross-ref** |
| Odealo | Cash marketplace | No (dynamic) | No | Excellent | **Cross-ref** |
| items7 | Cash marketplace | Yes (visible $) | No | Basic | **Cross-ref** |
| **IGGM** | Cash marketplace | **Yes (parser ready)** | No | **Yes (PC/NL/HC/ROTW)** | **Cross-ref ✅** |
| AOEAH | Cash marketplace | Partial | No | Good | Inspect further |
| YesGamers | Cash marketplace | No (dynamic) | Some | Excellent | Needs JS |
| d2items_for_sale | WordPress/RMT | Partial | No | Good | WP API candidate |
| **G2G** (browser capture) | Cash marketplace | **Yes (rendered)** | No | Partial (embedded in titles) | **Cross-ref** |

## Segmentation Support

Market segmentation across sources:

| Source | Ladder/NL | SC/HC | Platform | Season |
|---|---|---|---|---|
| Traderie API | Yes | Yes | Yes | N/A |
| PlayerAuctions | Yes | Yes | Yes | Yes (s14) |
| Odealo | Yes | Yes | Yes | Yes (s14/rotw) |
| YesGamers | Yes | Yes | Yes | Yes (UI toggle) |
| IGGM | Yes | Yes | Yes | Yes (rotw/s14) |
| items7 | Yes | No | No | Yes (rotw) |
| AOEAH | Yes | No | Yes | Yes |
| **G2G** | Partial (in titles) | Partial (in titles) | Yes | No (uses LoD/ROTW) |

## Price Extraction Summary

### Traderie API (Primary — Already Integrated)

Completed trades API provides structured rune-for-rune swap data. This is the **source of truth for relative rune ratios.** No cash prices involved.

### Cash/RMT Sites (Cross-Reference Only)

These sites sell runes for real money. They are useful for:
- Confirming whether relative rune ratios match cash price ratios
- Detecting divergence (e.g., Jah costs more than Ber in cash but trades for fewer Ist)
- Understanding segment pricing (ladder vs non-ladder differences)

Extractable cash prices found:
- **IGGM**: $0.09–$8.99 per rune, 30 runes, segment PC/NL/SC/ROTW (parser ready ✅)
- **items7**: $0.15–$2.85 per rune (static HTML, needs browser render for per-rune mapping)
- **PlayerAuctions**: $27.54–$1,999.00 per listing (structured `data-bind` attributes)
- **G2G**: $0.029+ per rune (browser-captured rendered HTML; segment info embedded in listing titles)

### API Endpoints Discovered

| API | Source | Notes |
|---|---|---|
| `https://user-api.playerauctions.com/` | PlayerAuctions | Potential listing data |
| `https://public-api.playerauctions.com/` | PlayerAuctions | Potential listing data |
| `https://account-api.playerauctions.com/` | PlayerAuctions | Account/auth |
| `https://itemnow.com/wp-json/wp/v2/` | itemnow.com | WordPress REST API |

## Modeling Rule

**Direct in-game completed trades (Traderie API) are the source of truth for relative rune ratios.**

Cash/RMT sites are for cross-site price comparison and divergence analysis only. Do not blend cash prices into the relative rune model.

## Priority for Next Downloads

1. **G2G (ROTW filter)** — Determine whether "LoD" label is classic D2 content or G2G's generic naming. A filter for D2R/ROTW-only runes exists but needs the correct `fa` parameter.
2. **PlayerAuctions** — rune search results page to see rendered listing prices
3. **Odealo** — rune listing pages (may have server-rendered prices even if the category page doesn't)
4. **items7** — individual rune product pages to get per-rune price mapping
5. **itemnow.com** — WP REST API root (`/wp-json/`) to discover structured product endpoints
6. **IGGM** — individual rune product pages
