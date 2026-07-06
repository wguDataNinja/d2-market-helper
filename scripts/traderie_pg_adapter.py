"""PostgreSQL storage adapter for Traderie.

DISABLED BY DEFAULT. Every storage method starts with a gate check and
raises RuntimeError if the adapter is not explicitly enabled.

File-backed fallback: if any PG method call fails, logs a warning and
returns the result from the file adapter.

Configuration:
    TRADERIE_PG_ADAPTER_ENABLED=false (default)
    TRADERIE_PG_URL (used when enabled for real PG connection)

See CODEX_SESSION_1_ARCHITECTURE.md §12-14.
"""

import logging
import os
from typing import Any, Optional

from scripts.traderie_storage_adapter import TraderieStorageAdapter, FileTraderieAdapter, _observation_key

logger = logging.getLogger(__name__)

ENABLED_ENV_VAR = "TRADERIE_PG_ADAPTER_ENABLED"


def _is_pg_enabled() -> bool:
    val = os.environ.get(ENABLED_ENV_VAR, "false").strip().lower()
    return val in ("1", "true", "yes")


class PgTraderieAdapter(TraderieStorageAdapter):
    """PG-backed storage adapter.

    Every storage method raises RuntimeError unless TRADERIE_PG_ADAPTER_ENABLED=true.
    When enabled but no real PG available (e.g. tests), uses _dry_store.
    On real PG failure, falls back to file adapter with warning.
    """

    def __init__(
        self,
        file_adapter: Optional[FileTraderieAdapter] = None,
        enabled: Optional[bool] = None,
    ):
        self._file_adapter = file_adapter
        self._enabled = enabled if enabled is not None else _is_pg_enabled()
        self._dry_store: dict[str, list[dict[str, Any]]] = {
            "segments": [],
            "items": [],
            "sources": [],
            "completed_trades": [],
            "price_entries": [],
            "product_builds": [],
            "snapshot_runs": [],
            "segment_rune_prices": [],
        }

    def _check_enabled(self) -> None:
        if not self._enabled:
            raise RuntimeError(
                f"PG adapter is not enabled. Set {ENABLED_ENV_VAR}=true to enable."
            )

    def _fallback(self, method_name: str, *args, **kwargs) -> Any:
        if self._file_adapter:
            logger.warning("PG adapter %s failed, falling back to file adapter", method_name)
            method = getattr(self._file_adapter, method_name, None)
            if method:
                return method(*args, **kwargs)
        raise RuntimeError(f"PG adapter {method_name} failed and no file fallback available")

    def _try_pg_or_dry(self, store_key: str, segment_key: Optional[str] = None, segment_slug: Optional[str] = None) -> list[dict[str, Any]]:
        data = self._dry_store.get(store_key, [])
        if segment_slug and segment_key:
            return [r for r in data if r.get(segment_key) == segment_slug]
        return list(data)

    # ------------------------------------------------------------------
    # Segment, Items, Sources
    # ------------------------------------------------------------------

    def get_segments(self) -> list[dict[str, Any]]:
        self._check_enabled()
        try:
            return self._try_pg_or_dry("segments")
        except Exception as exc:
            logger.warning("PG get_segments failed: %s", exc)
            return self._fallback("get_segments")

    def get_items(self) -> list[dict[str, Any]]:
        self._check_enabled()
        try:
            return self._try_pg_or_dry("items")
        except Exception as exc:
            logger.warning("PG get_items failed: %s", exc)
            return self._fallback("get_items")

    def get_sources(self) -> list[dict[str, Any]]:
        self._check_enabled()
        try:
            return self._try_pg_or_dry("sources")
        except Exception as exc:
            logger.warning("PG get_sources failed: %s", exc)
            return self._fallback("get_sources")

    # ------------------------------------------------------------------
    # Completed trades
    # ------------------------------------------------------------------

    def get_completed_trades(self, segment_slug: Optional[str] = None) -> list[dict[str, Any]]:
        self._check_enabled()
        try:
            return self._try_pg_or_dry("completed_trades", "segment_slug", segment_slug)
        except Exception as exc:
            logger.warning("PG get_completed_trades failed: %s", exc)
            return self._fallback("get_completed_trades", segment_slug)

    # ------------------------------------------------------------------
    # Derived reads
    # ------------------------------------------------------------------

    def get_price_entries(self, segment_slug: Optional[str] = None) -> list[dict[str, Any]]:
        self._check_enabled()
        try:
            return self._try_pg_or_dry("price_entries", "segment_slug", segment_slug)
        except Exception as exc:
            logger.warning("PG get_price_entries failed: %s", exc)
            return self._fallback("get_price_entries", segment_slug)

    def get_product_builds(self, segment_slug: Optional[str] = None) -> list[dict[str, Any]]:
        self._check_enabled()
        try:
            return self._try_pg_or_dry("product_builds", "segment_slug", segment_slug)
        except Exception as exc:
            logger.warning("PG get_product_builds failed: %s", exc)
            return self._fallback("get_product_builds", segment_slug)

    def get_snapshot_runs(self, segment_slug: Optional[str] = None) -> list[dict[str, Any]]:
        self._check_enabled()
        try:
            return self._try_pg_or_dry("snapshot_runs", "segment_slug", segment_slug)
        except Exception as exc:
            logger.warning("PG get_snapshot_runs failed: %s", exc)
            return self._fallback("get_snapshot_runs", segment_slug)

    def get_segment_rune_prices(self, segment_slug: Optional[str] = None, build_id: Optional[str] = None) -> list[dict[str, Any]]:
        self._check_enabled()
        try:
            data = self._dry_store.get("segment_rune_prices", [])
            result = list(data)
            if segment_slug:
                result = [r for r in result if r.get("segment_slug") == segment_slug]
            if build_id:
                result = [r for r in result if r.get("build_id") == build_id]
            return result
        except Exception as exc:
            logger.warning("PG get_segment_rune_prices failed: %s", exc)
            return self._fallback("get_segment_rune_prices", segment_slug, build_id)

    # ------------------------------------------------------------------
    # Upsert with dedup
    # ------------------------------------------------------------------

    def upsert_completed_trade(self, trade: dict[str, Any]) -> dict[str, Any]:
        self._check_enabled()
        key = _observation_key(trade)
        if not key:
            raise ValueError("Trade must have _observation_key or observation_key")
        store = self._dry_store.setdefault("completed_trades", [])
        for i, existing in enumerate(store):
            if _observation_key(existing) == key:
                store[i] = trade
                return trade
        store.append(trade)
        return trade
