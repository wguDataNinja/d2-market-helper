import sys
from argparse import Namespace
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REPO_ROOT = Path(__file__).resolve().parent.parent

from scripts.traderie_collection_metrics import build_metrics
from scripts.traderie_health_export import _migration_version_number, transform_to_sanitized
from scripts.traderie_prune import _where


def test_collection_metrics_duplicate_ratio_from_payload():
    args = Namespace(
        workflow=None,
        source_id=None,
        source_slug=None,
        segment=None,
        trigger_type=None,
        started_at="2026-07-06T10:00:00Z",
        completed_at="2026-07-06T10:00:03Z",
        elapsed_ms=None,
        requests_made=None,
        response_bytes=None,
        records_returned=None,
        records_new=None,
        records_skipped_duplicate=None,
        retries=None,
        failures=None,
        stop_reason=None,
        collector_version=None,
    )
    metrics = build_metrics(
        args,
        {
            "records_returned": 100,
            "records_new": 25,
            "requests_made": 4,
            "response_bytes": 2048,
        },
    )

    assert metrics["records_skipped_duplicate"] == 75
    assert metrics["duplicate_ratio"] == 0.75
    assert metrics["requests_made"] == 4
    assert metrics["response_bytes"] == 2048


def test_collection_metrics_cli_args_override_payload():
    args = Namespace(
        workflow="pilot",
        source_id="traderie",
        source_slug="traderie",
        segment="pc_sc_l",
        trigger_type="pilot",
        started_at="2026-07-06T10:00:00Z",
        completed_at=None,
        elapsed_ms=1,
        requests_made=2,
        response_bytes=3,
        records_returned=4,
        records_new=1,
        records_skipped_duplicate=3,
        retries=0,
        failures=0,
        stop_reason="completed",
        collector_version="test",
    )
    metrics = build_metrics(args, {"records_returned": 999, "records_new": 999})

    assert metrics["workflow"] == "pilot"
    assert metrics["segment_slug"] == "pc_sc_l"
    assert metrics["records_returned"] == 4
    assert metrics["duplicate_ratio"] == 0.75


def test_prune_where_key_limited_ignores_age_window():
    args = Namespace(segment="pc_sc_l", retention_days=7)
    where_sql, params = _where(args, ["obs-1"])

    assert "ct.segment_slug = %(segment)s" in where_sql
    assert "ct.observation_key = ANY(%(keys)s)" in where_sql
    assert "captured_at <" not in where_sql
    assert params["keys"] == ["obs-1"]


def test_prune_where_retention_window_without_keys():
    args = Namespace(segment=None, retention_days=7)
    where_sql, params = _where(args, [])

    assert "ct.captured_at < now()" in where_sql
    assert params["keys"] is None
    assert params["retention_days"] == 7


def test_health_transform_keeps_retention_fields():
    sanitized = transform_to_sanitized(
        {
            "project": "traderie",
            "workflow": "postgres_health",
            "status": "ok",
            "retention_health": {"completed_trades_eligible_7d": 0},
            "latest_collection_metrics": {"records_returned": 25},
            "latest_prune_audit": {"action": "pruned"},
            "row_counts": {"completed_trades": 25},
            "database_size_bytes": 1234,
        }
    )

    assert sanitized["metadata"]["retention_health"]["completed_trades_eligible_7d"] == 0
    assert sanitized["metadata"]["latest_collection_metrics"]["records_returned"] == 25
    assert sanitized["metadata"]["latest_prune_audit"]["action"] == "pruned"
    assert sanitized["metadata"]["row_counts"]["completed_trades"] == 25
    assert sanitized["database_size_bytes"] == 1234


def test_health_migration_version_number_from_migration_name():
    assert _migration_version_number("20260706_017_grant_reader_health_select") == 17
    assert _migration_version_number("17") == 17
    assert _migration_version_number(None) is None


def test_vps_wrapper_scripts_exist_and_are_executable():
    for script_name in (
        "run_traderie_snapshot.sh",
        "run_traderie_backup.sh",
        "run_traderie_validate.sh",
    ):
        path = REPO_ROOT / "scripts" / script_name
        assert path.exists()
        assert os.access(path, os.X_OK)


def test_snapshot_timer_uses_four_daily_runs():
    timer = (REPO_ROOT / "deploy" / "systemd" / "traderie-ingest-snapshot.timer").read_text()

    assert "OnCalendar=*:0/15" not in timer
    assert "OnCalendar=00:00:00" in timer
    assert "OnCalendar=06:00:00" in timer
    assert "OnCalendar=12:00:00" in timer
    assert "OnCalendar=18:00:00" in timer
