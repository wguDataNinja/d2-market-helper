"""Tests for Traderie pilot loader — no real PG or external services."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.traderie_pilot_loader import TARGET_TABLES, select_segment_records, selected_pg_counts


def test_target_tables_defined():
    assert len(TARGET_TABLES) == 2
    assert "app.completed_trades" in TARGET_TABLES
    assert "app.price_entries" in TARGET_TABLES


def test_select_records_default_segment():
    records = select_segment_records("pc_sc_l", 5, eligible_only=True)
    assert len(records) <= 5
    if records:
        assert "listing_id" in records[0]


def test_select_records_no_eligible():
    """eligible_only=False should return records even if they'd be rejected."""
    records = select_segment_records("pc_sc_l", 5, eligible_only=False)
    assert len(records) <= 5


def test_dry_run_no_mutation():
    """Verify --dry-run runs without connecting to PG."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "scripts/traderie_pilot_loader.py", "--dry-run", "--limit", "3", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["mode"] == "dry-run"
    assert report["project"] == "traderie"
    assert report["selected_count"] >= 0


def test_plan_mode():
    import subprocess
    result = subprocess.run(
        [sys.executable, "scripts/traderie_pilot_loader.py", "--plan", "--limit", "3", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["mode"] == "dry-run"


def test_stable_digest_import():
    from scripts.traderie_pilot_readiness_report import stable_digest
    assert stable_digest([{"a": 1}]) == stable_digest([{"a": 1}])
    assert stable_digest([{"a": 1}]) != stable_digest([{"a": 2}])


def test_selected_pg_counts_uses_selected_observation_keys():
    class FakeCursor:
        def __init__(self):
            self.calls = []
            self.results = [(2,), (3,)]

        def execute(self, sql, params):
            self.calls.append((sql, params))

        def fetchone(self):
            return self.results.pop(0)

    class FakeConn:
        def __init__(self):
            self.cursor_obj = FakeCursor()
            self.commits = 0

        def cursor(self):
            return self.cursor_obj

        def commit(self):
            self.commits += 1

    conn = FakeConn()
    keys = ["obs-1", "obs-2"]
    counts = selected_pg_counts(conn, keys, "pc_sc_l")

    assert counts == {"app.completed_trades": 2, "app.price_entries": 3}
    assert conn.commits == 1
    assert conn.cursor_obj.calls[0][1] == ("pc_sc_l", keys)
    assert conn.cursor_obj.calls[1][1] == ("pc_sc_l", keys)
