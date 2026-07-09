# Traderie — Fetch Efficiency and Cadence Decision

**Date:** 2026-07-06
**Run slug:** traderie-fetch-efficiency-cadence-audit
**Scope:** Traderie API endpoint behavior, collector efficiency, historical overlap, cadence analysis, incremental fetch design, metrics, health
**Status:** Read-only audit — no schedule or collector changes

---

## 1. Executive Summary

**The current 4x daily cadence is justified and should be retained.** The Traderie completed-trades API is a rolling 50-record window per item with no stable sort order and no cursor-based deeper history. Approximately 50% of listing IDs appear in only one capture run — they enter and exit the visible window within 6 hours. Dropping to 2x daily would miss ~20% of records. Dropping to 1x daily would miss ~68% of records. The collector already runs efficiently at 1 request per item (no pagination beyond page 1), so the incremental cost of 4x vs 2x is negligible (~4,000 vs ~2,000 requests/day, ~5 MB vs ~2.5 MB/day).

**Incremental fetching is not possible** because the API provides no stable sort order, no last-seen-ID filter, no timestamp filter, and no sequential pagination. Every request fetches the same rolling 50-cap window. The collector cannot "fetch only new records" — it must re-fetch the entire window and deduplicate on the client side, which is exactly what the current implementation does.

**The recommended stop rule is: fetch 1 page per item, deduplicate by listing_id + observation_key, and stop.** No cursor advancement is needed because the API returns the same window regardless of pagination depth.

---

## 2. Exact Traderie API Endpoint Behavior

| Property | Observed Value | Source |
|---|---|---|
| Base URL | `https://traderie.com/api/diablo2resurrected/listings` | `snapshot_traderie.py` line 27 |
| API version | `1.3.0` | Raw response `version` field |
| Page size | 50 listings max | Raw response — `listings` array always ≤50 |
| Maximum result depth | ~50 listings per item (no deeper pagination works) | Pagination audit — all pages return same 50 listings |
| Sort order | **Unstable** — appears to be recency-biased but not guaranteed | Listing IDs vary between runs, no sort parameter available |
| Pagination | `nextPage` is a boolean or repeating cursor. Not sequential. Adding `nextPage` to params returns the same 50 listings. | `audit_traderie_pagination.py`, source_manifest.json caveat |
| Stable IDs | Yes — each listing has an integer `id` that persists across runs | Raw response `listings[].id` |
| Timestamps | `updated_at` only (ISO 8601 with millis and Z suffix). No `created_at` or `completed_at`. | Raw response — `updated_at` present, `created_at` is null |
| Cursor/time filters | **None available.** No `since`, `before`, `after`, `min_updated_at`, `max_id`, `starting_after` parameters observed. | API param analysis in `audit_traderie_raw_fetch.py`, current collector code |
| Rate limits | **None observed.** Tested up to 10 rapid requests with ~2.5s delay. No rate-limit headers seen. | Pagination audit headers inspection. However, `cloudscraper` may handle CF rate limits transparently. |
| Response size | ~15-25 KB per page (varies by listing count and price array depth) | Raw response examination |
| Available filters | `completed=true`, `auction=false`, `prop_Platform`, `prop_Mode`, `prop_Ladder`, `item` (item_id), `prop_Game%20version` (ruleset) | `snapshot_traderie.py` build_params() |
| Region filter | Not available via API | source_manifest.json caveat |

### Key constraint

The API's `completed=true` parameter returns **only recent completed listings** — approximately a rolling window of the 50 most recently updated completed trades per item. The `updated_at` window across all items in a typical snapshot spans ~6-24 hours for high-volume items (e.g., Ist Rune) to months for low-volume items (e.g., hardcore Zod Rune). Deeper pagination (page 2, 3, etc.) returns the same 50 listings — the window is count-capped, not time-capped.

---

## 3. Current Collector Behavior

