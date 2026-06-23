# History vs Canonical Traderie Extraction — Reconciliation

Date: 2026-06-20

---

## 1. Exact Per-Segment Counts

| Segment | Canonical Raw Extracted | History Extracted | Canonical Modeled (Ist-pair VWAP) |
|---|---|---|---|
| pc_sc_l | 14,695 | 1,036 | 1,344 |
| pc_sc_nl | 13,462 | 952 | 1,095 |
| pc_hc_l | 2,366 | 451 | 126 |
| pc_hc_nl | 230 | 18 | 5 |
| **Total** | **30,753** | **2,457** | **2,570** |

## 2. The 2,570 vs 2,457 Interpretation

**The gap is that history extracted (2,457) < canonical modeled (2,570).**

This is significant: the history path extracts FEWER total trades (all types including AND) than the canonical path produces as Ist-pair modeled trades. This means some unique trades present in the canonical extraction are missing from the history extraction entirely.

The primary cause is **timing**: history JSONL collection started when `snapshot_traderie.py` was deployed. Before that, `fetch_completed_trades.py` accumulated raw data that never entered history. The canonical raw files contain data from as early as May 2026 (softcore) and March 2024 (hardcore), while history JSONL only captured data from the first snapshot run onward.

## 3. The "292 Modeled Trades" Number

The 292 number was produced by running `calculate_rune_prices.py --input-dir data/research`, which reads the history-derived CSVs and applies the Ist-pair VWAP filter. This filtered the 2,457 extracted trades down to 292 Ist-pair trades that pass the 0.5-50 Ist outlier filter and have both bid and ask sides.

This is NOT the total extracted trade count — it's the modeled VWAP count from a subset of available data. It's analogous to the canonical 2,570 but from the smaller history dataset.

## 4. Likely Causes of Differences

| Cause | Impact | Direction |
|---|---|---|
| History JSONL started late | All pre-snapshot data is in raw but not in history | History has fewer rows |
| Canonical raw has massive duplication | 30,753 raw vs 2,570 usable — ~92% duplication | Canonical raw count is misleading |
| Dedupe by listing_id in history | Aggressively dedupes across snapshot runs | History count is more correct |
| History JSONL dedupes by `_observation_key` from `snapshot_io` | Already deduped at append time; script's read-time dedupe is a second pass | History dedupe is reliable |
| Non-rune items in raw | Excluded by both extractors | No difference |
| `item_name` field in history vs `Runes` key in raw | Same semantic field but accessed differently | Should produce same data |

## 5. Recommendation

**Run dual outputs for one accumulation cycle, then switch to history-backed as canonical.**

The history path is architecturally superior:
- Deduped by `listing_id` at both append-time and read-time
- Append-only — no risk of data loss
- Timestamped snapshots enable trend analysis
- Gitignored — no accidental commits of runtime data

The canonical path has pre-history data that history will never match. But over time (2-4 weeks of 4x daily snapshots), the history dataset will accumulate sufficient data to replace the raw file path.

### Recommended Timeline

1. **Now:** Keep both paths running. Canonical for current products (data/raw/). History for accumulation.
2. **After 1 week:** Re-run comparison. If history has grown to >2,000 modeled trades, consider switching.
3. **After 1 month:** Switch to history-backed as the primary path. Deprecate the raw-file extractor.
4. **After 3 months:** Remove the old raw-file path.

### Action to Close Gap

To get pre-history data into history, run a one-time backfill:
```bash
# This does not exist yet — would read data/raw/ and append to history JSONL
# Script would be: scripts/backfill_traderie_raw_to_history.py
```
Not urgent. The scheduled pipeline will accumulate data naturally.

## 6. Comparison Output

`--compare-current` flag added to `build_traderie_dataset_from_history.py`. Run:
```bash
python scripts/build_traderie_dataset_from_history.py --write-research --compare-current
```
