# Market Source Discovery Protocol

**Created:** 2026-06-20
**Status:** Active
**Replaces:** research/memos/2026-06-20-source-discovery-workflow.md (informal workflow)

## Purpose

Define the mandatory 7-stage process every agent MUST follow when evaluating a new market source for D2R pricing data. This protocol replaces the informal workflow with explicit stages, mandatory probes, standardized scoring, and pass/fail gates.

---

## Stage 1: Broad Candidate Discovery

### Method

Search for D2R trade/pricing sources using ALL of the following:

| Channel | Method |
|---|---|
| Google | `d2r "rune prices" site`, `"diablo 2 resurrected" trade`, `d2r market site:*` variations |
| Forum mentions | d2jsp, pureDiablo, diabloii.net — scan market/selling subforums for linked marketplaces |
| Reddit | r/Diablo_2_Resurrected, r/d2r, r/Diablo — search "price check", "trading site", "where to trade" |
| Existing directories | d2stock.net, D2R market lists, GitHub repo READMEs |
| Cross-references | Existing sources that link to or mention other marketplaces (footer links, blogroll, "trusted stores") |
| Discord | Server join requests are **out of scope** (per no-login principle) unless public web-accessible |

### Documentation Requirements

Each candidate MUST be documented in two places:

1. **`data/source_manifest.json`** — add entry with:
   - `slug`, `name`, `url`, `type` (one of: marketplace, forum, directory, cash_rmt, api, community)
   - `status`: `discovered`
   - `discovery_channel`: which search method found it
   - `initial_notes`: any immediate observations (login wall, bot detection, empty results)

2. **`research/sources/{source_slug}.md`** — with sections:
   - **URL** — canonical URL
   - **Discovery context** — how found, what search terms hit it
   - **Known segments** — any visible ladder/HC/platform/season filters
   - **Initial surface assessment** — what evidence types might exist (completed trades, listings, price guides, API, forum chatter)
   - **Barriers** — login required, captcha, anti-bot, paywall, requires JS
   - **Competing sources** — does this duplicate an existing known source?

### Gate

A source with any documented barrier blocking all surfaces (login, paywall, unreachable) may be set to `status: deferred` immediately, but only after the barrier is **proven** by attempting access.

---

## Stage 2: Source Surface Inventory

For every candidate, classify EVERY possible evidence type the source offers, using the standard inventory format.

### Evidence Type Classification

| Evidence Type | Code | Example |
|---|---|---|
| Completed player trades | `completed_trade` | Traderie API completed trades |
| Active player listings | `active_listing` | Traderie active trade offers |
| Price history / trade history | `price_history` | Diablo2.io sold search results |
| Cash/RMT listings | `cash_listing` | G2G, PlayerAuctions, IGGM rune pages |
| Forum market chatter | `forum_text` | d2jsp price-check threads, Reddit |
| Static price guide | `reference` | Fixed-price tables, wikis, spreadsheets |
| API / network data | `api` | Structured JSON endpoints, GraphQL, XHR responses |
| Item detail pages | `item_page` | Individual item view with pricing info |
| Search result pages | `search_page` | Site-internal search for items with results |

### Surface Inventory Format

Each source MUST have a standardized surface inventory block in `research/sources/{slug}.md`:

```markdown
## Surface Inventory

| Surface | Status | Evidence Strength | Notes |
|---|---|---|---|
| completed_trade | found / absent / unchecked | completed_trade / active_listing / cash_listing / forum_text / reference | URL or path |
| active_listing | found / absent / unchecked | — | URL or path |
| price_history | found / absent / unchecked | — | URL or path |
| cash_listing | found / absent / unchecked | — | URL or path |
| forum_text | found / absent / unchecked | — | URL or path |
| reference | found / absent / unchecked | — | URL or path |
| api | found / absent / unchecked | — | Endpoint |
| item_page | found / absent / unchecked | — | URL or path |
| search_page | found / absent / unchecked | — | URL or path |
```

### Gate (G2 — Surface Exhaustiveness)

A source's surface list MUST be **exhaustive** — all known surfaces documented — before priority is assigned. "Unchecked" is explicitly allowed but must be recorded. A source with unchecked surfaces cannot receive a final tier ranking.

---

## Stage 3: Deep Market-Surface Search

### Mandatory Search Probes

For EVERY source, regardless of apparent type, the agent MUST perform ALL of the following probes. Each probe result must be recorded in the source notes.

