# Traderie vs Diablo2.io Diagnostic Comparison Design

Date: 2026-06-20
Status: Design only — no implementation, no blending, no canonical prices.

## 1. Comparable Unit

### Recommendation: Pair ratios first, Ist-equivalent second, both in output

**Primary: Pair ratios (Jah:Ber, Ber:Lo, etc.)**
- Diablo2.io rows express consideration in raw runes (e.g., "2 Ber", "1 Sur + 1 Lo", "11 Ist").
- Pair ratios require zero conversion assumptions — the raw consideration *is* the ratio.
- Example: "WTS SOLD 2 Jah for 2 Ber" → ratio Jah:Ber = 1.0. Compare against Traderie's Jah/Ber implicit ratio (17.25 / 12.43 = 1.39).
- This is the most independent comparison; Traderie does not compute or expose pair ratios directly, so this is genuine cross-validation.

**Secondary: Ist-equivalent value**
- Where consideration contains Ist directly (e.g., "11 Ist for Jah"), the Ist value is directly observable.
- Where consideration is non-Ist runes, convert to Ist using Traderie's OWN in_game_rune_values (e.g., 1 Sur = ? Ist, 1 Lo = 6.24 Ist, 1 Sur + 1 Lo = ? + 6.24 Ist).
- **Caveat:** This is partially circular — using Traderie prices to evaluate Diablo2.io trades. Therefore:
  - Always label Ist-equivalent rows as `ist_conversion_method: "direct"` (consideration contains Ist) or `ist_conversion_method: "via_traderie_prices"` (converted using Traderie values).
  - The pair-ratio comparison is the independent diagnostic; Ist-equivalent is secondary.

**Not recommended:** Blended canonical price, average of two sources, or any single-number output.

### Ist-equivalent conversion rules (diagnostic only, no blending)

| Consideration Type | Conversion Method | Label |
|---|---|---|
| Pure Ist (e.g., 11 Ist for Jah) | Direct — Ist Qty is value | `direct` |
| Single non-Ist rune (e.g., 2 Ber for 2 Jah) | value_ist = qty * Traderie[consideration_rune].value_ist | `via_traderie_prices` |
| Mixed runes (e.g., 1 Sur + 1 Lo for Jah) | value_ist = sum(qty_i * Traderie[item_i].value_ist) | `via_traderie_prices` |
| Unknown item in consideration | Exclude from Ist-equivalent comparison | `unconvertible` |

## 2. Minimum Parse Classes Allowed

| Parse Class | Eligible | Rationale |
|---|---|---|
| `clean_single_rune` | **Yes** | Single consideration item, known rune, structured. Most reliable. |
| `clean_multi_rune` | **Yes** | Multiple consideration items, all known runes, structured. Convertible via Ist or pair ratio. |
| `quantity_bundle` | **Yes, normalized** | target_quantity > 1. Normalize: ratio = consideration / target_quantity. Emit both raw and normalized in diagnostic output. |
| `description_only_consideration` | **No** | Consideration inferred from free-text description. Unreliable for comparison. |
| `missing_consideration` | **No** | No price data available. |
| `parse_failed` | **No** | Corrupt/unparseable data. |

### Additional eligibility gates (all must pass)

1. Buyer must be confirmed (named `buyer`) — strongest signal of completed two-party trade.
2. All consideration items must be known runes (in RUNE_NAMES).
3. Target item must match the searched item (uitemid validation).
4. Side must not be "unknown".

## 3. WTS vs WTB Handling

**Decision: Include both WTS and WTB. Do NOT invert or adjust WTB.**

- WTS SOLD: Seller sold target item. Consideration is what buyer paid. Standard seller perspective.
- WTB SOLD: Buyer was looking to buy. Row shows what they offered/accepted. Economic price is the same numeric value.
- Preserve `trade_side` in output as-is: `"WTS"` or `"WTB"`.
- Add a diagnostic flag `payer_is_poster: true` for WTB rows (poster is the payer, not the receiver).
- No confidence penalty for WTB rows in the comparison, but surface the side distribution so a reader can assess.