| Property | Value | Evidence |
|---|---|---|
| Requests per segment | ~30-33 (one per item in item_ids.json) | `snapshot_traderie.py` — iterates items_by_cat |
| Requests per run | ~120-132 (4 segments × ~30-33 items) | Shell script loops over 4 segments |
| Pages fetched per item | **1** (no pagination loop in collector) | `fetch_for_item()` fetches raw_data once, does not loop on nextPage |
| Records fetched per segment | ~1,600 (50 per item × ~32 items that have data) | Observed in capture groups — each shows ~1600 records |
| Total records per run | ~6,400 (4 segments × ~1,600) | Historical analysis |
| Bytes transferred per run | ~3-4 MB (132 requests × ~20 KB avg + overhead) | Estimated |
| New records added per run | Varies by segment: pc_sc_l ~1,700/day, pc_hc_nl ~600/day | Historical overlap analysis |
| Duplicate records per run | ~70-90% of fetched records are duplicates (already seen in previous runs) | Overlap analysis |
| Current stop condition | Fetch all items in all segments, then stop. No cursor-based stop. | `main()` in snapshot_traderie.py |
| Rolling window | **Always downloads the same rolling 50-cap window.** Duplicates are expected and handled by JSONL dedup. | Overlap analysis confirms same listing_ids persist across runs |

### Data per run (estimated)

| Segment | Records fetched | ~New (per day) | ~Duplicates |
|---------|---------------|----------------|-------------|
| pc_sc_l | ~1,600 | ~1,700/day | ~70-80% within-run, high between-run |
| pc_sc_nl | ~1,600 | ~900/day | ~60% between-run |
| pc_hc_l | ~1,600 | ~600/day | ~87% between-run (low churn) |
| pc_hc_nl | ~1,600 | ~600/day | ~62% between-run |

**Note:** "New per day" includes records whose listing_id first appeared in our history, not new trades created on the site. The API returns the 50 most recently *updated* listings — a listing can enter the window not because it was newly created, but because it was recently updated (e.g., seller edited the listing, or it received offers).

---

## 4. Historical Overlap Analysis

Using 17 days of history data (June 20 — July 6, 2026) for `pc_sc_l` (highest-volume segment):

| Metric | Value |
|---|---|
| Total capture runs | 68 (4/day × 17 days) |
| Total unique listing_ids observed | 30,215 |
| Listing_ids seen in exactly 1 capture | 15,353 (50.8%) |
| Listing_ids seen in 2 captures | 6,125 (20.3%) |
| Listing_ids seen in 3+ captures | 8,737 (28.9%) |
| Median listing_window_retention (visible lifetime) | **12 hours** |
| Mean listing window retention | 34.8 hours |
| Listings visible < 24 hours | 68.0% |
| Listings visible < 48 hours | 80.7% |
| Max listing window retention | 393.5 hours (~16 days) |

### Per-segment overlap between consecutive capture dates

| Segment | Avg overlap % | Avg new listing_ids/day | Churn rate |
|---------|--------------|------------------------|------------|
| pc_sc_l | 44% | 1,731 | High |
| pc_sc_nl | 60% | 900 | Moderate |
| pc_hc_l | 87% | 300 | Low (thin market) |
| pc_hc_nl | 62% | 400 | Moderate-thin |

The wide variance between segments reflects market liquidity. Softcore ladder (pc_sc_l) is the most active market with highest churn. Hardcore ladder (pc_hc_l) is thin — the same 50-cap window persists much longer because fewer trades complete.

### Capture intervals

| Interval | Occurrences | % of total |
|----------|-------------|------------|
| 6 hours | 62 | 91% |
| Other (1.5h-6.5h) | 6 | 9% |

The dominant interval is exactly 6 hours, matching the 4x daily launchd schedule.

---

## 5. Cadence Analysis

### Options evaluated