#### 3.1 Site Search (Internal Search Box)
- Search for: `Jah`, `Ber`, `Lo`, `Sur`, `Ohm`, `Vex`, `Ist`
- Search for: `Annihilus`, `Hellfire Torch`, `Griffon's Eye`, `Stone of Jordan`
- Record: does search return results? Are results priced? Are results segmented?

#### 3.2 Item Page Probes
- Navigate to item pages for: `Jah`, `Ber`, `Lo`, `Sur`, `Ohm`, `Vex`, `Ist`
- Navigate to item pages for: `Annihilus`, `Hellfire Torch`, `Griffon's Eye`, `Stone of Jordan`
- Record: what pricing info is on the page? Is there a completed/sold tab? A history view?

#### 3.3 Category / Forum Page
- Navigate to the main marketplace/trade category
- Record: what is the default view? Are there subcategories?

#### 3.4 Filter Controls
- Enumerate ALL visible toggles, dropdowns, checkboxes, radio buttons
- Record: ladder/non-ladder, hardcore/softcore, platform, season, item type, price range, sort order

#### 3.5 URL Parameters
- Record ALL query parameters from page URLs
- Test modifying key parameters: `?page=2`, `?sort=price`, `?ladder=1`, `?search=jah`
- Record: do URL parameters change the response? Which ones affect segment/pagination/filtering?

#### 3.6 Network Requests
- Open browser DevTools Network tab (or equivalent)
- Filter XHR/Fetch requests
- Record: API endpoints, GraphQL queries, embedded JSON blobs, data URIs with base64 payloads

#### 3.7 Static HTML
- `curl` the page or view page source (`curl -sL <url> | python -c "import sys; html=sys.stdin.read(); print(len(html)); print(html[:2000])"`)
- Record: are prices visible in raw HTML? Is there embedded JSON (`<script>window.__INITIAL_STATE__`)? Server-rendered tables?

#### 3.8 Rendered HTML
- For JS-heavy sites: browser-capture the page
- Record: does the rendered HTML differ from static? Are prices injected client-side?

#### 3.9 Pagination Behavior
- Click "Next page" or load more
- Record: cursor-based, page-number-based, infinite scroll, or no pagination
- Record: does each page have a unique URL? Is pagination API-driven?

### Mandatory Search Terms

For every search/pagination probe, use ALL of these D2R-specific terms:

| Term | Purpose |
|---|---|
| sold | Completed transactions |
| completed | Completed transactions |
| recent trades | Time-ordered trade history |
| price check | Community price estimation |
| historical prices | Price history view |
| WTS SOLD | For-sale listings that have closed |
| WTB SOLD | Want-to-buy listings that have closed |
| sold for | Completed transaction price |
| offer accepted | Completed negotiation |
| closed | Closed/completed listings |
| archive | Archived listings |
| history | Trade history view |
| ladder | Ladder-specific filter |
| non-ladder | Non-ladder filter |
| hardcore | HC filter |
| softcore | SC filter |
| PC | Price check abbreviation |
| ROTW | Rest of the world (non-ladder) |

### Mandatory Item Probes

For every site search and item page probe:

| Item | Why |
|---|---|
| Jah | High-value rune, strong price signal |
| Ber | High-value rune, strong price signal |
| Lo | Mid-high rune |
| Sur | Mid rune |
| Ohm | Mid rune, rune-word staple |
| Vex | Mid rune |
| Ist | Base reference rune |
| Annihilus | Unique charm, high-value |
| Hellfire Torch | Unique charm, high-value |
| Griffon's Eye | High-value unique |
| Stone of Jordan | Classic high-value unique |

### Gate (G1 — Tier 1 Surface Proof)

A source cannot be ranked `tier_1` unless at least one high-value surface (`completed_trade` or `api`) is captured or proven to exist with accessible data. Evidence of existence from Stage 3 probes suffices; a full capture is not required for tier ranking.

---

## Stage 4: Capture Fixture Requirements

### When to Capture Static HTML

Capture static HTML via `curl` when:
- Prices are visible in the raw HTML source
- Embedded JSON structures contain pricing data
- The page does **not** require JavaScript to render trade/listing data
- The page is accessible without session/auth

### When to Capture Browser Render

Capture browser-rendered HTML via Camoufox when:
- Prices are injected client-side via JavaScript
- The site uses React/Vue/Angular with client-side rendering
- The site returns a shell with data loaded via XHR/Fetch
- Anti-bot challenge verification is needed
- The static HTML contains no useful trade/pricing information

### Fixture Directory Structure

