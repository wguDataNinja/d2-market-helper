# Traderie Pagination / Window Audit

## Summary

Completed trades from `GET /api/diablo2resurrected/listings?completed=true` are served as a **single page of at most 50 listings** reflecting a **rolling ~7-hour window**. There is no functional pagination — `nextPage` is a boolean-like integer (`1`) that returns the same results when passed back.

## Methodology

- **Item:** Jah Rune (`item_id=2552039455`)
- **Segment:** PC Softcore Non-Ladder (`prop_Platform=PC`, `prop_Mode=softcore`, `prop_Ladder=false`)
- **Script:** `scripts/audit_traderie_pagination.py`
- **Data:** `data/research/traderie_pagination_audit_jah_pc_sc_nl.sample.json`
- **Requests:** 10 sequential pages with `nextPage` cursor, 2.5s delay between requests
- **HTTP status:** 200 on all 10 requests (no rate limiting, no blocking)

## Results

| Metric | Value |
|---|---|
| Pages fetched | 10 |
| Listings per page | 50 (all 10 pages identical) |
| Total raw listings | 500 |
| **Total unique listing IDs** | **50** |
| Duplicate count | 450 |
| `updated_at` min | `2026-06-20T03:14:16.141Z` |
| `updated_at` max | `2026-06-20T10:37:37.617Z` |
| Time window | **7.4 hours** |
| `nextPage` behavior | Returns `1` always; passing it back yields same 50 listings |
| Rate limiting | None observed |
| Blocking | None observed |

## Findings

### 1. nextPage is not a cursor — it is a boolean flag

`nextPage` is always the integer `1` when there is data. When passed back as a query param, the server returns the **exact same 50 listings** with the same `nextPage: 1`. This means:

- It is not a page index (does not increment).
- It is not a cursor (does not advance position).
- It behaves like a `hasMore: true` boolean, except that requesting "more" yields no new data.

### 2. Only one page of completed trades exists

The API exposes exactly **50 completed trades** for this item/segment. There is no way to paginate deeper. The 50 listings are the most recent completed trades the server has chosen to retain.

### 3. Results are newest-first (descending `updated_at`)

Listing 1 on page 1 has `updated_at` ~10:37, listing 50 has ~03:14. The ordering is monotonic decreasing. This is consistent across all 10 requests (same 50 items, same order).

### 4. Page size is stable at 50

Every request returned exactly 50 listings. This is almost certainly a server-enforced cap.

### 5. The window is a rolling 7-8 hours

The `updated_at` range spans ~7.4 hours. This likely slides as time passes — older trades fall off and newer trades appear. The depth is determined by trade volume for that item; a low-volume item might retain trades for days, while a high-volume item like Jah Rune cycles in hours.

### 6. No rate limiting or blocking

All 10 sequential requests returned HTTP 200 within 0.2-0.5s each. Cloudflare headers are present (`cf-cache-status: DYNAMIC`, `CF-RAY`) but no `x-ratelimit-*` headers were observed.

## Historical Coverage Implications

**`completed=true` offers NO historical depth.** Only the most recent ~50 trades (roughly 7 hours for high-volume items) are available. This means:

1. **Cannot backfill history via pagination.** There is no way to paginate deeper into completed trades.
2. **Long-term historical coverage requires periodic snapshots.** You must poll regularly (e.g., every 1-6 hours) to capture trades before they fall off.
3. **Low-volume items may have wider windows.** If only 10 trades occurred in the last week, the window could span days. The cap is on count (50), not time.
4. **Freshness labels are straightforward.** The data is always "recent" — within hours for high-volume items. A label like "Last 24 hours" would be technically accurate but possibly misleading since low-volume items may span longer. Recommend: **"Recent trades"** or **"Last ~50 trades"**.

## Recommended Freshness Label for Traderie

**"Recent trades"** — because the window is count-based (50 listings) rather than time-based. A time label implies a guarantee the API doesn't make. For UI, consider showing the actual `updated_at` range of displayed trades so users see exactly how fresh the data is.

## Future Work

- Run the same audit on a low-volume item (e.g., a specific Unique or gem) to see how far back the 50-listing window extends.
- Re-run the Jah Rune audit at different times of day to confirm the window slides and establish the churn rate.
- Investigate whether `?completed=true` with different `sort` params changes pagination behavior.
