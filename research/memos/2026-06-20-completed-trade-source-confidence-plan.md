# Completed-Trade Source Confidence Plan

Date: 2026-06-20
Status: Plan document — not yet executed
Target: Raise confidence that all main public/semi-public completed-trade/history sources have been found

---

## A. Objective

Raise confidence from **low-to-moderate** to **medium-high** that the project has found the main public/semi-public completed-trade and trade-history surfaces for D2R.

Completed-trade surfaces are defined as: pages, APIs, feeds, or archives that expose actual completed player-to-player trades (not active listings, not cash asking prices). Trade-history surfaces are defined as: pages that track historical price movements, even if not per-trade granularity.

---

## B. Explicit Non-Goals

- No model integration of any new source.
- No source blending.
- No cash parser expansion — unless the cash source reveals a sold/completed/history surface.
- No Discord joining, invite chasing, or server-code hunting.
- No login-gated scraping or credential use.
- No broad crawling, pagination loops, or bulk collection.
- No changing pricing weights or product schema.
- No committing — artifacts saved but not committed during discovery phase.

---

## C. Candidate Classes to Test

### Class 1: Known Player-Market Sources
Sources already in the manifest that may have completed/history surfaces:

1. Traderie — integrated, rolling 50-cap. No additional completed surface needed. Baseline.
2. Diablo2.io — sold-search tested (low volume). Item price-history page not yet probed.
3. d2jsp — gated (Cloudflare + login). Public index/search result pages need testing.
4. Reddit — qualitative only per prior analysis. Subreddit search for sold/completed threads.
5. Discord / Baal's Ledger — gated/manual downstream only. Do not attempt access.

### Class 2: Cash/Marketplace Sources with Possible Sold/History Filters
Cash storefronts that may expose sold/completed filters:

6. eBay — known `LH_Sold=1` filter. Anti-bot blocks automation.
7. PlayerAuctions — active listings only per probe. No sold/completed found.
8. G2G — active listings. Sold/history not yet searched.
9. Eldorado.gg — rendered capture done. Sold/history not yet searched.
10. MMOPixel — rendered capture done. Sold/history not yet searched.
11. MuleFactory — static microdata found. Sold/history not yet searched.
12. RPGStash — captured_static. Sold/history not yet searched.
13. D2Stock — RSS feed, current listings. Sold/history not yet searched.
14. ItemNow — WooCommerce API. Sold/history not yet searched.
15. IGGM — cash parser done. Sold/history not yet searched.
16. AOEAH — captured_static. Sold/history not yet searched.
17. Chicks Gold — captured_static. Sold/history not yet searched.
18. items7 — captured_static, 0 rows. Sold/history not yet searched.
19. Odealo — captured_browser. Sold/history not yet searched.
20. YesGamers — deferred (login wall).

### Class 3: Search-Engine Discovered Sources
Sources not yet in manifest, found via web search:

21. Google/Bing/DuckDuckGo for "D2R completed trades", "D2R trade history", etc.
22. Forum archives beyond d2jsp (e.g., diabloii.net, d2tomb, old phpfbb forums).
23. Public spreadsheets or tools (Google Sheets, price trackers, community projects).
24. GitHub projects (D2R price trackers, market scrapers, trade databases).
25. Community price trackers / Discord-bot-published data.

---

## D. Mandatory Search Terms

Per source/domain, search for completed/history surfaces using these terms:

| Term | Why |
|---|---|
| `sold` | General completed trade filter |
| `completed` | General completed trade filter |
| `recent trades` | Trade history surface |
| `trade history` | Historical price data |
| `price history` | Historical price data |
| `sold for` | Accepted consideration evidence |
| `accepted offer` | Completed trade signal |
| `closed` | Archived/closed listing surface |
| `archived` | Archive of old trades |
| `WTS SOLD` | Player-market sold indicator |
| `WTB SOLD` | Player-market sold indicator |
| `Jah sold` | Item-specific sold search |
| `Ber sold` | Item-specific sold search |
| `Lo sold` | Item-specific sold search |
| `Sur sold` | Item-specific sold search |
| `Diablo 2 Resurrected trade history` | Broad discovery |
| `D2R completed trades` | Broad discovery |
| `D2R sold trades` | Broad discovery |
| `D2R price tracker` | Price history surface |
| `D2R market history` | Market history surface |

---

## E. Mandatory Item Probes

For every candidate source with a search function:

- Jah Rune
- Ber Rune
- Lo Rune
- Sur Rune
- Ohm Rune
- Vex Rune
- Ist Rune
- Stone of Jordan
- Griffon's Eye
- Hellfire Torch
- Annihilus

At minimum, Jah and Ber must be tested. The full set is preferred.

---

## F. Probe Ladder