```
research/sources/
├── {source_slug}.md                         # Source notes (always committed)
├── downloads/                               # Static HTML captures
│   └── {batch_date}/
│       └── {source_slug}.html
└── captures/                                # Browser captures
    └── {source_slug}_{YYYYMMDD_HHMM}/
        ├── page.html                        # Rendered page HTML
        ├── screenshot.png                   # Visual evidence
        ├── metadata.json                    # Capture metadata (URL, user agent, timestamp, viewport)
        ├── listing_samples.json             # Sample structured listings if observable
        └── network_summary.json             # Captured XHR/API endpoints and responses
```

### Required Artifacts Per Capture

| Capture Type | Required | Optional |
|---|---|---|
| Static HTML | `.html` | — |
| Browser capture | `page.html`, `screenshot.png`, `metadata.json`, `listing_samples.json` | `network_summary.json` |

### Gate: Fixture Existence for Parser

A parser MUST NOT be written for a surface unless a fixture exists. No exceptions. The fixture must be committed or linked to the source notes.

---

## Stage 5: Scrape Feasibility Scoring

For EACH surface found (not per source), score the following dimensions. Every dimension must be scored. Default value is `unknown` — no field may be left blank.

### Scoring Dimensions

| Field | Values | Meaning |
|---|---|---|
| `evidence_strength` | `completed_trade` > `active_listing` > `cash_listing` > `forum_text` > `reference` | Best evidence type available on this surface |
| `segment_clarity` | `explicit` / `partial` / `none` | Are segment filters (ladder, HC, platform) visible and functional? |
| `consideration_clarity` | `explicit` / `partial` / `none` | Is what was given in exchange clearly stated? (e.g., "Jah for 8 Ist" vs "Selling Jah") |
| `time_clarity` | `exact` / `relative` / `none` | Is the trade timestamp exact, relative ("2 hours ago"), or absent? |
| `counterparty_clarity` | `seller+buyer` / `seller_only` / `none` | Are both parties identified? |
| `pagination_clarity` | `cursor` / `page` / `none` / `unknown` | How does the surface paginate? |
| `parseability` | `static_html` / `rendered_html` / `api` / `hostile` | Ease of extracting structured data. `hostile` = anti-bot, captcha, rate-limited, requires session |
| `legal_risk` | `acceptable` / `unclear` / `avoid` | Risk of scraping this surface. `avoid` = ToS explicitly prohibits, paywalled, or illegal activity |
| `volume_potential` | `high` / `medium` / `low` / `unknown` | Estimated number of extractable observations per batch |
| `normalization_fit` | `rune_for_rune` / `multi_rune` / `item_only` / `none` | How well the surface's trade format maps to the rune-value model. `rune_for_rune` = direct swap with rune on both sides |

### Standard Scoring Table Format

```markdown
## Feasibility Scores

### Surface: {surface_name} ({URL})

| Dimension | Score | Evidence |
|---|---|---|
| evidence_strength | completed_trade | Page shows "Jah rune sold for 8 Ist" with timestamps |
| segment_clarity | explicit | Dropdown for ladder/non-ladder + HC/SC |
| consideration_clarity | explicit | "Sold for" field always populated |
| time_clarity | exact | ISO 8601 timestamps on every trade |
| counterparty_clarity | seller_only | Only seller name shown |
| pagination_clarity | page | `?page=N` parameter, 50 items per page |
| parseability | API | XHR endpoint returns JSON at `/api/trades/sold` |
| legal_risk | acceptable | Public marketplace, no anti-scrape ToS found |
| volume_potential | high | 5,000+ trades visible |
| normalization_fit | rune_for_rune | Direct rune-for-rune swaps |
```

### Gate: Feasibility Threshold

A surface with feasibility score below the following thresholds should be flagged as `low_priority` or `deferred`:

- `parseability` = `hostile`: defer unless all other scores are high
- `legal_risk` = `avoid`: do not proceed
- `evidence_strength` = `reference`: low priority (no actual trade data)
- `legal_risk` = `unclear`: must be resolved before parser work

Any surface with `evidence_strength` = `completed_trade` + `parseability` != `hostile` = **high priority**, proceed immediately.

---

## Stage 6: Parser Prototype Gate

### Requirements Before Writing a Parser

ALL of the following MUST be true:

1. **Fixture exists**: A captured HTML or rendered artifact for the target surface is present in `research/sources/downloads/` or `research/sources/captures/`.
2. **Feasibility score >= threshold**: The surface scores pass the Stage 5 gate.
3. **Validation plan written**: A parser validation plan exists in `research/memos/` that describes:
   - What the parser extracts (fields, format)
   - How to verify correctness (manual count, cross-reference, known values)
   - Minimum sample size for validation (N >= 20 trades or listings)
   - How to handle edge cases (duplicate entries, missing fields, malformed data)

