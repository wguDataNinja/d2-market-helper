D2R Market Helper — Repo State + Next Plan

Date: 2026-06-20
Repo: /Users/buddy/projects/traderie
Commit: 013c994
Commit title: init: D2R Market Helper — pricing pipeline, item registry, source discovery, external cash-price prototype

⸻

1. Product Definition

D2R Market Helper is now framed as a multi-source market intelligence hub for Diablo II: Resurrected traders.

It is not just a Traderie userscript, rune calculator, or price list.

Core purpose:

Combine segment-specific in-game rune ratios, external cash-market prices, trade-source links, source caveats, and community signals into one transparent trader dashboard.

Primary surfaces:

* Rune values by economy segment
* External cash/RMT price comparison
* Source directory
* Evidence labels and caveats
* High-value item tracking later
* Companion userscript integration later

Core product rule:

* Traderie completed trades = in-game barter value source
* Cash/RMT sites = external comparison only
* Forums/community/Reddit/Discord = qualitative or reference signals
* Never blend cash-market prices into in-game rune ratios

⸻

2. Economy Segment Model

D2R economies are separate and must not be merged by default.

Minimum PC segments:

Segment Meaning
pc_sc_l PC Softcore Ladder
pc_sc_nl  PC Softcore Non-Ladder
pc_hc_l PC Hardcore Ladder
pc_hc_nl  PC Hardcore Non-Ladder

Future dimensions:

* PlayStation
* Xbox
* Switch
* Region
* Season / ROTW
* Ladder vs Non-Ladder
* Softcore vs Hardcore

Rules:

* Retain segment metadata whenever possible.
* Missing segment metadata lowers confidence.
* Cross-segment aggregation is not MVP behavior.

⸻

3. Current Data Tracks

A. In-game barter pricing

Primary source:

* Traderie completed trades

Current model:

* Rune-for-rune completed trades only
* Ist-normalized VWAP
* Bid/ask side preserved
* Segment-specific outputs

Excluded for now:

* AND trades
* Non-Ist rune-pair modeling beyond current approach
* Active listings
* Cross-segment merged pricing
* Cash prices

B. External cash prices

Current source:

* IGGM prototype

Purpose:

* Cash-market comparison/shopping reference only

Rules:

* Not used in in-game model.
* Must show caveats.
* Must preserve source and segment confidence.

C. Source intelligence

Current source ledger:

* data/source_manifest.json

Tracks:

* source slug/name/url/category
* priority/status
* evidence class
* known URLs
* rune/item support
* segment filters
* extraction method
* artifacts
* caveats
* next action
* last reviewed date

⸻

4. Documentation Created / Updated

File  Purpose
docs/PROJECT_ROADMAP.md Product vision and phased plan
docs/ARCHITECTURE.md  Segment model, evidence classes, data flow, layout
docs/PRICING_MODEL.md Pricing model, VWAP, caveats
docs/DATA_PRODUCTS.md Product JSON schemas/status
docs/CODEX_HANDOFF.md Agent handoff and project invariants
docs/SOURCE_MANIFEST.md Source ledger docs
docs/SOURCE_DISCOVERY.md  Source discovery updates
research/sources/captures/README.md Capture artifact layout

Memos:

* research/memos/codex-source-discovery-review.md
* research/memos/2026-06-20-browser-automation-discovery-plan.md
* research/memos/2026-06-20-g2g-browser-capture-review.md
* research/memos/2026-06-20-source-discovery-workflow.md
* research/memos/2026-06-20-external-cash-prices-prototype.md
* research/memos/2026-06-20-session-closeout.md

⸻

5. Traderie Pipeline State

Traderie endpoint used:

GET https://traderie.com/api/diablo2resurrected/listings
  completed=true
  auction=false
  prop_Platform=PC
  prop_Mode={softcore|hardcore}
  prop_Ladder={true|false}
  item={traderie_item_id}

Fetcher:

* Loads server_configs.json
* Loads data/item_ids.json
* Iterates segment → category → item
* Uses cloudscraper
* Writes sanitized raw records to:
    * data/raw/raw_trades_{segment}.json

Extractor:

* Reads only Runes
* Keeps rune-for-rune completed trades
* Writes:
    * data/extracted/extracted_trades_{segment}.csv

Pricing:

* Uses Ist-normalized bid/ask VWAP
* Uses single-request Ist-pair trades
* Writes:
    * data/prices/rune_prices_{segment}.csv

Known Traderie risks:

* Unofficial API dependency
* Pagination/window behavior unknown
* Dedupe relies too much on updated_at
* Listing IDs and item IDs are dropped
* Segment metadata inferred from filenames instead of persisted
* Seller metadata, price item IDs, listing status, and properties dropped
* AND trades extracted but not modeled
* Need richer timestamp/window metadata for freshness labels

Recommended next Traderie task:

Run one live fetch with full raw response logging for one item/segment and inspect:

* pagination fields: total, page, limit
* listing IDs: listing_id or id
* timestamps: created_at, completed_at, updated_at
* seller fields: seller.rating, seller.total_trades
* buyer fields
* response-envelope metadata

Then update fetch_completed_trades.py to retain richer private normalized fields.

⸻

6. In-game Rune JSON Product

Files created/updated:

File  Purpose
scripts/generate_prices_json.py Reads 4 CSVs, outputs both JSON products
scripts/validate_in_game_rune_values.py Validates schema, segments, confidence, compat format
data/products/in_game_rune_values.json  Main product: 4 segments, 92 rune observations, 2,570 trades
data/products/traderie_tools_prices.json  Userscript-compatible feed
docs/DATA_PRODUCTS.md Marked in-game product active

Validation:

Validator Result
validate_in_game_rune_values.py Passed
validate_source_manifest.py Passed: 20 sources valid
validate_external_cash_prices.py  Passed: 30 observations

Segment summary:

segment       runes   trades   high   med   low   unav
pc_sc_l          23     1344      6     2     8      7
pc_sc_nl         23     1095      5     4     8      6
pc_hc_l          23      126      1     1    10     11
pc_hc_nl         23        5      0     0     4     19

Totals:

* 92 rune observations
* 2,570 modeled trades
* Softcore = 2,439 trades, 95% of volume
* Hardcore ladder = thin, 126 trades
* Hardcore non-ladder = unusable, 5 trades
* Confidence counts:
    * 12 high
    * 7 medium
    * 30 low
    * 43 unavailable

Confidence rules:

* High: >= 50 trades
* Medium: >= 15
* Low: < 15
* Unavailable: 0

Sample pc_sc_l values:

rune      value_ist  bid_price  ask_price  bid_ct  ask_ct  confidence
Lo           6.2445     5.9783     6.5107      45     249  high
Ohm          4.3154     4.0741     4.5568      27     227  high
Jah         17.2533    16.3884    18.1181     102     118  high
Mal          0.7458     0.6356     0.8560      47     154  high
Gul          1.5499     1.3889     1.7110      33     114  high

Userscript compatibility:

* Segment keys match getServerSlug():
    * pc_sc_l
    * pc_sc_nl
    * pc_hc_l
    * pc_hc_nl
* Rune names use "Jah Rune" format.
* Matches userscript parseRune() extraction.
* Compat entry shape:

{
  "ist_value": 17.2533,
  "low_confidence": false
}

Status:

* No compatibility mismatches.
* Feed ready for Tampermonkey/userscript consumption.

⸻

7. Source Discovery State

Sources discussed or inspected:

* Traderie
* G2G
* PlayerAuctions
* items7
* IGGM
* Odealo
* YesGamers
* AOEAH
* Chicks Gold
* ItemNow
* eBay
* Eldorado
* MMOPixel
* MuleFactory
* RPGStash
* D2Stock
* Diablo2.io
* d2jsp
* Reddit
* Discord / Baal’s Ledger

Key correction:

* Static downloaded HTML is insufficient for many sources.
* JS-rendered marketplaces require controlled browser capture.

Browser discovery rules:

* Use Camoufox for discovery only, not production scraping.
* One page at a time.
* No login.
* No checkout/cart.
* No aggressive crawling.
* Save rendered HTML, screenshot, metadata, listing samples, and network summaries.
* Analyze offline.

Relevant prior Camoufox references:

* browser_llm/docs/research/camoufox_study.md
* playwright_workbench/
* playwright_workbench/docs/research/camoufox.md
* ih_market_companion/_internal/vps_helper/docs/camoufox_vps_guide.md
* ih_market_companion/_internal/vps_helper/docs/hackbot_stabs_buy.md

Use existing env:

* /Users/buddy/projects/playwright_workbench/.venv

⸻

8. Source Manifest

Files:

File  Purpose
data/source_manifest.json Canonical source ledger
docs/SOURCE_MANIFEST.md Manifest docs
research/memos/2026-06-20-source-discovery-workflow.md  Workflow memo
scripts/validate_source_manifest.py Validator
research/sources/captures/README.md Capture layout docs

Status lifecycle:

discovered
→ captured_static
→ captured_browser
→ offline_parse_candidate
→ parser_prototype_ready
→ integrated

Also supports deferred/rejected states.

Seeded sources:

* 20

Validation:

20 sources valid
0 errors
0 warnings

⸻

9. Browser Capture Results

G2G

User URL:

https://www.g2g.com/categories/diablo-2-resurrected-item-for-sale?fa=7075ff24%3A2c21e727%7C7071deb3%3A4d2c8b55&sort=lowest_price

Result:

* Capture PASS
* Camoufox rendered without challenge
* 20 listing samples extracted in ~13s
* No login required
* Rune prices visible
* Lowest visible examples around $0.029 to $0.049

Issue:

Listing titles included text like:

PC - LoD - NonLadder - SC > Runes > Runes:6# Ith

Ambiguity:

* URL is D2R category
* Listing text says LoD
* Search also showed ROTW examples
* Need taxonomy validation

Interpretation candidates:

* LoD may be G2G taxonomy within D2R
* Classic D2 spillover
* Base-game item-system classification separate from ROTW

Offer-detail captures:

* Caused browser/tool errors and timeouts
* Deferred

Final G2G status:

* captured_browser
* Promising
* Category pages render
* Offer details deferred
* LoD/ROTW unresolved
* Not trusted for external cash product v0

⸻

IGGM

URL:

https://www.iggm.com/d2-resurrected-items

Result:

* Best external cash candidate
* Runes visible
* Prices visible
* Segment filters visible
* No login required
* 30 rune prices parsed

Confirmed segment:

Dimension Value
Platform  PC
Ladder  Non-Ladder
Hardcore  No
Softcore  Yes
Season/ruleset  ROTW

Segment confidence:

* Upgraded low → high

Sample cash observations:

Zod   $8.99
Cham  $4.99
Jah   $7.90
Ber   $7.29
Sur   $4.29

Final IGGM status:

* parser_prototype_ready
* Tier 2
* High-confidence external cash source
* Segment: PC / Non-Ladder / Softcore / ROTW
* 30 rune observations

⸻

items7

Initial belief:

* Static artifact might contain per-rune prices

Actual parser result:

* 0 rows

Status:

* captured_static
* Static artifact lacks extractable per-rune prices
* Needs browser-rendered capture

⸻

YesGamers

Result:

* Rendered
* Segment UI visible
* Prices behind login

Status:

* deferred

⸻

Odealo

Result:

* Rendered
* Some useful structured/listing info visible
* Needs rune-specific URL

Status:

* captured_browser
* Tier 3

⸻

PlayerAuctions

Result:

* Homepage rendered
* No useful rune listing prices on captured page
* Needs rune-specific URL/search result capture

Status:

* captured_browser
* Tier 2

⸻

10. External Cash Price Prototype