For each candidate, follow this sequence. Stop when a completed/history surface is found. Record the result at the stopping point.

1. **Normal web/search query** — Google if source has external presence, or site-specific search.
2. **Source internal search** — Use the source's own search box with mandatory terms.
3. **Item page** — Navigate to the item-specific page if one exists.
4. **Search/filter URL params** — Inspect URL for `?sold=`, `?completed=`, `?status=`, `?history=`, etc. Try common params.
5. **Static HTML** — `curl -L` to fetch page HTML. Inspect for embedded data.
6. **Rendered browser capture** — If blocked by JS rendering or anti-bot, use Camoufox or Chromium.
7. **Public API/network inspection** — If DevTools-observable XHR/fetch calls exist.
8. **If still blocked** — Record exact URL for manual capture. Mark as `blocked` or `gated`.

---

## G. Evidence Scoring

For every candidate surface found, score:

| Dimension | Values |
|---|---|
| `completed_surface_found` | `yes` / `no` / `unknown` / `gated` |
| `history_surface_found` | `yes` / `no` / `unknown` / `gated` |
| `active_only` | `yes` / `no` |
| `cash_only` | `yes` / `no` |
| `access` | `static` / `rendered` / `api` / `gated` / `blocked` |
| `volume_evidence` | `none` / `low` / `medium` / `high` |
| `segment_evidence` | `none` / `low` / `medium` / `high` |
| `consideration_evidence` | `none` / `low` / `medium` / `high` |
| `pagination_evidence` | `none` / `low` / `medium` / `high` |
| `parser_feasibility` | `0`-`10` |
| `model_eligibility` | `no` / `research_only` / `diagnostic_candidate` / `model_candidate` |

---

## H. Confidence Gates

Medium-high confidence that all main completed-trade/history sources have been found requires:

| # | Gate | Evidence |
|---|---|---|
| 1 | Top 20 known sources checked with mandatory search probes | 20 entries in scored table |
| 2 | At least 10 broad web queries for unknown sources/tools | Query result summaries |
| 3 | Diablo2.io item price history specifically tested and classified | Score record for `misc/jah-t43.html` |
| 4 | d2jsp classified as gated with proof, or public index/search result proof recorded | Score record or `gated` proof |
| 5 | eBay sold filter classified with proof or manual-capture note | Score record with access finding |
| 6 | Every source with a found history surface has pagination/window inspected | Pagination score per source |
| 7 | All results recorded in source manifest or memo | Scored table complete |
| 8 | No "unknown" remains for completed/history surface on top-tier known sources (except gated/manual) | All Tier 1-2 sources have decision recorded |

If all 8 gates pass, confidence can be raised to **medium-high**.

---

## I. Deliverable Table Schema

| source | candidate_surface | url_or_query | completed_found | history_found | access | volume_evidence | parseability | artifact_path | decision | next_action |
|---|---|---|---|---|---|---|---|---|---|---|

Example row:
```
Diablo2.io | sold_search | search.php?activesold=1&uitemid=43 | yes | no | static | low | 9 | renders/.../rendered.html | research_only | probe item price history
```

---

## J. Recommended Agent Batches

### Batch A — Public Web / Source Discovery

**Mission:** Find completed-trade/history surfaces not yet in the manifest.

- Broad web queries: "D2R completed trades", "D2R trade history", "D2R price tracker", "Diablo 2 Resurrected sold trades", "D2R market history", "D2R spreadsheet prices", "D2R price database", "D2R GitHub prices", "Diablo 2 price history tracker".
- GitHub search: "D2R prices", "diablo 2 resurrected trade", "d2r price tracker", "d2r market".
- Forum archive search: diabloii.net, d2tomb, old phpfbb archives.
- Output: candidate list of new sources/surfaces found.

### Batch B — Deep Known-Source Probes

**Mission:** Score every known source for completed/history surfaces.

- Diablo2.io item price history (`misc/jah-t43.html`).
- eBay sold filter probe (manual capture URL or `LH_Sold=1` classification).
- d2jsp public index/search result pages.
- PlayerAuctions, G2G, Eldorado, MMOPixel, MuleFactory, RPGStash — sold/history filter search on each.
- ItemNow, D2Stock, IGGM — sold/history API params.
- AOEAH, Chicks Gold, Odealo, items7 — sold/history URL params check.
- Output: completed 20+ row scored table.

### Batch C — Artifact / Manifest Update

**Mission:** Save targeted artifacts and update tracking.

- Save only high-value artifacts (rendered HTML of found completed/history surfaces).
- Update `data/source_manifest.json` surfaces_checked and any new surface entries.
- Update or create `research/sources/*.md` source notes for probed sources.
- Record final confidence assessment.
- Output: confidence gate status table. Report whether medium-high was reached.