## 4. Quantity Bundle Handling

- Normalize: divide consideration quantities by target_quantity.
  - Example: "2 Jah for 2 Ber" → normalized: 1 Jah for 1 Ber → ratio Jah:Ber = 1.0.
- Emit both `raw_consideration` (as-is from parser) and `normalized_consideration` in the output.
- When bundle is heterogeneous (different consideration items), normalize each item quantity:
  - "2 Jah for 2 Ber + 2 Ist" → normalized: 1 Jah for 1 Ber + 1 Ist.
- Do NOT normalize when bundle contains non-divisible consideration (the only items in scope are runes, which are divisible in quantity).

## 5. Mixed-Rune Consideration

**Decision: Include mixed-rune rows, but label their comparison tier.**

| Tier | Description | Eligible rows | Use in Ist comparison |
|---|---|---|---|
| Tier 1 | Single-rune consideration, Ist-pair | clean_single_rune where consideration[0].item == "Ist" | Yes — direct Ist value |
| Tier 2 | Single-rune consideration, non-Ist | clean_single_rune where consideration[0].item != "Ist" | via_traderie_prices |
| Tier 3 | Multi-rune consideration | clean_multi_rune, quantity_bundle | via_traderie_prices |
| Tier 4 | Unconvertible / unknown | Any row with non-rune items | Exclude from Ist comparison; show in pair-ratio comparison only |

All tiers are eligible for **pair-ratio comparison** (the primary diagnostic). Tiers 1-3 are eligible for Ist-equivalent comparison; Tier 4 is not.

## 6. Segment Handling

### Current state
- Diablo2.io segment confidence: "medium" (3/5 fields proven — ladder, platform, ruleset confirmed; hardcore/softcore unknown; region sometimes known).
- Traderie segment: fully explicit (API returns platform, mode, ladder, hardcore).

### Comparison rules

1. **Only compare same-segment rows.** Cross-segment comparison (pc_sc_l Jah vs pc_sc_nl Jah) is invalid.
2. Diablo2.io rows with `segment_confidence: "medium"` are eligible for comparison, but each comparison row gets a `segment_match_label`:
   - `"exact"` — all 5 segment dimensions match between sources.
   - `"partial"` — 3-4 dimensions match, hardcore or region unverified for Diablo2.io side.
   - `"mismatch"` — one or more known dimensions differ → exclude from comparison.
3. When Diablo2.io `hardcore` is `"unknown"`, default to softcore for segment matching (softcore is the default D2R mode). Flag this as `hardcore_assumed: true`.

### Segment match matrix

| Diablo2.io known dimensions | Match quality | Eligible? |
|---|---|---|
| platform + ladder + ruleset + hardcore + region | `exact` | Yes |
| platform + ladder + ruleset + region (hc unknown) | `partial` (hc assumed sc) | Yes |
| platform + ladder + ruleset (hc + region unknown) | `partial` (hc assumed sc, region unverified) | Yes |
| Only 1-2 known | `low_confidence` | No |

## 7. Time-Window Mismatch

### Current state
- Traderie: Each listing has `updated_at` but no `created_at` or `completed_at`. The time window captured is defined by the paginated fetch of completed listings and is not precisely bounded.
- Diablo2.io: Each row has `sold_at_relative` ("15 hours ago") and `sold_timestamp` (parsed date string).

### Comparison labeling

Each comparison row gets a `time_match_label`:

