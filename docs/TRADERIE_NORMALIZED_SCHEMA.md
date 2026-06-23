# Traderie Normalized Schema — Private Record Format

## Purpose

This schema defines a private normalized record format for individual completed trade observations from the Traderie API. It is intended for internal storage only, not for public distribution.

The current pipeline discards several raw fields that should be retained for audit, cross-referencing, and future model improvements. This schema proposes what a complete normalized record should look like.

## Schema

```json
{
  "schema_version": "0.1",
  "record_id": "unique_record_uuid",
  "source_slug": "traderie_api",
  "fetched_at": "2026-06-20T12:00:00Z",
  "parser_version": "fetch_v1",

  "query_params": {
    "segment": "pc_sc_nl",
    "prop_Platform": "PC",
    "prop_Mode": "softcore",
    "prop_Ladder": "false",
    "item_id": 2290642411,
    "completed": true,
    "auction": false
  },

  "source": {
    "listing_id": null,
    "status": null,
    "created_at": null,
    "updated_at": "2026-06-20T04:09:30.288Z",
    "completed_at": null,
    "expires_at": null
  },

  "seller": {
    "username": "seller_name",
    "user_id": null,
    "rating": null,
    "total_trades": null
  },

  "buyer": {
    "username": null,
    "user_id": null
  },

  "offered": {
    "item_name": "Ist Rune",
    "item_id": 2290642411,
    "quantity": 9
  },

  "requested": [
    {
      "item_name": "Jah Rune",
      "item_id": 2552039455,
      "quantity": 1
    }
  ],

  "trade_type": "single_item",
  "platform": "PC",
  "is_completed": true,

  "raw_properties": {},
  "audit_notes": ""
}
```

## Field Definitions

### Identity

| Field | Required | Description |
|---|---|---|
| `schema_version` | yes | Schema version string |
| `record_id` | yes | UUID or hash of source fields for deduplication |
| `source_slug` | yes | Always `traderie_api` |
| `fetched_at` | yes | When we fetched this record (UTC ISO8601) |
| `parser_version` | yes | Version of the fetch script that created this record |

### Query Context

| Field | Required | Description |
|---|---|---|
| `query_params.segment` | yes | Canonical segment slug |
| `query_params.prop_Platform` | yes | Platform from query |
| `query_params.prop_Mode` | yes | Mode from query |
| `query_params.prop_Ladder` | yes | Ladder flag from query |
| `query_params.item_id` | yes | Traderie item ID that was queried |

### Source Timestamps

| Field | Required | Description |
|---|---|---|
| `source.listing_id` | no | Traderie listing ID (if available in API payload) |
| `source.status` | no | Listing status from API |
| `source.created_at` | no | When the listing was created |
| `source.updated_at` | yes | When the listing was last updated (used for dedup) |
| `source.completed_at` | no | When the trade was completed |
| `source.expires_at` | no | When the listing expires |

### Seller & Buyer

| Field | Required | Description |
|---|---|---|
| `seller.username` | yes | Seller display name |
| `seller.user_id` | no | Seller internal ID |
| `seller.rating` | no | Seller rating |
| `seller.total_trades` | no | Seller total trade count |
| `buyer.username` | no | Buyer username (if completed trade) |
| `buyer.user_id` | no | Buyer internal ID |

### Trade Data

| Field | Required | Description |
|---|---|---|
| `offered.item_name` | yes | Name of the offered item |
| `offered.item_id` | yes | Traderie item ID of the offered item |
| `offered.quantity` | yes | Quantity offered |
| `requested[]` | yes | Array of requested items (may be 1 or more for AND trades) |
| `requested[].item_name` | yes | Name of requested item |
| `requested[].item_id` | yes | Traderie item ID of requested item |
| `requested[].quantity` | yes | Quantity requested |
| `trade_type` | yes | `single_item`, `and_trade`, `unknown` |
| `platform` | yes | Platform from response or query |

### Audit

| Field | Required | Description |
|---|---|---|
| `raw_properties` | no | JSON object preserving any fields not otherwise captured |
| `audit_notes` | no | Free-text notes about this record |

## What Must NOT Be Published Publicly

- **Seller usernames and IDs** — could identify individual traders
- **Buyer usernames and IDs** — could identify individual traders
- **Exact timestamps** down to the second — could be used to identify individuals
- **User ratings and trade counts** — seller-specific metrics

The public `in_game_rune_values.json` should contain only **aggregated, de-identified price data** with no user-level fields and only day-level or coarser timestamps.

## Migration Plan

1. **Current state**: Minimal fields retained, no listing IDs, no buyer info, aggregated CSVs
2. **Short-term**: Add `entry.id` retention, enrich seller fields, store complete raw response
3. **Medium-term**: Migrate from flat JSON to the normalized record format, with separate raw/aggregated storage
4. **Long-term**: Move to a queryable normalized store (SQLite or similar) for historical analysis

The normalized schema should be adopted before adding support for non-rune items or multi-source deduplication.
