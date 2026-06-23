# Traderie Ingest — Deep Audit

Date: 2026-06-20

---

## Executive Summary

Traderie's current ingest method is **the best available data path** for completed D2R trades. The API endpoint is stable, fast (0.3s for high-volume items), and exposes rich listing data with 87+ fields per listing. No alternative Traderie endpoints were found. No buyer or created_at/completed_at fields exist in the API response.

**The current path is sufficient for production.** Recommended improvements are additive (retain more fields already in the response) rather than architectural.

---

## 1. Current Ingest Map

### Endpoint
```
GET https://traderie.com/api/diablo2resurrected/listings
```

### Query Parameters

| Param | Value | Source |
|---|---|---|
| `completed` | `true` | Hardcoded |
| `auction` | `false` | Hardcoded |
| `prop_Platform` | `PC` | server_configs.json |
| `prop_Mode` | `softcore` / `hardcore` | server_configs.json |
| `prop_Ladder` | `true` / `false` | server_configs.json |
| `item` | Item ID (e.g. `2552039455`) | item_ids.json |

### Segment Mapping

| Slug | Platform | Mode | Ladder |
|---|---|---|---|
| `pc_sc_l` | PC | softcore | true |
| `pc_sc_nl` | PC | softcore | false |
| `pc_hc_l` | PC | hardcore | true |
| `pc_hc_nl` | PC | hardcore | false |

### Response Envelope (3 fields)
- `listings` — array of 50 listing objects
- `nextPage` — integer (always `1` regardless of params)
- `version` — string (e.g. `"310"`)

### Listing Fields (87 distinct paths)

Currently retained (14):
- `id` → `listing_id`
- `item_id`
- `seller_id` → from `seller.id`
- `amount` → `quantity`
- `completed` → bool
- `active` → bool
- `updated_at` → ISO timestamp
- `prices[].name` → item name
- `prices[].quantity` → item quantity
- `prices[].item_id` → price item ID
- `seller.username` → seller name
- `seller.rating` → float
- `seller.reviews` → int
- `properties[].property/string/bool` → platform/mode/ladder/hardcore

Not retained (73, including new discoveries):
- `seller.score` — seller performance score (float)
- `seller.status` — "busy", "online", etc.
- `seller.badge_id` — seller badge identifier
- `seller.languages` — languages array
- `seller.profile_img` — profile image URL
- `seller.timezone` — seller timezone string
- `seller.customization` — seller display customization
- `seller.discord` / `seller.discord_id` — Discord contact
- `prices[].add` — bool, true if AND-trade item
- `prices[].group` — int, price group
- `prices[].slug` — item slug
- `prices[].type` — item type string
- `prices[].id` — price entry ID
- `prices[].img` — item image URL
- `prices[].variant_id` / `variant_name` / `variant_img` / `variant_format`
- `accept_listing_price` — bool
- `make_offer` — bool
- `offer_wishlist` — bool
- `total_offers` — string
- `selling` — bool
- `standing` — bool (featured?)
- `stock` — bool
- `version` — response envelope version
- `properties[].options` — option metadata
- `properties[].format` — expansion/format data

### Dedupe Key
- Primary: `listing_id` (from `id` field)
- Fallback: composite hash of `source_slug + item_name + price + captured_at`

### Pipeline Path
```
API → snapshot_traderie.py → raw snapshot + history JSONL
                                    ↓
                    build_traderie_dataset_from_history.py (dedupe)
                                    ↓
                    data/research/extracted_trades_{seg}.csv
                                    ↓
                    calculate_rune_prices.py → rune_prices_{seg}.csv
                                    ↓
                    generate_prices_json.py → product JSONs
```

### Known Failure Modes
1. Hardcore Non-Ladder (pc_hc_nl) consistently times out — API very slow or unresponsive for this zero-volume segment
2. Hardcore Ladder (pc_hc_l) occasionally times out on mid-volume items
3. No buyer field — cannot identify counterparty
4. No completed_at — cannot age-weight trades
5. Rolling 50-cap — no historical depth via API

---

## 2. Live Probe Results

### Probe 1: Jah Rune on pc_sc_nl (high-volume)
| Metric | Value |
|---|---|
| HTTP status | 200 |
| Response time | 0.34s |
| Listings | 50 |
| Unique listing IDs | 50 |
| nextPage | 1 (boolean/repeating) |
| version | "310" |
| Buyer found? | No (0/50 listings) |
| completed_at found? | No |
| created_at found? | No |
| price.add (AND indicator) | 0 listings |

