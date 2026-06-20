# Traderie Raw Response Audit — Jah Rune (pc_sc_nl)

**Date**: 2026-06-20
**Method**: Single `GET /api/diablo2resurrected/listings` with `completed=true`, `auction=false`, `prop_Platform=PC`, `prop_Mode=softcore`, `prop_Ladder=false`, `item=2552039455`
**Tool**: `scripts/audit_traderie_raw_fetch.py`
**Sample**: `data/research/traderie_raw_audit_jah_one_segment.sample.json`

---

## Envelope Shape

```
{
  "listings": [ ... ],   # array, 50 items
  "nextPage": 1,          # int — truthy means more pages exist
  "version": "1.3.0"      # API version string
}
```

**No `total`, `page`, `limit`, `has_next`, `pages`, `offset`, or `count` fields.** Pagination is cursor-based via `nextPage` (truthy = more pages). No `Link` header or rate-limit headers observed (single request).

---

## Listing-Level Fields (86 distinct paths)

### Currently Retained by `sanitize_trade_entry`

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `seller.username` | str | `"GergőMolnár86774"` | Stored as flat `seller` string |
| `amount` | int | `1` | Stored as `quantity` |
| `updated_at` | str | `"2026-06-20T08:51:47.781Z"` | Dedup key |
| `prices[].name` | str | `"Ist Rune"` | In `price[].name` |
| `prices[].quantity` | int | `11` | In `price[].quantity` |

### Currently Dropped (but available)

#### Identifiers
| Field | Type | Example |
|-------|------|---------|
| `id` | str | `"1002370977020"` — listing UUID |
| `item_id` | str | `"2552039455"` — item ID being sold |
| `seller_id` | str | `"2888986869"` — seller user ID |

#### Seller Object (dict — 28 fields, most null)
| Field | Type | Example |
|-------|------|---------|
| `seller.id` | int | `2888986869` |
| `seller.rating` | int | `5` — star rating |
| `seller.reviews` | int | `173` — **total trade count** |
| `seller.status` | str | `"online"` |
| `seller.leaderboard_optin` | bool | `false` |
| `seller.username` | str | `"GergőMolnár86774"` |
| `seller.bio` | str (nullable) | `null` |
| `seller.profile_img` | str (nullable) | `null` |
| `seller.discord`, `seller.xbox`, `seller.psn`, `seller.other`, `seller.twitter` | all nullable | contact methods |

#### Price Items (full objects)
| Field | Type | Example |
|-------|------|---------|
| `prices[].id` | int | `2290642411` — item ID |
| `prices[].item_id` | int | `2290642411` |
| `prices[].listing_id` | int | `1002370977020` |
| `prices[].img` | str | `"https://cdn.nookazon.com/.../ist_rune.png"` |
| `prices[].slug` | str | `"ist-rune"` |
| `prices[].type` | str | `"runes"` |
| `prices[].group` | int | `0` |
| `prices[].add` | bool | `false` — additive flag |
| `prices[].selling` | bool (nullable) | `null` |
| `prices[].properties` | dict (nullable) | `null` — item-specific properties |
| `prices[].variant_id` | nullable | — |
| `prices[].variant_format` | nullable | — |
| `prices[].variant_img` | nullable | — |
| `prices[].variant_name` | nullable | — |

#### Properties Array (Segment Info)
`properties` is an array of 4 objects encoding the trade's segment:

| Property | `property` value | `string` value |
|----------|-----------------|----------------|
| Game version | `"Game version"` | `"reign of the warlock"` |
| Platform | `"Platform"` | `"PC"` |
| Mode | `"Mode"` | `"softcore"` |
| Ladder | `"Ladder"` | `null` (bool type, `bool: false` for Non Ladder) |

Each property has: `id`, `img`, `bool`, `date`, `type`, `format` (with values/colors), `number`, `string`, `options`, `property`.

#### Boolean Flags
| Field | Type | Value |
|-------|------|-------|
| `completed` | bool | `true` |
| `active` | bool | `true` |
| `selling` | bool | `true` (vs buying) |
| `standing` | bool | `false` |
| `stock` | bool | `false` |
| `make_offer` | bool | `false` |
| `accept_listing_price` | bool | `false` |
| `offer_wishlist` | bool | `false` |

#### Other
| Field | Type | Value |
|-------|------|-------|
| `total_offers` | str | `"0"` |
| `variant_id` | nullable | — |
| `wishlist_id` | nullable | — |
| `offer_wishlist_id` | nullable | — |

---

## Key Findings / Surprises

1. **No buyer field**: API responses for completed trades do **not** include a `buyer` object. Buyer identity is not exposed.

2. **No aggregate pagination metadata**: No `total`, `page`, `limit`, `pages`. Just `nextPage` (int, truthy = has next page). This makes progress tracking impossible without iterating until `nextPage` is falsy.

3. **Pagination is cursor ID-based**: `nextPage` = `1` after the first page of 50 results. The page size appears fixed at 50 listings.

4. **No rate-limit headers** observed in this single request.

5. **Seller has `reviews` (total trades)**, not `total_trades`. The key is `seller.reviews` (int).

6. **IDs are strings** at listing level (`id`, `item_id`, `seller_id`) but **ints** in the seller object (`seller.id`) and price items (`prices[].id`).

7. **`updated_at` is the only timestamp**: No `created_at` or `completed_at`. You cannot distinguish when the listing was created vs when the trade completed.

8. **Segment info is in `properties[]` array** on each listing (not on the envelope). It must be parsed from `properties[].property` + `properties[].string` / `properties[].bool`.

9. **`version` field at top level** (`"1.3.0"`) — could be useful for tracking API changes.

10. **`total_offers` is a string** even though it's a count.

---

## Recommended Fields for Future `fetch_completed_trades.py` Update

Add to `sanitize_trade_entry()`:

| Priority | Field | Why |
|----------|-------|-----|
| **High** | `seller.rating` | Seller trust signal |
| **High** | `seller.reviews` | Seller total trade count — useful for weighting |
| **Medium** | `id` | Listing UUID — could help dedup beyond `updated_at` |
| **Medium** | `seller.status` | Online/offline state |
| **Medium** | `prices[].item_id` | Canonical item ID for price items |
| **Low** | `properties[].property` + `string`/`bool` | Redundant (already filtered by query params) but useful cross-check |
| **Low** | `active`, `completed`, `selling` | Redundant (filtered by params) but useful for verification |
| **Low** | `version` | API version tracking |

---
