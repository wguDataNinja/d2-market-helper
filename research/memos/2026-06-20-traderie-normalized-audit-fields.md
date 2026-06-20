# Traderie Normalized Audit Fields

## What Changed

Two pipeline scripts were updated to retain audit-critical fields that were previously dropped during capture and extraction:

### `fetch_completed_trades.py` — Raw Capture

| Field | Source | Why |
|---|---|---|
| `listing_id` | `listing.id` | Unique identifier for each listing. Enables cross-referencing with Traderie UI, dedup by ID, and verifying that repeated fetches don't re-record the same listing. |
| `seller_rating` | `seller.rating` | Seller reputation (1-5). Useful for filtering suspicious trades (e.g., brand-new sellers with 0 rating). |
| `seller_reviews` | `seller.reviews` | Total completed trades by that seller (per audit, this is the count of past reviews, i.e., trade count). Higher = more established. |
| `item_id` | `prices[].item_id` | The canonical item ID for each price/consideration entry. Enables exact item matching without relying on name strings. |
| `active` | `listing.active` | Whether the listing is still active. All returned listings are `completed=true` in the query, but a listing can be both completed and active. |
| `completed` | `listing.completed` | Explicit boolean for completion status (already filtered by query param, but stored for completeness). |
| `version` | `response.version` | API response version. May change with Traderie API updates. Future-proofing for API drift detection. |
| `nextPage` | `response.nextPage` | Cursor for paginated responses. Null for single-page responses. Enables paginated fetch in future. |
| `platform` | `properties[].Platform.string` | Explicit platform string (e.g., "pc", "xbox"). Extracted from listing properties array. |
| `mode` | `properties[].Mode.string` | "softcore" or "hardcore". Extracted from listing properties array. |
| `hardcore` | Derived from `mode` | Boolean: true if mode == "hardcore". |
| `ladder` | `properties[].Ladder.bool` | Boolean: true = Ladder, false = Non Ladder. Extracted from properties array. |

### `extract_rune_trades.py` — Extracted CSV Records

| Column | Source | Why |
|---|---|---|
| `listing_id` | Raw listing | Pass-through from raw capture for traceability back to source API response. |
| `seller_rating` | Raw listing | Pass-through for downstream analysis (e.g., confidence weighting by seller reputation). |
| `seller_reviews` | Raw listing | Pass-through — seller experience level. |
| `platform` | Segment constant | Explicit per-record instead of only inferring from filename. |
| `ladder` | Segment constant | Explicit boolean. |
| `hardcore` | Segment constant | Explicit boolean. |
| `segment_slug` | Segment constant | e.g., `pc_sc_l`. Enables filtering/grouping without filename parsing. |

## Fields Still Missing (and Why)

| Field | Reason |
|---|---|
| `buyer` fields | Not exposed by Traderie API. No `buyer` key exists in any listing response. Audit confirmed zero listings with buyer data. |
| `created_at` | Not exposed by Traderie API. Only `updated_at` is available per listing. |
| `completed_at` | Not exposed by Traderie API. Completion time is not returned. |
| `seller.id` | Not retained; purely internal. The `seller_id` at listing level is available via `listing.seller_id` if ever needed. |

## Explicit Segment Metadata Approach

Previously, segment context was only available from the filename (e.g., `raw_trades_pc_sc_l.json`). This created two problems:
1. A raw file could be renamed or moved, losing segment context.
2. The extractor could only infer segment from a hardcoded filename mapping.

Now each raw listing carries its own segment metadata extracted from the Traderie API's `properties[]` array. The extractor also writes explicit segment columns (`platform`, `ladder`, `hardcore`, `segment_slug`) into every CSV row, making the data self-describing and immune to filename drift.

## Impact on Downstream Processing

- **VWAP calculation**: Unchanged. `calculate_rune_prices.py` reads `Offered` and `Requested` columns only, which are unchanged.
- **Price product generation**: Unchanged. `generate_prices_json.py` reads from price CSVs, not extracted CSVs.
- **Backward compatibility**: Existing raw files without new fields still work. Missing fields default to `null`/empty in the extractor.