Files:

File  Purpose
scripts/parse_iggm_offline.py Offline IGGM parser
scripts/parse_items7_offline.py Offline items7 parser; documents limitation
scripts/generate_external_cash_prices.py  Merges parser outputs
scripts/validate_external_cash_prices.py  Product validator
data/external/iggm_cash_prices.json 30 IGGM observations
data/external/items7_cash_prices.json 0 observations, documented
data/products/external_cash_prices.sample.json  Schema-versioned product
research/memos/2026-06-20-external-cash-prices-prototype.md Prototype memo

Initial output:

* IGGM: 30 observations
* items7: 0 observations
* Total product: 30 observations

Validation:

* Passed

Caveats included:

* External comparison only
* Not live feed
* Prices may include seller margin, delivery risk, site fees, minimum floors, and stock constraints
* Source segments may differ
* Must not feed in-game pricing model

⸻

11. Final Source Status

Source  Status  Priority  Notes
Traderie  integrated  tier 1  Primary completed-trade source
IGGM  parser_prototype_ready  tier 2  30 cash rune prices, high segment confidence
items7  captured_static tier 2  Static artifact lacks usable prices
G2G captured_browser  tier 2  Category renders; offer pages crash; LoD/ROTW deferred
PlayerAuctions  captured_browser  tier 2  Needs rune-specific URL
Odealo  captured_browser  tier 3  Needs rune page
YesGamers deferred  tier 3  Login wall

Manifest validation:

20 sources valid
0 errors
0 warnings

⸻

12. Validators at Closeout

Validator Result
scripts/validate_source_manifest.py 20 sources valid
scripts/validate_external_cash_prices.py  30 observations, all checks passed
scripts/validate_item_profiles.py 12 profiles valid
scripts/validate_in_game_rune_values.py Both in-game files passed

Confirmed product files:

File  Status
data/source_manifest.json Present
data/products/external_cash_prices.sample.json  Present
data/external/iggm_cash_prices.json Present, 30 observations
data/external/items7_cash_prices.json Present, 0 observations
data/products/in_game_rune_values.json  Present, active
data/products/traderie_tools_prices.json  Present, userscript-ready

⸻

13. Git / Repo State

Repo moved to:

/Users/buddy/projects/traderie

Git initialized.

First commit:

013c994

Commit title:

init: D2R Market Helper — pricing pipeline, item registry, source discovery, external cash-price prototype

Commit size:

434 files
113,929 insertions

.gitignore additions:

.ipynb_checkpoints/
.old/
data/.old/
*.har

Sensitive/private paths excluded:

.venv/
data/raw/
data/extracted/
.env

Explicitly unstaged:

dev/traderie.com_Archive [25-05-22 12-18-02].har

Final state:

* Repo clean
* Initial project history established
* Large/private/sensitive paths excluded
* Validators passing

⸻

14. Product Surface Plan

Homepage should feel like a market front page, not a calculator.

Homepage sections

1. Segment selector
2. Market snapshot cards
3. Cheapest real-money rune sites
4. Rune market table
5. Where-to-trade directory
6. Community pulse
7. Watchlist / trend movers later

Default MVP segment:

PC / Softcore / Non-Ladder

Visible product rules:

1. In-game values and cash prices are separate.
2. Economy segments are not merged.
3. Completed trades are stronger than active listings.
4. Cash prices include site/seller friction and are not fair-market in-game value.
5. Reddit/forums are qualitative unless separately modeled.
6. Thin-volume items get low confidence.
7. Every number must show source and confidence.

⸻

15. Planned Pages

Page  Purpose
/ Market overview
/runes  Full rune dashboard
/items  Major item dashboard
/item/:slug Single item page
/sources  Source directory and trust labels
/trends Market movement
/about-methodology  Required trust/methodology page

Initial tracked items for /items:

* Annihilus
* Hellfire Torch
* Griffon’s Eye
* Shako / Harlequin Crest
* Stone of Jordan
* Arachnid Mesh
* Mara’s Kaleidoscope
* Death’s Web
* Death’s Fathom
* Nightwing’s Veil
* War Traveler
* Monarch 4os
* Tokens
* Keys
* Essences

⸻

16. Needed / Future Data Products

Product Status  Purpose
source_manifest.json  Active  Source ledger
in_game_rune_values.json  Active  Segment-specific Traderie rune values
traderie_tools_prices.json  Active  Userscript-compatible feed
external_cash_prices.json / sample  Prototype Cash listing observations
rune_price_history.json Future  Sparklines/trends
market_posts.json Future  Qualitative community signals
source_directory.json Future/generated  Website source cards
item_values.json  Future  Major item pricing

⸻

17. Known Caveats

Traderie

* Unofficial API
* Needs richer private normalized records
* Current sanitizer drops audit fields
* Pagination/window behavior unknown
* AND trades not modeled
* Public outputs lack time-window/freshness clarity

In-game JSON

Does not include:

* Cash/RMT prices
* Reddit/community data
* Active listings
* AND trades
* Cross-segment merged prices
* Confidence intervals/spread stats
* Time weighting
* Season metadata beyond current segment fields

Unknowns:

* Whether /listings?completed=true returns all completed trades or recent window
* Whether unique listing IDs are available
* Whether created_at, completed_at, seller.rating, seller.total_trades, buyer exist
* Effective rate limit
* cloudscraper reliability
* Traderie ToS constraints
* Historical accumulation limits

IGGM

* Cash-market source only
* Confirmed segment: PC / Non-Ladder / Softcore / ROTW
* Need other segment captures
* Needs strong UI caveats before public display

items7

* Static artifact unusable for per-rune prices
* Needs browser capture

G2G

* Category page works
* Offer pages crash/timeout
* LoD/ROTW taxonomy unresolved
* Not product-ready

PlayerAuctions

* Needs rune-specific URL

Odealo

* Needs rune-specific page

YesGamers

* Login wall
* Deferred

⸻

18. Next Session Checklist

Recommended order:

1. Run one live Traderie fetch with full raw response logging.
2. Inspect pagination, IDs, timestamps, seller/buyer fields, envelope metadata.
3. Update fetch_completed_trades.py to retain dropped audit fields.
4. Browser-capture items7 rendered rune page.
5. Update parse_items7_offline.py if rendered prices appear.
6. Add items7 observations to external cash product.
7. Capture IGGM segment variation:
    * PC Ladder Softcore
    * Hardcore
8. Find/capture Odealo rune-specific URL.
9. Find/capture PlayerAuctions rune-specific URL.
10. Revisit G2G category parsing only, not offer-detail pages.
11. Investigate Diablo2.io price-history/completed-trade surface.
12. Evaluate d2jsp / FG economy without converting FG to Ist.
13. Build first static website prototype from:
    * data/source_manifest.json
    * data/products/in_game_rune_values.json
    * data/products/external_cash_prices.sample.json

⸻

19. Suggested Next Commit

Likely next commit:

Add Traderie raw audit capture, items7 rendered parser, and website-ready rune products

Expected scope:

* One-item Traderie raw audit capture
* Richer normalized Traderie fields
* items7 browser artifact
* updated items7 parser
* more external cash observations
* product JSON validator improvements
* first website-ready data contract updates

Alternative narrower commit:

Add Traderie response audit and normalized listing metadata

⸻

20. Final State

Current state:

* Repo initialized
* Commit 013c994 complete
* Repo clean
* Validators passing
* Source manifest established
* Browser discovery workflow established
* IGGM external cash prototype working
* In-game rune values JSON active
* Userscript compatibility feed ready
* Traderie remains primary in-game source
* Next work is clear and bounded

Product one-liner:

D2R Market Helper is a multi-source market dashboard for Diablo II: Resurrected traders, combining segment-specific in-game rune ratios, cash-market prices, trade-source links, and community signals into one transparent trader hub.