| Condition | Label |
|---|---|
| Both trades within same calendar week | `same_week` |
| Both trades within same calendar day | `same_day` |
| Traderie window cannot be determined precisely | `unknown_window` |
| Explicitly different weeks (Diablo2.io row is weeks older than Traderie's fetch window) | `different_period` |

### Fields to include
- `diablo2io_sold_at_relative` — string from parser
- `diablo2io_sold_timestamp` — parsed date string
- `traderie_updated_at` — from Traderie raw listing (if available)
- `time_match_label` — computed classification

## 8. Disagreement Reporting (No Blending)

### Core principle
**Never blend, average, or pick a winner.** All outputs are diagnostic side-by-side comparisons.

### When Traderie and Diablo2.io disagree
Example: Traderie says Jah=17.25 Ist (pc_sc_l), Diablo2.io shows Jah sold for 11 Ist (pc_sc_nl).

Output structure per comparison:
```json
{
  "rune": "Jah",
  "segment": "pc_sc_l",
  "traderie_value_ist": 17.2533,
  "diablo2io_value_ist": null,
  "delta_ist": null,
  "delta_pct": null,
  "source_a_label": "traderie",
  "source_b_label": "diablo2io",
  "traderie_observations": {
    "value_ist": 17.2533,
    "bid_price": 16.3884,
    "ask_price": 18.1181,
    "bid_count": 102,
    "ask_count": 118,
    "total_trades": 220,
    "confidence": "high",
    "source": "Traderie completed listings",
    "time_window_label": "unknown_window"
  },
  "diablo2io_observations": {
    "value_ist": null,
    "raw_observations": [],
    "observations_count": 0,
    "segment_match_label": "partial",
    "segment_note": "Diablo2.io l=non_ladder, Traderie segment=l — mismatched. Excluded from Ist comparison."
  },
  "delta_ist": null,
  "delta_pct": null,
  "time_match_label": "not_applicable",
  "segment_match_label": "mismatch",
  "disagreement_reasons": [
    "Segment mismatch: Traderie pc_sc_l (ladder) vs Diablo2.io pc_sc_nl (non-ladder). Jah is typically worth more on ladder.",
    "Time window unknown for Traderie — may be different trading periods."
  ],
  "no_comparison_possible": true,
  "notes": "Segment mismatch prevents direct comparison. Both values are correct for their respective segments."
}
```

When segments match and both have values:
```json
{
  "rune": "Jah",
  "segment": "pc_sc_nl",
  "traderie_value_ist": 11.6524,
  "diablo2io_value_ist": 11.0,
  "delta_ist": -0.6524,
  "delta_pct": -5.6,
  "source_a_label": "traderie",
  "source_b_label": "diablo2io",
  "traderie_observations": { ... },
  "diablo2io_observations": {
    "value_ist": 11.0,
    "ist_conversion_method": "direct",
    "raw_observations": [
      {
        "parse_class": "clean_single_rune",
        "trade_side": "WTB",
        "target_quantity": 1,
        "consideration": [{"item": "Ist", "quantity": 11}],
        "sold_at_relative": "15 hours ago",
        "sold_timestamp": "Fri Jun 19, 2026 4:47 pm",
        "buyer": "varangium",
        "segment_match_type": "partial",
        "hardcore_assumed": true
      }
    ],
    "observations_count": 1
  },
  "delta_ist": -0.6524,
  "delta_pct": -5.6,
  "time_match_label": "same_week",
  "segment_match_label": "partial",
  "disagreement_reasons": [
    "Small sample size (1 Diablo2.io observation).",
    "Diablo2.io hardcore assumed softcore — may affect segment match.",
    "Traderie VWAP averages 611 trades; single observation variance expected."
  ],
  "notes": "Diablo2.io single observation (11 Ist) is within expected range of Traderie VWAP (11.65 Ist). Delta -5.6% is within normal variance for rune trades."
}
```

## 9. Output Schema

### File: `data/diagnostics/traderie_vs_diablo2io_rune_comparison.sample.json`

```json
{
  "schema_version": "0.1",
  "generated_at": "2026-06-20T12:00:00Z",
  "product": "diagnostic_rune_comparison",
  "game": "diablo2resurrected",
  "description": "Side-by-side diagnostic comparison of Traderie and Diablo2.io completed player trade prices. No blending, no canonical prices, purely diagnostic.",
  "disclaimer": "This is a diagnostic comparison only. Do not use for canonical pricing. Diablo2.io data is research-only (use_in_model=false). Traderie values are the primary pricing source.",
  "sources_compared": [
    {
      "source": "Traderie",
      "evidence_class": "completed_player_trades",
      "data_file": "data/products/in_game_rune_values.json",
      "time_window": "unknown_window"
    },
    {
      "source": "Diablo2.io",
      "evidence_class": "completed_player_trade_candidate",
      "data_file": "data/research/diablo2io_sold_jah_trades.sample.json",
      "research_only": true
    }
  ],
  "comparable_unit": {
    "primary": "pair_ratio",
    "secondary": "ist_equivalent",
    "ist_conversion_policy": "direct where possible; via_traderie_prices where not; unconvertible excluded"
  },
  "segment_comparison_policy": {
    "only_same_segment": true,
    "segment_match_labels": ["exact", "partial", "mismatch"],
    "hardcore_default_when_unknown": "softcore"
  },
  "time_comparison_policy": {
    "labels": ["same_day", "same_week", "unknown_window", "different_period"]
  },
  "comparisons": [
    {
      "rune": "Jah",
      "segment": "pc_sc_l",
      "comparable_unit": "ist_equivalent",
      "traderie": {
        "value_ist": 17.2533,
        "bid_price": 16.3884,
        "ask_price": 18.1181,
        "bid_count": 102,
        "ask_count": 118,
        "total_trades": 220,
        "confidence": "high"
      },
      "diablo2io": {
        "value_ist": null,
        "ist_conversion_method": null,
        "pair_ratios": null,
        "observations": [],
        "observations_total": 0,
        "clean_observations": 0,
        "excluded_observations": 0
      },
      "delta_ist": null,
      "delta_pct": null,
      "pair_ratio_comparison": null,
      "segment_match_label": "mismatch",
      "segment_note": "No Diablo2.io ladder Jah trades in sample. Only non-ladder rows available.",
      "time_match_label": "not_applicable",
      "disagreement_reasons": [
        "Segment mismatch — no overlap in this segment."
      ],
      "no_comparison_possible": true,
      "notes": ""
    },
    {
      "rune": "Jah",
      "segment": "pc_sc_nl",
      "comparable_unit": "ist_equivalent",
      "traderie": {
        "value_ist": 11.6524,
        "bid_price": 11.5438,
        "ask_price": 11.7611,
        "bid_count": 525,
        "ask_count": 86,
        "total_trades": 611,
        "confidence": "high"
      },
      "diablo2io": {
        "value_ist": 11.0,
        "ist_conversion_method": "direct",
        "pair_ratios": null,
        "observations": [
          {
            "parse_class": "clean_single_rune",
            "trade_side": "WTB",
            "payer_is_poster": true,
            "target_quantity": 1,
            "target_item": "Jah Rune",
            "consideration": [
              { "item": "Ist", "quantity": 11 }
            ],
            "sold_at_relative": "15 hours ago",
            "sold_timestamp": "Fri Jun 19, 2026 4:47 pm",
            "seller": "Ctaylorheck",
            "buyer": "varangium",
            "segment": {
              "platform": "pc",
              "ladder": "non_ladder",
              "hardcore": "unknown",
              "region": "americas"
            },
            "segment_match_type": "partial",
            "hardcore_assumed": true,
            "segment_confidence": "medium",
            "source_url": "https://diablo2.io/search.php?keywords=Jah&terms=all..."
          }
        ],
        "observations_total": 1,
        "clean_observations": 1,
        "excluded_observations": 0
      },
      "delta_ist": -0.6524,
      "delta_pct": -5.6,
      "pair_ratio_comparison": null,
      "segment_match_label": "partial",
      "segment_note": "Diablo2.io hardcore=unknown, assumed softcore. All other dimensions match pc_sc_nl.",
      "time_match_label": "same_week",
      "time_note": "Diablo2.io: 15 hours ago (Jun 19). Traderie: unknown window but likely recent.",
      "observations_note": "Single Diablo2.io observation — insufficient for statistical comparison.",
      "disagreement_reasons": [
        "Small sample size (1 Diablo2.io observation) vs 611 Traderie trades.",
        "Single observation variance expected within normal range.",
        "Diablo2.io hardcore dimension assumed (may affect segment if actual trade was HC)."
      ],
      "no_comparison_possible": false,
      "notes": "Delta -5.6% is within normal trade-to-trade variance. No evidence of systematic divergence."
    },
    {
      "rune": "Jah",
      "segment": "pc_sc_nl",
      "comparable_unit": "pair_ratio",
      "traderie": {
        "implied_jah_ber_ratio": 1.135,
        "calculation": "traderie Jah(11.6524) / traderie Ber(10.2695) pc_sc_nl"
      },
      "diablo2io": {
        "pair_ratios": {
          "jah_ber": 1.0,
          "source": "clean_multi_rune and quantity_bundle rows"
        },
        "observations": [
          {
            "parse_class": "quantity_bundle",
            "trade_side": "WTS",
            "raw": "2 Jah for 2 Ber",
            "normalized_ratio": "1 Jah : 1 Ber",
            "ratio_jah_ber": 1.0,
            "sold_at_relative": "2 days ago",
            "sold_timestamp": "Wed Jun 17, 2026 7:26 pm",
            "buyer": "LyonCZ"
          }
        ],
        "observations_total": 1,
        "clean_observations": 1
      },
      "delta_pct": -11.9,
      "pair_ratio_delta_pct": -11.9,
      "calculation_note": "Traderie implicit Jah:Ber = 11.65/10.27 = 1.135. Diablo2.io observed Jah:Ber = 1.0.",
      "segment_match_label": "partial",
      "time_match_label": "same_week",
      "disagreement_reasons": [
        "Single Diablo2.io observation — may not represent market.",
        "Bulk trade (2:2) may have different rate than single-unit trades.",
        "Time window mismatch possible (Traderie window unknown)."
      ],
      "no_comparison_possible": false,
      "notes": "Pair ratio comparison is the more independent diagnostic. Diablo2.io suggests Jah:Ber closer to 1:1, while Traderie implies 1.135:1. Both within historical normal range."
    }
  ],
  "segment_coverage_summary": {
    "segments_with_clean_diablo2io_data": ["pc_sc_nl"],
    "segments_with_traderie_data": ["pc_sc_l", "pc_sc_nl", "pc_hc_l", "pc_hc_nl"],
    "segments_with_overlap": ["pc_sc_nl"],
    "segments_without_overlap": ["pc_sc_l", "pc_hc_l", "pc_hc_nl"],
    "note": "Only pc_sc_nl has clean Diablo2.io rows in the sample. All other segments have zero Diablo2.io observations for comparison."
  },
  "caveats": [
    "This is a diagnostic comparison, not a pricing model.",
    "Do not blend, average, or interpolate between sources.",
    "Diablo2.io sample is limited (6 clean rows, 1 segment).",
    "Traderie time window is unknown — time-match labels are approximations.",
    "Pair ratio comparison uses Traderie's own Ist values for implicit ratios, which is not fully independent.",
    "Segment match for Diablo2.io is partial (hardcore assumed softcore)."
  ]
}
```

## 10. Implementation Notes (Do Not Execute)

### Pipeline steps (for future implementation)
1. Read `in_game_rune_values.json` → build Traderie lookup: `{segment + rune: {value_ist, bid, ask, counts}}`.
2. Read `diablo2io_sold_{rune}_trades.sample.json` → filter by eligible parse classes and gates.
3. Per Diablo2.io observation:
   a. Classify segment match against Traderie segments.
   b. Compute Ist-equivalent (if convertible).
   c. Compute pair ratio (if single non-Ist consideration or multi-rune).
   d. Assign time_match_label.
4. Group by (rune, segment, comparable_unit).
5. Build comparison objects: Traderie value, Diablo2.io value, delta, delta_pct, labels, notes.
6. Write `data/diagnostics/traderie_vs_diablo2io_rune_comparison.sample.json`.

### Edge cases to handle
- Diablo2.io row with multiple consideration items where some are not runes → exclude from comparison, flag as `unconvertible`.
- Diablo2.io row with segment that doesn't exist in Traderie data → `segment_match_label: "mismatch"`.
- Quantity bundle with heterogeneous consideration after normalization → still valid for pair ratio; may be invalid for Ist-equivalent if items are not all runes.
- Zero clean observations for a given segment → `no_comparison_possible: true`.