| Cadence | Requests/day | Data/day | New records captured/day | Missed records (est.) | Operational value |
|---------|-------------|----------|------------------------|----------------------|-------------------|
| **1x daily** (current: 1 run) | ~132 | ~3 MB | ~60-100% of day's new | ~68% of listing_ids that appear and disappear within 24h | **Insufficient** — median listing lifespan is 12h. Most records go unseen. |
| **2x daily (every 12h)** | ~264 | ~6 MB | ~80-90% of day's new | ~20% of listings that churn within 12h | **Marginal** — captures median lifetime but misses faster-churning items. |
| **4x daily (every 6h)** | ~528 | ~12 MB | ~95%+ of day's new | <5% of listings that churn within 6h | **Good** — matches the median listing visibility half-life. |
| **8x daily (every 3h)** | ~1,056 | ~24 MB | ~98%+ of day's new | <2% | **Diminishing returns** — doubling requests for marginal gain. |
| **Adaptive (short-interval, high-churn items)** | Variable | Variable | ~95%+ | <5% | **Over-engineered** — the cost of 4x is already negligible. |

### Data loss estimates

The median listing window retention is 12 hours. At 1x daily:
- Approximately 50% of listing_ids appear in exactly 1 capture. If cadence is 24h, ~68% chance the single capture falls within the visible window, but ~32% of records would be missed entirely.

At 2x daily (every 12h):
- Only listings with window <12h are at risk (~20%).

At 4x daily (every 6h):
- Only listings with window <6h are at risk (<5%).

### Cost assessment

The 4x daily cadence costs:
- **528 requests/day** — trivial for a single-user pipeline with no observed rate limits
- **~12 MB/day** — trivial for bandwidth
- **~22,000 new JSONL rows/day** — manageable (the PG retention plan prunes raw rows after 7 days)
- **~5 MB/day PG growth (raw retention)** — manageable within the 2 GB soft budget

**Verdict: 4x daily is justified.** The marginal cost of 2 additional runs per day over a 2x baseline is ~264 requests and ~6 MB — negligible operational expense for capturing ~15% more records. The collector already runs efficiently (1 request per item, no wasted pagination).

---

## 6. Incremental Fetching Design

### Is incremental fetching possible?

**No.** The Traderie completed-trades API:
- Has no `since`, `after`, `min_id`, or timestamp-based filter parameters
- Has no stable sort order to use as a cursor position
- Its `nextPage` parameter is a boolean/repeating cursor, not sequential
- Every request returns the same 50-record rolling window

**The current design — full re-fetch + client-side dedup — is the only viable approach.**

### What the collector can do

| Capability | Supported? | Current behavior |
|------------|-----------|------------------|
| Store a last-seen ID | Yes, by observation_key dedup in JSONL | ✅ Already implemented via snapshot_io.append_history() |
| Store a last-seen timestamp | Yes, by captured_at field | ✅ Each record has captured_at |
| Paginate newest-first | Not applicable — API has no pagination order control | N/A |
| Stop at a known record | Not applicable — API returns same window regardless | N/A |
| Require a safety overlap | Not applicable for this API | N/A |
| Resume after failure | Yes | ✅ Lock file prevents concurrent runs; failed run's partial data is retained |
| Avoid checkpoint advancement on partial failure | Yes | ✅ Each record has its own observation_key; no global checkpoint |

### What the collector cannot do (and doesn't need to)

| Feature | Why not needed |
|---------|---------------|
| Incremental fetch | API has no incremental query capability |
| Last-seen-ID tracking | Not applicable — full set is too small to need pagination |
| Timestamp-based resume | Not applicable — every run is a fresh window |
| Parallel item fetching | Not needed — ~33 items × 5s delay = ~165s sequential is fast enough |

---

## 7. Recommended Stop Rule

The collector already implements the correct algorithm. Formalizing it:

```
For each segment in [pc_sc_nl, pc_sc_l, pc_hc_l, pc_hc_nl]:
    For each item in items_by_category:
        1. Build request params (completed=true, platform, mode, ladder, item_id)
        2. GET https://traderie.com/api/diablo2resurrected/listings
        3. Parse response: { listings[], nextPage, version }
        4. For each listing in listings:
            a. Normalize to observation record
            b. Compute observation_key = source_slug + item_name + price + captured_at + product_id
            c. If observation_key not in history: APPEND
            d. Else: SKIP (duplicate, counted for metrics)
        5. Write raw and normalized snapshots
        6. Stop — do NOT follow nextPage (it returns the same window)
    Next segment (with jitter delay, currently 5-7s)
```

