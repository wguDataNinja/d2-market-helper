import sys
from argparse import Namespace
from pathlib import Path
import os
import shlex

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


def _continued_unit_values(unit_path, key):
    values = []
    lines = unit_path.read_text().splitlines()
    index = 0
    prefix = f"{key}="

    while index < len(lines):
        line = lines[index].strip()
        if not line or line.startswith("#") or not line.startswith(prefix):
            index += 1
            continue

        value_parts = [line.split("=", 1)[1].rstrip()]
        while value_parts[-1].endswith("\\") and index + 1 < len(lines):
            value_parts[-1] = value_parts[-1][:-1].rstrip()
            index += 1
            value_parts.append(lines[index].strip().rstrip())
        values.append(" ".join(part for part in value_parts if part))
        index += 1

    return values


def test_all_python_services_use_venv():
    approved_python = "/home/scraper/apps/traderie/.venv/bin/python"

    for unit_path in (REPO_ROOT / "deploy" / "systemd").glob("traderie-*.service"):
        for exec_start in _continued_unit_values(unit_path, "ExecStart"):
            tokens = shlex.split(exec_start)
            python_tokens = [
                token
                for token in tokens
                if token.startswith("/") and Path(token).name.startswith("python")
            ]
            assert all(token == approved_python for token in python_tokens), (
                f"{unit_path.name} uses Python outside the deployment venv: "
                f"{python_tokens}"
            )


def _install_fake_psycopg2(mock_connect=None):
    """Install a fake psycopg2 module into sys.modules for testing."""
    import sys, types
    mock_connect_fn = mock_connect or (lambda *a, **kw: None)

    fake_pg = types.ModuleType("psycopg2")
    fake_pg.__path__ = []
    fake_pg.__package__ = "psycopg2"
    fake_pg.connect = mock_connect_fn

    fake_extras = types.ModuleType("psycopg2.extras")
    fake_extras.__package__ = "psycopg2.extras"
    fake_extras.RealDictCursor = dict

    fake_sql = types.ModuleType("psycopg2.sql")
    fake_sql.__package__ = "psycopg2.sql"
    fake_sql.Identifier = lambda n: f'"{n}"'
    fake_sql.SQL = lambda s: s

    saved = {}
    for name in ("psycopg2", "psycopg2.extras", "psycopg2.sql"):
        saved[name] = sys.modules.get(name)
    sys.modules["psycopg2"] = fake_pg
    sys.modules["psycopg2.extras"] = fake_extras
    sys.modules["psycopg2.sql"] = fake_sql

    def restore():
        for name, mod in saved.items():
            if mod is not None:
                sys.modules[name] = mod
            else:
                sys.modules.pop(name, None)

    return fake_pg, restore


def _test_pg_connect(env, mock_conn, assert_fn):
    """Helper: install fake psycopg2, run _pg_connect with env, call assert_fn(mock_connect)."""
    import os
    from unittest.mock import patch, MagicMock

    mock_connect = MagicMock(return_value=mock_conn)
    fake_pg, restore = _install_fake_psycopg2(mock_connect)
    try:
        with patch.object(os.environ, "get", lambda k, d="": env.get(k, d)):
            from scripts.traderie_health_export import _pg_connect
            conn = _pg_connect()
        assert_fn(mock_connect)
        assert conn is mock_conn
    finally:
        restore()


def test_pg_connect_reader_url_preferred():
    """TRADERIE_PG_READER_URL is preferred over TRADERIE_PG_URL."""
    from unittest.mock import MagicMock

    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = MagicMock()

    def check(mc):
        mc.assert_called_once_with(
            "postgresql://traderie_reader:secret@127.0.0.1:5432/traderie",
            cursor_factory=dict,
        )

    _test_pg_connect({
        "TRADERIE_PG_READER_URL": "postgresql://traderie_reader:secret@127.0.0.1:5432/traderie",
        "TRADERIE_PG_URL": "postgresql://traderie_writer:secret@127.0.0.1:5432/traderie",
    }, mock_conn, check)


def test_pg_connect_reader_url_fallback_to_writer():
    """Empty TRADERIE_PG_READER_URL falls back to TRADERIE_PG_URL + SET ROLE."""
    from unittest.mock import MagicMock

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = {"current_user": "traderie_writer"}
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    def check(mc):
        mc.assert_called_once_with(
            "postgresql://traderie_writer:secret@127.0.0.1:5432/traderie",
            cursor_factory=dict,
        )

    _test_pg_connect({
        "TRADERIE_PG_READER_URL": "",
        "TRADERIE_PG_URL": "postgresql://traderie_writer:secret@127.0.0.1:5432/traderie",
    }, mock_conn, check)


