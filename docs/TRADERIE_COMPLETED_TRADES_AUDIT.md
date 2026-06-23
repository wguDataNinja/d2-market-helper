# Traderie Completed Trades Pipeline — Audit

## Data Flow

```
server_configs.json ──→ fetch_completed_trades.py ──→ data/raw/raw_trades_{slug}.json
item_ids.json ────────→                                  │
                                                         ▼
                                                  extract_rune_trades.py ──→ data/extracted/extracted_trades_{segment}.csv
                                                                             │
                                                                             ▼
                                                                      calculate_rune_prices.py ──→ data/prices/rune_prices_{segment}.csv
```

## Endpoint

```
GET https://traderie.com/api/diablo2resurrected/listings
```

### Query Parameters

| Param | Source | Example | Notes |
|---|---|---|---|
| `completed` | hardcoded | `true` | Always true — fetches completed trades |
| `auction` | hardcoded | `false` | Always false — skips auctions |
| `prop_Platform` | server_configs | `PC` | Hardcoded to PC for MVP |
| `prop_Mode` | server_configs | `softcore` / `hardcore` | From config `mode` field |
| `prop_Ladder` | server_configs | `true` / `false` | From config `ladder` field — stringified |
| `item` | item_ids.json | `2290642411` | Traderie numeric item ID |

### Segment → Query Mapping

| Slug | prop_Mode | prop_Ladder |
|---|---|---|
| `pc_sc_nl` | softcore | false |
| `pc_sc_l` | softcore | true |
| `pc_hc_nl` | hardcore | false |
| `pc_hc_l` | hardcore | true |

### Item ID Loading

Items are loaded from `data/item_ids.json`. Three categories: `Runes` (24), `Gems` (6), `Misc` (2). Only `Runes` entries are used for rune extraction — gems and misc are fetched but discarded by the extraction step.

Each item is fetched individually with a 5-second delay (`PER_ITEM_DELAY`) between items.

## Raw Fields Retained

The `sanitize_trade_entry` function retains:

| Field | Source | Type | Notes |
|---|---|---|---|
| `seller` | `entry.seller.username` | string | Mapped from nested object |
| `quantity` | `entry.amount` | int | Defaults to 1 |
| `updated_at` | `entry.updated_at` | ISO8601 string | Used for deduplication |
| `price` | `entry.prices[]` | array | Array of `{name, quantity}` objects |

## Fields Dropped

The following fields from the Traderie API response are **dropped**:

- `entry.id` — listing ID (if available)
- `entry.seller.id` — seller internal ID
- `entry.seller.avatar` — avatar URL
- `entry.seller.rating` — seller rating/stats
- `entry.prices[].id` — individual price item ID
- `entry.created_at` — listing creation time
- `entry.expires_at` — listing expiration
- `entry.status` — listing status
- `entry.buyer` — buyer info (if completed trade)
- `entry.completed_at` — when the trade was completed
- `entry.platform` — platform if included in response
- Raw response envelope fields (pagination, totals, etc.)

## Deduplication

Deduplication is based **solely on `updated_at` timestamps** within each item category. The dedupe set is per-item-per-category-per-segment. Two trades with the same `updated_at` for the same item in the same segment are considered duplicates.

**Limitation**: If the API returns the same trade with a different timestamp on a subsequent fetch, it will be stored as a duplicate entry. Conversely, if the API returns two genuinely different trades with identical timestamps (unlikely but possible), the second will be incorrectly skipped.

## Rune Trade Extraction

Filtering in `extract_rune_trades.py`:

1. Only entries under `Runes` category (from `item_ids.json`) are processed
2. Only trades where **both** offered and requested items are in the `valid_runes` set
3. Trades with empty price arrays or zero/invalid quantities are skipped
4. Self-trades (offering and requesting the same rune) are skipped
5. Multi-item requested trades (AND trades) are kept but distinguished in stats

**Extracted CSV columns:** `TradeID, Offered, Requested`

Format: `Offered` = `"RuneName:quantity"`, `Requested` = `"Rune1:qty;Rune2:qty"`

## Price Calculation (Ist-Normalized VWAP)

For each segment:
1. Filter to single-item requests only (`NumAsks == 1`)
2. For each rune (excluding Ist):
   - **Bid side**: trades offering Ist for the target rune
   - **Ask side**: trades offering the target rune for Ist
3. VWAP per side = `sum(IstQty) / sum(RuneQty)`
4. Outlier filter: keep only trades with `0.5 <= IstsPerRune <= 50`
5. Blended FMV = average of bid and ask VWAP (single side if only one exists)

## Known Limitations

| Limitation | Impact | Notes |
|---|---|---|
| No pagination | Unknown data window | The API may return only the most recent N listings |
| `completed=true` unclear | May not be all completed trades | Could be "recently completed" only |
| No listing ID retained | Cannot cross-reference | `entry.id` is dropped in sanitization |
| Seller fields minimal | Cannot assess listing quality | Only username retained |
| No `completed_at` | Cannot age-weight trades | All trades weighted equally |
| Static 5s delay | Slow for 33 items × 4 segments | ~11 minutes per full run |
| Cloudflare dependency | Fragile | `cloudscraper` may break with Traderie changes |
| No retry backoff | Repeat failures on 5s delay | Two attempts only, then skip |
| Overwrite save pattern | Risk of data loss | Saves entire file per item — corruption risk |
| No segment metadata in output | No provenance | Extracted CSVs don't record which segment they came from |
| Only Ist-paired trades | Ignores non-Ist pairs | AND trades and non-Ist pairs are not modeled |
| Static outlier bounds | May not fit all runes | 0.5-50 range is hardcoded |

## Questions Not Yet Answered

These require a live/network audit (explicitly approved first):

1. **Pagination/window**: Does the API return all completed listings for an item, or only the most recent N? Is there a `limit` or `page` parameter that could extend the window? What is the maximum listing age returned?

2. **`completed=true` semantics**: Does this return only trades that were actually completed, or does it include expired/cancelled listings that were once completed? Is there a status field in the raw response?

3. **Listing IDs**: Is `entry.id` or a similar unique listing identifier available in the current API response? It is present in the web UI but may not be in the API payload.

4. **Richer fields available**: Does the raw response include `created_at`, `expires_at`, `completed_at`, `platform`, `buyer`, `seller.rating`, `seller.total_trades`? These are visible in the web UI.

5. **Cloudflare behavior**: Does cloudscraper reliably handle Traderie's Cloudflare configuration? Are there session/IP-based rate limits? Does the Cloudflare challenge change frequency with usage patterns?

6. **ToS/robots constraints**: Does Traderie's terms of service or robots.txt restrict API access for completed trade collection? Is there a published API or is this a reverse-engineered endpoint?

7. **History depth**: How much historical trade data can be accumulated? If the API only returns recent trades, repeated daily fetches would be needed to build history. If it returns all trades, a single backfill could capture the full dataset.

8. **Pagination limit**: Is there a maximum number of items the API returns per request? Is it possible to page through all results, or is there a hard cap (e.g. 100, 1000)?

9. **Rate limiting**: What is the effective rate limit? The current 5-second delay works, but is that necessary or overly conservative?

10. **Raw response envelope**: What fields are present in the top-level API response (total count, page info, etc.)? These are currently discarded by `raw.get("listings", [])`.
