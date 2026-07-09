"""Tests for Traderie storage adapter, PG adapter, parity, and health export.

See TRD-007 assignment: adapter, parity, and observability package.
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.traderie_storage_adapter import FileTraderieAdapter, _observation_key
from scripts.traderie_pg_adapter import PgTraderieAdapter, ENABLED_ENV_VAR
from scripts.traderie_parity_report import ParityReport
from scripts.traderie_health_export import (
    redact_dict,
    transform_to_sanitized,
    build_default_fixture_input,
    PROHIBITED_FIELDS,
)
from tests.fixtures.parity_fixtures import (
    COMPLETED_TRADES,
    PRICE_ENTRIES,
    SEGMENTS,
    PRODUCT_BUILDS,
    HEALTH_EXPORT_INPUT,
    HEALTH_EXPORT_EXPECTED_SANITIZED,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
FIXTURE_JSONL = FIXTURE_DIR / "completed_trades.jsonl"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def file_adapter():
    return FileTraderieAdapter(data_root=FIXTURE_DIR)


@pytest.fixture
def file_adapter_real():
    return FileTraderieAdapter()


@pytest.fixture
def pg_adapter_disabled():
    return PgTraderieAdapter(enabled=False)


@pytest.fixture
def pg_adapter_enabled():
    adapter = PgTraderieAdapter(enabled=True)
    adapter._dry_store["segments"] = list(SEGMENTS)
    adapter._dry_store["completed_trades"] = [dict(t) for t in COMPLETED_TRADES]
    adapter._dry_store["price_entries"] = [dict(e) for e in PRICE_ENTRIES]
    adapter._dry_store["product_builds"] = [dict(b) for b in PRODUCT_BUILDS]
    return adapter


@pytest.fixture
def pg_adapter_enabled_with_file(file_adapter):
    adapter = PgTraderieAdapter(file_adapter=file_adapter, enabled=True)
    return adapter


# ---------------------------------------------------------------------------
# Test: File adapter methods with fixtures
# ---------------------------------------------------------------------------

class TestFileAdapter:
    def test_read_segments_from_fixture(self, file_adapter):
        segs = file_adapter.get_segments()
        assert len(segs) >= 4
        slugs = {s["segment_slug"] for s in segs}
        assert "pc_sc_l" in slugs
        assert "pc_sc_nl" in slugs
        assert "pc_hc_l" in slugs
        assert "pc_hc_nl" in slugs

    def test_read_completed_trades_from_jsonl(self, file_adapter):
        trades = file_adapter.get_completed_trades()
        assert len(trades) == 7
        keys = {_observation_key(t) for t in trades}
        assert "traderie/pc_sc_l::Ist Rune::2.5::2026-07-05T05:00:00Z::1001" in keys
        assert "traderie/pc_sc_l::Jah Rune::17.0::2026-07-05T05:00:00Z::1002" in keys

    def test_read_trades_by_segment(self, file_adapter):
        trades = file_adapter.get_completed_trades(segment_slug="pc_sc_l")
        assert all(t.get("segment_slug") == "pc_sc_l" or t.get("source_slug", "").endswith("pc_sc_l") for t in trades)
        assert len(trades) >= 3

    def test_read_trades_empty_segment(self, file_adapter):
        trades = file_adapter.get_completed_trades(segment_slug="pc_xbox_sc_nl")
        assert trades == []

    def test_get_price_entries(self, file_adapter):
        entries = file_adapter.get_price_entries()
        assert len(entries) >= 8

        entry_keys = {e["trade_observation_key"] for e in entries}
        assert "traderie/pc_sc_l::Ist Rune::2.5::2026-07-05T05:00:00Z::1001" in entry_keys

    def test_get_product_builds(self, file_adapter_real):
        builds = file_adapter_real.get_product_builds()
        assert isinstance(builds, list)

    def test_get_snapshot_runs(self, file_adapter_real):
        runs = file_adapter_real.get_snapshot_runs()
        assert isinstance(runs, list)

    def test_segment_display_names(self, file_adapter):
        segs = file_adapter.get_segments()
        by_slug = {s["segment_slug"]: s for s in segs}
        assert by_slug["pc_sc_l"]["display_name"] == "PC Softcore Ladder"
        assert by_slug["pc_hc_nl"]["display_name"] == "PC Hardcore Non-Ladder"


# ---------------------------------------------------------------------------
# Test: PG adapter disabled (raises RuntimeError)
# ---------------------------------------------------------------------------

class TestPgAdapterDisabled:
    def test_get_segments_raises(self, pg_adapter_disabled):
        with pytest.raises(RuntimeError, match="not enabled"):
            pg_adapter_disabled.get_segments()

    def test_get_completed_trades_raises(self, pg_adapter_disabled):
        with pytest.raises(RuntimeError, match="not enabled"):
            pg_adapter_disabled.get_completed_trades()

    def test_get_price_entries_raises(self, pg_adapter_disabled):
        with pytest.raises(RuntimeError, match="not enabled"):
            pg_adapter_disabled.get_price_entries()

    def test_get_product_builds_raises(self, pg_adapter_disabled):
        with pytest.raises(RuntimeError, match="not enabled"):
            pg_adapter_disabled.get_product_builds()

    def test_get_snapshot_runs_raises(self, pg_adapter_disabled):
        with pytest.raises(RuntimeError, match="not enabled"):
            pg_adapter_disabled.get_snapshot_runs()

    def test_upsert_raises(self, pg_adapter_disabled):
        with pytest.raises(RuntimeError, match="not enabled"):
            pg_adapter_disabled.upsert_completed_trade({})


# ---------------------------------------------------------------------------
# Test: PG adapter enabled path (dry only, no real PG)
# ---------------------------------------------------------------------------

class TestPgAdapterEnabled:
    def test_get_segments_from_dry_store(self, pg_adapter_enabled):
        segs = pg_adapter_enabled.get_segments()
        assert len(segs) == 4
        slugs = {s["segment_slug"] for s in segs}
        assert slugs == {"pc_sc_l", "pc_sc_nl", "pc_hc_l", "pc_hc_nl"}

    def test_get_completed_trades_from_dry_store(self, pg_adapter_enabled):
        trades = pg_adapter_enabled.get_completed_trades()
        assert len(trades) == 7

    def test_get_completed_trades_filtered(self, pg_adapter_enabled):
        trades = pg_adapter_enabled.get_completed_trades(segment_slug="pc_sc_l")
        assert len(trades) == 3
        assert all(t["segment_slug"] == "pc_sc_l" for t in trades)

    def test_get_price_entries_from_dry_store(self, pg_adapter_enabled):
        entries = pg_adapter_enabled.get_price_entries()
        assert len(entries) == 8

    def test_get_product_builds_from_dry_store(self, pg_adapter_enabled):
        builds = pg_adapter_enabled.get_product_builds()
        assert len(builds) == 4

    def test_upsert_inserts_new(self, pg_adapter_enabled):
        trade = {
            "observation_key": "test::new_trade::1",
            "segment_slug": "pc_sc_l",
            "item_name": "Test Rune",
            "item_id": 999999,
        }
        result = pg_adapter_enabled.upsert_completed_trade(trade)
        assert result["observation_key"] == "test::new_trade::1"
        trades = pg_adapter_enabled.get_completed_trades()
        assert len(trades) == 8

    def test_upsert_updates_existing(self, pg_adapter_enabled):
        key = "traderie/pc_sc_l::Ist Rune::2.5::2026-07-05T05:00:00Z::1001"
        trade = {
            "observation_key": key,
            "segment_slug": "pc_sc_l",
            "item_name": "Ist Rune (updated)",
            "item_id": 2290642411,
        }
        pg_adapter_enabled.upsert_completed_trade(trade)
        trades = pg_adapter_enabled.get_completed_trades()
        assert len(trades) == 7
        match = [t for t in trades if t["observation_key"] == key]
        assert len(match) == 1
        assert match[0]["item_name"] == "Ist Rune (updated)"

    def test_upsert_missing_key_raises(self, pg_adapter_enabled):
        with pytest.raises(ValueError, match="observation_key"):
            pg_adapter_enabled.upsert_completed_trade({"item_name": "No Key"})


# ---------------------------------------------------------------------------
# Test: PG adapter file-backed fallback
# ---------------------------------------------------------------------------

class TestPgAdapterFallback:
    def test_fallback_on_pg_exception(self, pg_adapter_enabled_with_file, file_adapter):
        original = pg_adapter_enabled_with_file._try_pg_or_dry
        def failing(*args, **kwargs):
            raise RuntimeError("PG connection failed")
        pg_adapter_enabled_with_file._try_pg_or_dry = failing
        trades = pg_adapter_enabled_with_file.get_completed_trades()
        file_trades = file_adapter.get_completed_trades()
        assert len(trades) == len(file_trades)

    def test_fallback_segments_on_pg_exception(self, pg_adapter_enabled_with_file):
        original = pg_adapter_enabled_with_file._try_pg_or_dry
        def failing(*args, **kwargs):
            raise RuntimeError("PG connection failed")
        pg_adapter_enabled_with_file._try_pg_or_dry = failing
        segs = pg_adapter_enabled_with_file.get_segments()
        assert len(segs) >= 4

    def test_enabled_empty_store_returns_empty(self, pg_adapter_enabled_with_file):
        pg_adapter_enabled_with_file._dry_store["completed_trades"] = []
        trades = pg_adapter_enabled_with_file.get_completed_trades()
        assert trades == []

    def test_explicit_pg_url_refuses_file_fallback(self, file_adapter):
        adapter = PgTraderieAdapter(file_adapter=file_adapter, enabled=True, pg_url="postgresql://localhost/traderie")
        def failing(*args, **kwargs):
            raise RuntimeError("PG connection failed")
        adapter._fetch_all = failing
        with pytest.raises(RuntimeError, match="refusing file fallback"):
            adapter.get_segments()

    def test_snapshot_runs_real_pg_query_matches_schema(self):
        adapter = PgTraderieAdapter(enabled=True, pg_url="postgresql://localhost/traderie")
        captured = {}
        def fake_fetch_all(sql, params=()):
            captured["sql"] = sql
            captured["params"] = params
            return []
        adapter._fetch_all = fake_fetch_all

        assert adapter.get_snapshot_runs("pc_sc_l") == []
        sql = captured["sql"]
        assert "snapshot_run_id" in sql
        assert "item_count" in sql
        assert "listing_count" in sql
        assert "error_count" in sql
        assert "duration_seconds" in sql
        assert "source_artifact_path" not in sql
        assert "records_fetched" not in sql
        assert captured["params"] == ("pc_sc_l",)


# ---------------------------------------------------------------------------
# Test: Parity comparison with known fixture data
# ---------------------------------------------------------------------------

class TestParity:
    def test_parity_identical_data(self, file_adapter, pg_adapter_enabled):
        reporter = ParityReport(file_adapter, pg_adapter_enabled)
        report = reporter.compare_trades()
        assert report["status"] == "completed"
        assert report["match"] is True
        assert report["file_count"] == report["pg_count"]

    def test_parity_filtered_segment(self, file_adapter, pg_adapter_enabled):
        reporter = ParityReport(file_adapter, pg_adapter_enabled)
        report = reporter.compare_trades(segment_slug="pc_sc_l")
        assert report["status"] == "completed"
        assert report["match"] is True

    def test_parity_detects_mismatch(self, file_adapter, pg_adapter_enabled):
        key = "traderie/pc_sc_l::Ist Rune::2.5::2026-07-05T05:00:00Z::1001"
        pg_adapter_enabled._dry_store["completed_trades"][0] = {
            "observation_key": key,
            "segment_slug": "pc_sc_l",
            "item_name": "Wrong Rune",
            "item_id": 999,
        }
        reporter = ParityReport(file_adapter, pg_adapter_enabled)
        report = reporter.compare_trades()
        assert report["match"] is False
        assert len(report["mismatches"]) >= 1

    def test_parity_skipped_when_pg_disabled(self, file_adapter, pg_adapter_disabled):
        reporter = ParityReport(file_adapter, pg_adapter_disabled)
        report = reporter.compare_trades()
        assert report["status"] == "skipped"


# ---------------------------------------------------------------------------
# Test: Health export redaction
# ---------------------------------------------------------------------------

class TestHealthExportRedaction:
    def test_prohibited_fields_removed(self):
        data = {
            "status": "ok",
            "error_message_private": "this should be removed",
            "api_key": "sk-secret123",
            "normal_field": "keep me",
        }
        redacted = redact_dict(data)
        assert "error_message_private" not in redacted
        assert "api_key" not in redacted
        assert redacted["status"] == "ok"
        assert redacted["normal_field"] == "keep me"

    def test_path_redaction(self):
        data = {"path": "/home/scraper/traderie/data/history"}
        redacted = redact_dict(data)
        assert "<redacted>" in redacted["path"]

    def test_ip_redaction(self):
        data = {"host": "Server at 192.168.1.1 is down"}
        redacted = redact_dict(data)
        assert "<ip-redacted>" in redacted["host"]

    def test_nested_dict_redaction(self):
        data = {"details": {"ip": "10.0.0.1", "path": "/Users/buddy/data"}}
        redacted = redact_dict(data)
        assert "<ip-redacted>" in redacted["details"]["ip"]
        assert "<redacted>" in redacted["details"]["path"]

    def test_transform_sanitized(self):
        private = HEALTH_EXPORT_INPUT
        sanitized = transform_to_sanitized(private)
        assert sanitized["project"] == "traderie"
        assert sanitized["workflow"] == "snapshot"
        assert sanitized["status"] == "ok"
        assert sanitized["contract_version"] == 2
        assert sanitized["workflow_id"] == "traderie/snapshot"
        assert sanitized["schema_version"] == 9
        assert sanitized["migration_version"] == "20260705_009_create_health_schema"
        assert sanitized["error_message_private"] is not None  # included in private sanitized output

    def test_redaction_chain(self):
        private = build_default_fixture_input()
        sanitized = transform_to_sanitized(private)
        # Operator-only fields are present in private sanitized output
        assert "error_message_private" in sanitized
        # Other prohibited fields (non-operator) should not be present
        other_prohibited = PROHIBITED_FIELDS - {"error_message_private"}
        for field in other_prohibited:
            assert field not in sanitized, f"Field {field} should not be in sanitized output"
        redacted = redact_dict(sanitized)
        for field in PROHIBITED_FIELDS:
            assert field not in redacted

    def test_redaction_direct_on_strings(self):
        data = {"description": "/home/scraper/traderie/data error at host 192.168.1.1"}
        redacted = redact_dict(data)
        assert "<redacted>" in redacted["description"]
        assert "<ip-redacted>" in redacted["description"]

    def test_error_class_and_code_separate(self):
        data = dict(HEALTH_EXPORT_INPUT)
        data["error_class"] = "TimeoutError"
        data["error_code"] = "E_TIMEOUT"
        sanitized = transform_to_sanitized(data)
        assert sanitized["error_class"] == "TimeoutError"
        assert sanitized["error_code"] == "E_TIMEOUT"

    def test_incident_state(self):
        data = dict(HEALTH_EXPORT_INPUT)
        data["incident_state"] = "active"
        sanitized = transform_to_sanitized(data)
        assert sanitized["incident_state"] == "active"


# ---------------------------------------------------------------------------
# Test: Idempotent upsert (observation_key uniqueness)
# ---------------------------------------------------------------------------

class TestIdempotentUpsert:
    def test_file_adapter_upsert_dedup(self, file_adapter):
        key = "test::dedup_key::1"
        trade1 = {"_observation_key": key, "item_name": "First", "segment_slug": "pc_sc_l"}
        trade2 = {"_observation_key": key, "item_name": "Second", "segment_slug": "pc_sc_l"}
        file_adapter.upsert_completed_trade(trade1)
        file_adapter.upsert_completed_trade(trade2)
        trades = file_adapter.get_completed_trades()
        keys = [_observation_key(t) for t in trades]
        assert keys.count(key) == 1

    def test_pg_adapter_upsert_dedup(self, pg_adapter_enabled):
        key = "test::dedup_key::2"
        trade1 = {"observation_key": key, "item_name": "First", "segment_slug": "pc_sc_l"}
        trade2 = {"observation_key": key, "item_name": "Second", "segment_slug": "pc_sc_l"}
        pg_adapter_enabled.upsert_completed_trade(trade1)
        pg_adapter_enabled.upsert_completed_trade(trade2)
        trades = pg_adapter_enabled.get_completed_trades()
        matching = [t for t in trades if t.get("observation_key") == key]
        assert len(matching) == 1
        assert matching[0]["item_name"] == "Second"