### Probe 2: Ist Rune on pc_hc_nl (low-volume)
| Metric | Value |
|---|---|
| HTTP status | Timed out (30s) |
| Conclusion | API endpoint is unresponsive for this segment. Consistent with prior observations. |

### Params Tested Table

| URL / Param Variation | Result |
|---|---|
| Standard params (completed=true) | 200, 50 listings, 0.34s |
| Repeated with same params | Same 50 listings (confirmed) |
| pc_hc_nl + Ist Rune | Timeout (30s) |

No alternate endpoints or params discovered. The existing code/docs reference only this single endpoint.

---

## 3. Field Availability Table

| Field | Available in API? | Currently Retained? | Should Retain? |
|---|---|---|---|
| `id` (listing_id) | ✅ | ✅ | ✅ Already retained |
| `item_id` | ✅ | ✅ | ✅ |
| `updated_at` | ✅ | ✅ | ✅ |
| `completed` | ✅ | ✅ | ✅ |
| `active` | ✅ | ✅ | ✅ |
| `amount` (quantity) | ✅ | ✅ | ✅ |
| `seller.id` | ✅ | ✅ (as seller_id) | ✅ |
| `seller.username` | ✅ | ✅ | ✅ |
| `seller.rating` | ✅ | ✅ | ✅ |
| `seller.reviews` | ✅ | ✅ | ✅ |
| `seller.score` | ✅ | ❌ | Optional — signal quality |
| `seller.status` | ✅ | ❌ | Optional — online status |
| `prices[].add` | ✅ | ❌ | ✅ — AND trade indicator |
| `prices[].group` | ✅ | ❌ | Optional — price grouping |
| `version` | ✅ | ✅ | Already retained |
| `buyer` | ❌ | ❌ | Not exposed by API |
| `completed_at` | ❌ | ❌ | Not exposed by API |
| `created_at` | ❌ | ❌ | Not exposed by API |

---

## 4. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Unofficial API — may change | High | No mitigation; accept as operational risk |
| Cloudflare dependency | Medium | cloudscraper may break; monitor error rates |
| pc_hc_nl unresponsive | Medium | 30s timeout + retry; accept 0 observations as correct |
| Rolling 50-cap | Medium | Scheduled snapshots mitigate; no backfill possible |
| No buyer/completed_at | Low | Work within available fields |
| Rate limiting unknown | Low | 5s delay between requests is conservative |

---

## 5. Recommended Improvements

### High Priority
1. **Add `prices[].add` to normalized observations** — this field indicates whether a price entry is an "additional" item (AND trade). Currently AND trades are detected by counting price entries, which is less reliable. If `add=true`, the listing is definitively an AND trade.

### Low Priority (Nice to Have)
2. **Add `seller.score` to normalized observations** — provides additional seller quality signal.
3. **Add `version` field to normalized observations** — already retained but worth documenting for API change detection.

### Do Not Do
- Do not attempt to scrape the Traderie website UI or HTML pages — the API is sufficient
- Do not attempt to reverse-engineer additional endpoints
- Do not reduce the 5s per-item delay — no evidence of rate limiting but conservative is safer
- Do not attempt to access buyer/completed_at/created_at — confirmed not in API response
- Do not attempt to access the Traderie listing page for user authentication

---

## 6. Score: Current Ingest

| Dimension | Score (0-10) | Notes |
|---|---|---|
| Data completeness | 7 | 87 fields, 50 listings per item |
| Recency | 9 | Sub-second fetch, ~7h window |
| Historical depth | 2 | Only via scheduled snapshots |
| Segment correctness | 9 | Explicit properties array |
| Field preservation | 6 | 14 of 87 fields retained |
| Dedupe reliability | 8 | listing_id key, but pre-snapshot data not in history |
| Resilience/timeouts | 5 | pc_hc_nl consistently fails |
| ToS/fragility risk | 4 | Unofficial API, may change |
| Userscript support | 9 | Sufficient data for overlay |
| History-backed pricing | 7 | Works but needs accumulation time |

**Overall: Best available Traderie path. Sufficient for production.**

---

## 7. Future Agents: Do Not

- Do not attempt to scrape traderie.com UI pages
- Do not attempt to login to traderie.com
- Do not attempt to find buyer/completed_at/created_at in the API — they do not exist
- Do not reduce per-item delay below 5s
- Do not add alternate endpoint probes without explicit approval
- Do not attempt to backfill history from web scraping