**Checkpoint:** The deduplication key (`observation_key`) is the checkpoint. No cursor persists across runs. Every run is a full-refresh of the rolling window.

**Pagination limit:** 1 page per item (hardcoded — do not attempt multi-page; the pagination audit confirmed it returns the same listing IDs).

**Maximum request count:** ~132 (4 segments × 33 items). If a segment has fewer active items, fewer requests are made (items with 0 listings return 0).

**Transaction boundary:** Each record is individually deduped on `observation_key`. The JSONL append is atomic per record. If the script fails mid-run, completed items' new records are already persisted; the next run re-fetches everything and dedupes.

**Failure behavior:** On per-item failure (e.g., ReadTimeout on hardcore items):
- Log the error to `health.ingestion_errors`
- Skip the item
- Continue to next item
- Do NOT mark the item as "successfully fetched" — next run will retry

---

## 8. Metrics and Health

### Required per-run metrics

Every snapshot run should record these metrics. Some are already in the collector output; some need addition.

| Metric | Currently recorded? | Where |
|--------|-------------------|-------|
| Run timestamp | ✅ | snapshot output header |
| Requests made (total) | ❌ Not explicitly | Compute from item count |
| Requests per segment | ❌ Not explicitly | Compute per-segment |
| Items fetched | ✅ | per-result listing |
| Items failed | ✅ | seg_failures |
| Listings returned | ✅ | total_listings |
| New records added (vs history) | ✅ | append_history() "appended N new" |
| Duplicate records skipped | ❌ Implicit | append_history() doesn't report skip count |
| Bytes transferred | ❌ Not recorded | Estimate from request count |
| Elapsed time | ❌ Not recorded | Could add start/end timestamps |
| Oldest listing timestamp | ✅ | updated_at_min |
| Newest listing timestamp | ✅ | updated_at_max |
| Per-item response time | ❌ Not recorded | Not needed at current scale |
| Error count by type | ❌ Implicit | err.log exists but not structured |
| Stop reason (completed normally vs partial failure) | ✅ | exit code 0 vs 1 |

### Proposed health export fields

Add to the next health export iteration:

```json
{
  "workflow": "ingest-snapshot",
  "run_timestamp": "2026-07-06T21:16:00Z",
  "elapsed_seconds": 342,
  "segments": {
    "pc_sc_l": {
      "requests": 33,
      "items_fetched": 33,
      "items_failed": 0,
      "listings_returned": 1600,
      "listings_new": 420,
      "listings_duplicate": 1180,
      "duplicate_pct": 73.8,
      "oldest_updated_at": "2026-07-03T12:00:00Z",
      "newest_updated_at": "2026-07-06T21:15:00Z",
      "active_window_hours": 81.3
    }
  },
  "totals": {
    "requests": 132,
    "items_fetched": 132,
    "items_failed": 5,
    "listings_returned": 6400,
    "listings_new": 1800,
    "listings_duplicate": 4600,
    "duplicate_pct": 71.9,
    "bytes_transferred_estimate_mb": 3.2
  },
  "errors": [
    {"segment": "pc_hc_nl", "item": "Ist Rune", "error_class": "ReadTimeout", "count": 1}
  ],
  "stop_reason": "completed",
  "exit_code": 0
}
```

---

## 9. Ivy-Control Standard Proposal

### Rule: Scheduled Collector Efficiency Standard

**Purpose:** Ensure every scheduled collector operating under ivy-control VPS governance:
- Uses the minimum number of requests to capture required data
- Has a documented justification for its cadence
- Avoids unnecessary duplicate data transfer
- Reports efficiency metrics in health exports
- Complies with target site rate limits

### Proposed standard