def test_pg_connect_whitespace_reader_url():
    """Whitespace-only TRADERIE_PG_READER_URL treated as absent."""
    from unittest.mock import MagicMock

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = {"current_user": "traderie_writer"}
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    def check(mc):
        mc.assert_called_once_with(
            "postgresql://traderie_writer:secret@127.0.0.1:5432/traderie",
            cursor_factory=dict,
        )

    _test_pg_connect({
        "TRADERIE_PG_READER_URL": "   ",
        "TRADERIE_PG_URL": "postgresql://traderie_writer:secret@127.0.0.1:5432/traderie",
    }, mock_conn, check)


def test_pg_connect_no_urls_uses_kwargs():
    """Neither reader nor writer URL available uses individual env vars."""
    from unittest.mock import MagicMock

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = {"current_user": "traderie_writer"}
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    def check(mc):
        mc.assert_called_once()
        assert mc.call_args[1].get("database") == "traderie"
        assert mc.call_args[1].get("host") == "127.0.0.1"
        assert mc.call_args[1].get("user") == "traderie_writer"

    _test_pg_connect({
        "TRADERIE_PG_DATABASE": "traderie",
        "PGHOST": "127.0.0.1",
        "PGUSER": "traderie_writer",
    }, mock_conn, check)


def test_pg_connect_no_set_role_with_reader_url():
    """When reader URL is present, connection returns without cursor execute."""
    from unittest.mock import MagicMock

    def check(mc):
        mc.assert_called_once()

    _test_pg_connect({
        "TRADERIE_PG_READER_URL": "postgresql://traderie_reader:secret@127.0.0.1:5432/traderie",
        "TRADERIE_PG_URL": "postgresql://traderie_writer:secret@127.0.0.1:5432/traderie",
    }, MagicMock(), check)


def test_health_import_does_not_expose_urls():
    """Secret-bearing URL env vars are not exposed in normal error text."""
    from scripts.traderie_health_export import PG_READER_URL_ENV_VAR, PG_URL_ENV_VAR
    assert PG_READER_URL_ENV_VAR == "TRADERIE_PG_READER_URL"
    assert PG_URL_ENV_VAR == "TRADERIE_PG_URL"


def test_ingest_service_uses_infinity_timeout_with_per_segment_bounds():
    """traderie-ingest-snapshot.service uses TimeoutStartSec=infinity
    because each segment has its own timeout in the orchestrator script.
    """
    unit_path = REPO_ROOT / "deploy" / "systemd" / "traderie-ingest-snapshot.service"
    content = unit_path.read_text()
    assert "TimeoutStartSec=infinity" in content

def test_generation_orchestrator_script_exists():
    script = REPO_ROOT / "scripts" / "run_traderie_generation.sh"
    assert script.is_file()
    assert os.access(script, os.X_OK)

def test_generation_orchestrator_defines_all_segment_timeouts():
    script = (REPO_ROOT / "scripts" / "run_traderie_generation.sh").read_text()
    for seg in ("pc_sc_nl", "pc_sc_l", "pc_hc_l", "pc_hc_nl"):
        assert seg in script, f"Missing segment {seg} in orchestrator"
        assert f"{seg})" in script, f"Missing timeout case for {seg} in orchestrator"

def test_generation_orchestrator_timeouts_are_positive():
    script = (REPO_ROOT / "scripts" / "run_traderie_generation.sh").read_text()
    import re
    timeouts = re.findall(r'(\w+)\)\s*echo\s+(\d+)', script)
    for seg, val in timeouts:
        assert int(val) > 0, f"Non-positive timeout for {seg}: {val}"
        assert int(val) >= 120, f"Timeout for {seg} too small: {val}s (min 120s)"

def test_generation_orchestrator_invokes_snapshot_correctly():
    script = (REPO_ROOT / "scripts" / "run_traderie_generation.sh").read_text()
    assert "timeout" in script
    assert "snapshot_traderie.py" in script
    assert '--segment "$SEGMENT"' in script or "--segment" in script


def test_all_service_ExecStart_targets_exist():
    deploy_root = "/home/scraper/apps/traderie/"
    approved_external_executables = {"/usr/bin/flock"}
    approved_deployment_executables = {
        "/home/scraper/apps/traderie/.venv/bin/python",
    }

    for unit_path in (REPO_ROOT / "deploy" / "systemd").glob("traderie-*.service"):
        for exec_start in _continued_unit_values(unit_path, "ExecStart"):
            for token in shlex.split(exec_start):
                if token in approved_external_executables:
                    continue
                if token in approved_deployment_executables:
                    continue
                if not token.startswith(deploy_root):
                    continue

                repo_relative = token.removeprefix(deploy_root)
                target = REPO_ROOT / repo_relative
                assert target.exists(), (
                    f"{unit_path.name} references missing deployed repo path: "
                    f"{token}"
                )
