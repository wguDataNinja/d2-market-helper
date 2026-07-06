- foundation_complete: true (2026-07-06 — migrations, validation, backup, restore, pilot loader done)
- pilot_loader: scripts/traderie_pilot_loader.py (dry-run/plan/apply/rollback/parity, 6 tests PASS)
- continuity_doc: docs/VPS_CONTINUITY.md
- evidence: ivy-control/vps/worker-control/reports/STRONG_AGENTIC_EXECUTION_REPORT.md
- current_goal: VPS migration preparation — backup/retention prep (TRD_BACKUP_RETENTION_PREP)
- active_task: Traderie real-data pilot readiness dry-run complete — no live ingest
- active_agent: Codex
- current_decision: Pilot blocked until real PG loader/adapter exists and explicit real-data Gate approval is recorded.
- pilot_candidate:
    command: python3 scripts/traderie_pilot_readiness_report.py --eligible-only --json
    segment: pc_sc_l
    selected_count: 25
    digest: df82ac34e7ccb16688963a1100d30bfc1eeeb8223d00b2243c75146e88bf794f
- validation:
    - python3 -m pytest tests/test_traderie_adapter.py — 40 passed
- next_action: Implement real PG loader/adapter with dry-run/plan/apply, reject report, rollback by segment_slug + observation_key, delete-and-reimport proof, and parity.
