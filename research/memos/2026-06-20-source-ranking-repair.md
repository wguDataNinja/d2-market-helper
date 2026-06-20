# Source Ranking Repair — 2026-06-20

## Changes Applied to `data/source_manifest.json`

### 1. IGGM: tier_3 → tier_2

**Evidence:** IGGM has a validated offline parser, 30 extracted rune observations with high segment confidence (PC, Non-Ladder, Softcore, ROTW), browser capture confirmed, and a working `iggm_cash_prices.json` output. It is the only cash-market source with a fully validated parser producing structured price data.

**Rationale:** The tier_3 label was misleading — IGGM had better evidence than any other cash source but was ranked below PlayerAuctions (tier_2, no parser), items7 (tier_2, 0 parse rows), and G2G (tier_2, browser-only). Per the general rule: working parsers should not rank below unparsed sources.

**Remaining gaps:**
- Only one segment captured (PC, Non-Ladder, Softcore, ROTW). Ladder and Hardcore variation untested.
- No sold/completed surface searched.
- URL params not inspected — filter selection may use POST/JS.
- Pagination untested.

---

### 2. PlayerAuctions: tier_2 → tier_3

**Evidence:** The probe (2026-06-20) confirmed:
- No sold/completed/history surface exists.
- Cloudflare managed challenge blocks all curl requests (6/6 URLs returned 403).
- No rune-specific filtered URL has been captured.
- Segment filters are embedded in listing `data-bind` paths but not confirmed as working UI filter controls.
- The best existing fixture (`warlock_gear_sets.html`) contains only one seller's listings.

**Rationale:** Despite having structured data-bind attributes with segment encoding, PlayerAuctions has no working parser, no rune-specific capture, and requires browser automation to access. Tier_2 overstated its readiness. Downgraded to tier_3 per audit recommendation.

**Remaining gaps:**
- No browser capture of a rune-specific listing page.
- Multi-seller data not collected.
- Filter UI controls unconfirmed.
- Pagination behaviour unknown.

---

### 3. items7: tier_2 → tier_3

**Evidence:** The static HTML download was parsed and produced 0 rows. Prices are loaded client-side and cannot be extracted without a browser capture. The offline parser `parse_items7_offline.py` returned no results.

**Rationale:** Tier_2 implies higher readiness than tier_3 sources like IGGM (working parser) or ItemNow (clean API), but items7 has no extractable prices and no browser capture. Per audit recommendation.

**Remaining gaps:**
- No browser capture proving per-rune prices are extractable.
- Segment filters (ladder, season) assumed from navigation text, never verified by URL param testing.
- Individual rune product pages never captured.

---

### 4. ItemNow: status captured_static → parser_prototype_ready

**Evidence:** The API probe (2026-06-20) confirmed:
- WooCommerce Store API at `/wp-json/wc/store/v1/products?category=99&per_page=100` is fully public, returns structured JSON with 42 rune products and prices in USD cents.
- No browser or auth required — clean JSON API.
- Segment filter params documented and confirmed: `?server=d2r-ladder`, `?server=d2r-non-ladder`, `?server=d2r-hc-ladder`, `?server=d2r-hc-non-ladder`.
- No sold/completed/history surface.

**Status change:** `captured_static` → `parser_prototype_ready`. Agent M should create a Store API parser matching the existing `cash_market_listings` output schema.

**Segment filter fix:** `platform` changed from `true` to `false`. The audit found no platform-specific URL param — the `?server=` params cover ladder and HC but not platform. Platform is not filterable via URL.

**Static HTML extraction changed:** `extraction.static_html` set to `false` — the Store API is the canonical extraction path, not static HTML.

**Priority:** Kept at tier_3 (cash source, external comparison). This is appropriate — ItemNow is a clean API but still an asking-price cash source, not a completed-trade source.

**Remaining gaps:**
- Per-segment variation prices need individual variation lookups (WC v3 requires auth).
- Base price from Store API is the minimum variation price, not segment-specific.
- Only 30 D2R runes confirmed — bundles also present but not yet categorized.

---

### 5. Diablo2.io: hardcore/softcore segment_filters corrected

**Change:** `hardcore: true` → `hardcore: "unproven"`, `softcore: true` → `softcore: "unproven"`.

**Evidence:** The Jah sold-search fixture contained 7 rows. Every row uses softcore by default (no HC/SC icon class present in HTML). Neither `zi-softcore` nor `zi-hardcore` class was found in the fixture. The `true` values were assumed, not proven.

**What remains:** A fixture with an explicit HC or SC filter URL is needed to confirm the icon classes appear in search results HTML.

---

### 6. IGGM segment_filters consistency

No change made. Audit flagged that `segment_filters` values (all `true`) are based on UI observation without verified URL param testing. However, the parser confirms PC, Non-Ladder, Softcore, ROTW from actual page content — these are verified from extracted data, not just UI observation. Keeping as-is with existing caveat that other filter combinations may yield different prices.

---

## Sources Still Unproven (Zero Artifacts)

These 8 sources have `current_artifacts: []` and remain at status `discovered` with no capture evidence:

| Source | Priority | Category |
|--------|----------|----------|
| ebay | later | cash_market |
| eldorado | later | cash_market |
| mmopixel | later | cash_market |
| mulefactory | later | cash_market |
| rpgstash | later | cash_market |
| d2stock | later | source_directory_only |
| discord_baals_ledger | later | community_discussion |
| d2jsp | tier_3 | forum_reference |

None of these are ranked tier_1 or tier_2, consistent with the general rule. d2jsp at tier_3 has caveats explaining its forum-only FG economy — acceptable.

The only integrated source with empty `current_artifacts` is **traderie** (tier_1). This is acceptable because it is already integrated into the pricing pipeline — its artifacts are the codebase itself, not research captures.

---

## Validated Correct As-Is

- **G2G** — tier_2, captured_browser. Segment filters remain `"partial (embedded in listing titles)"` for ladder/HC/SC, which is honest and accurate per audit.
- **Reddit** — tier_3, deferred. Status correct.
- **yesgamers** — tier_3, deferred. Status correct.
- **odealo** — tier_3, captured_browser. Status correct pending rune-specific URL capture.
- **aoeah** — tier_3, captured_static. Status correct.
- **chicksgold** — later, captured_static. Status correct.
- **traderie** — tier_1, integrated. No changes needed.
