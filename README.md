# D2R Market Helper

Public market-data tooling for Diablo II: Resurrected Traderie completed-trade analysis.

## Scope

- Tracks in-game rune value evidence by economy segment.
- Keeps PC softcore/hardcore and ladder/non-ladder segments separate.
- Stores local PostgreSQL schema, migrations, validation SQL, and lifecycle scripts.
- Produces JSON products for downstream tools from completed player-trade evidence.

Cash-market captures are handled only as separate external reference data. They are not blended into in-game rune value calculations.

## Current State

Phase A prepares the repository for public GitHub publication and proves the local Mac PostgreSQL database as the current authority. VPS deployment is intentionally separate and gated.

Local PostgreSQL migrations currently define:

- `app` tables for sources, segments, completed trades, price entries, collection metrics, aggregates, and prune audit.
- `archive` tables for retention audit archives.
- `health` tables for sanitized operational health exports.

## Validation

Run the Python test suite:

```bash
python3 -m pytest tests/ -v
```

Validate the PostgreSQL schema against the local `traderie` database:

```bash
psql -d traderie -f db/validation/999_full_validation.sql
```

Generate a sanitized PostgreSQL health export:

```bash
python3 scripts/traderie_health_export.py --pg --output /tmp/traderie.health.json
```

The health export writes one bounded `health.health_runs` record when `--pg` is used. Validation workflows should remove their test health row after proof capture.

## Deployment

Deployment templates live in `deploy/`. They are inert until the scheduler and VPS gates are approved. Do not install timers or mutate VPS services from this repository without explicit approval.

## License

No license is granted at this time.