### Parser Requirements

- Parser script lives at `scripts/parse_{source_slug}.py`
- Parser MUST work from saved artifacts only — no live network fetches
- Output format: structured JSON matching the `external_cash_prices.json` schema (for cash sources) or a comparable schema for trade data
- Parser MUST handle its fixture being absent or malformed gracefully
- Parser MUST log warnings for unexpected data shapes

### Validation Plan Template

```markdown
# Parser Validation Plan: {source_slug}

## Surface
{surface_name} at {URL}

## Parser Location
`scripts/parse_{source_slug}.py`

## Extraction Targets
- Field 1: {description, format, example}
- Field 2: {description, format, example}
- Field 3: {description, format, example}

## Validation Method
- [ ] Manual count matches parser output (N >= 20)
- [ ] Cross-reference with {other_source} for {item} price
- [ ] Known values: {item} should be ~{expected_price}
- [ ] Edge cases tested: missing price, multiple offers, no results

## Success Criteria
Parser output is validated when:
1. All fields match manual inspection for >= 20 samples
2. No false positives (garbage data parsed as valid trades)
3. Segment metadata (where present) is correctly extracted
```

---

## Stage 7: Integration Gate

### Requirements Before a Source Enters the Pricing Model

ALL of the following MUST be true:

1. **Parser validated**: The parser has been validated against N >= 20 samples (or the entire fixture if smaller) per the validation plan.
2. **Segment metadata verified**: Every segment filter documented in Stage 2 is verified to produce correctly segmented data. Segment extraction logic is tested.
3. **Crosswalk documented**: A cross-reference between this source's item names and the canonical item registry (`data/item_registry/items.json`) is documented in the source notes. No unmapped items are silently dropped.
4. **`use_in_model` flag**: The manifest field `use_in_model` MUST default to `false` for all new sources. It is lifted to `true` only after all the above checks pass AND a human or automated review confirms:
   - The source data format is compatible with the pricing model
   - The source's segment model matches the project's segment model (or a documented mapping exists)
   - No cash/RMT data is blended into the in-game rune value model (for cash sources, `use_in_model` MUST remain `false`)
   - The source classification (`completed_player_trades`, `cash_market_listings`, etc.) is correct

### Status Lifecycle When Integrated

```
discovered → captured_static → offline_parse_candidate → parser_prototype_ready → integrated
          ↘ captured_browser ↗                                     ↘ rejected
          ↘ deferred (blocked or deferred)
          ↘ rejected (not usable)
```

`integrated` means: source data flows into a production data product. Cash sources at `integrated` status feed the website comparison display only, not the pricing model.

---

## Pass/Fail Gates (Summary)

### Gate 1 — Tier 1 Surface Proof (Stage 3)
A source cannot be ranked `tier_1` unless at least one high-value surface (`completed_trade` or `api`) is captured or proven to exist.

### Gate 2 — Non-Useful Classification (Stage 2/3)
A source cannot be called "non-useful" until all sold/completed/history surfaces are explicitly checked AND found absent. Assumption of absence is not permitted.

### Gate 3 — Surface Exhaustiveness (Stage 2)
A source's surface list must be exhaustive — all known surfaces documented — before priority is assigned. Unchecked surfaces prevent ranking.

### Gate 4 — Pricing Model Entry (Stage 7)
A source cannot enter the pricing model until parser validation AND segment validation AND crosswalk documentation are all complete. `use_in_model` defaults to `false` and must be explicitly lifted.

### Gate 5 — Parser Prerequisite (Stage 6)
A parser MUST NOT be written without an existing fixture AND a feasibility score >= threshold AND a written validation plan. All three conditions must be met.

### Gate 6 — Fixture Prerequisite (Stage 4)
A parser MUST NOT be written for a surface unless a fixture (static HTML or browser capture) exists. No exceptions.

---

## Deviations and Amendments

This protocol is the canonical process for source discovery. Any deviation must be documented in a memo referencing this document and explaining the rationale. Amendments to this protocol itself must be reviewed against all existing active source work to ensure backward compatibility.

## Related Documents

- `docs/SOURCE_MANIFEST.md` — Source manifest schema and lifecycle
- `docs/SOURCE_DISCOVERY.md` — Source ratings and priority
- `docs/ARCHITECTURE.md` — Data architecture and evidence classes
- `research/memos/2026-06-20-source-discovery-workflow.md` — Superseded informal workflow