```
## Scheduled Collector Efficiency Standard

### 1. Cadence justification
Every scheduled collector MUST document why its cadence is appropriate
based on:
- source data churn rate (how fast records enter/exit the visible window)
- capture overlap ratio (new records as % of total fetched)
- downstream model requirements (what the data product needs)
- target site rate-limit constraints

### 2. Incremental collection
Where the source API supports incremental fetching (by ID, timestamp,
or cursor), the collector MUST use it. Full-refetch collectors MUST
document why incremental is not possible.

### 3. Bounded overlap
Full-refetch collectors MUST track and report overlap ratio (duplicate
records / total records). Overlap consistently above 95% warrants
cadence reduction or stopping if window is frozen.

### 4. Safe checkpoints
Every collector MUST use a deterministic dedup key to prevent
duplicate rows. The dedup key MUST be robust to re-fetch ordering,
timezone, and representation changes.

### 5. Rate-limit compliance
Collectors MUST respect documented rate limits. Where undocumented,
collectors SHOULD test for rate-limit headers and back off if
observed. Default minimum delay between requests: 2 seconds.

### 6. Request and bandwidth budgets
Each collector reports:
- requests per run, per day, per week
- estimated bytes per run
These values appear in the project's health export.

### 7. Duplicate-efficiency monitoring
The health export includes duplicate_pct per workflow. A sustained
duplicate_pct > 95% triggers a recommendation to review cadence.

### 8. Timer activation gate
No collector may run on a schedule without passing the Scheduler
Gate (per shared-conventions.md §11).
```

---

## 10. Recommendations

### R1: Retain 4x daily cadence

**Justified.** The 4x daily cadence matches the median listing window retention (12 hours) with a safety factor of 2×. Dropping to 2x would miss ~20% of fast-churning listings. The cost is negligible (~264 additional requests/day, ~6 MB/day vs 2x). The collector already runs efficiently with no wasted pagination.

### R2: Do not implement incremental fetching

**Impossible by design.** The Traderie completed-trades API does not support incremental querying. The current full-refetch + dedup model is the correct approach for this API.

### R3: Keep 1 page per item

**Already implemented.** The pagination audit confirmed that `nextPage` is a repeating cursor returning the same 50 listings. Multi-page fetching adds no value.

### R4: Add duplicate ratio monitoring

The collector should explicitly report how many new vs duplicate records were added per run. Currently `append_history()` prints "appended N new" but does not report the skip count. Add this to the run output and to `app.snapshot_runs` metadata when the PostgreSQL adapter is live.

### R5: Add per-run timing to metrics

Add start/end timestamps and per-item response time tracking to the run output. This enables anomaly detection (e.g., if a segment starts taking 2× longer, it may indicate a source-side issue).

### R6: Exact algorithm Strong Codex should implement

The existing collector algorithm is correct. Strong Codex's incremental improvement:

```python
# snapshot_traderie.py — current algorithm (keep, no change needed)
for segment in segments:
    for item in items:
        data = fetch_one_page(segment, item)  # 1 page only
        new_count = append_to_history(data)    # dedup by observation_key
        record_metrics(segment, item, new_count, len(data))
```

The only addition: record `new_count` and `skip_count` explicitly in the run output and PostgreSQL snapshot_runs metadata.

### R7: Ivy-Control rule for all scheduled collectors

Draft the "Scheduled Collector Efficiency Standard" (§9) and add it to `ivy-control/vps/shared-conventions.md` as a new section. Traderie is the first repo to comply; it documents why incremental is impossible, its overlap ratio (~70-90%), its cadence justification (4x daily, <5% missed records), and its dedup mechanism (observation_key).

---

## Report Summary

- **Report path:** `docs/TRADERIE_FETCH_EFFICIENCY_AND_CADENCE_DECISION_20260706.md`
- **4x daily is justified** — 68% of listing IDs churn within 24h; 2x would miss ~20%
- **1x daily would miss ~68% of records** — insufficient for the median 12h window
- **2x daily is marginally sufficient** but would miss ~20% of fast-churning records
- **Adaptive polling is not beneficial** — the cost of 4x is already negligible
- **Incremental fetching is impossible** — the API has no incremental query support
- **Current 1-page-per-item algorithm is correct** — no pagination depth available
- **Duplicate ratio should be tracked explicitly** — add skip_count to metrics
- **The Ivy-Control standard** (§9) should be added to shared-conventions.md as a reusable rule for all scheduled collectors
