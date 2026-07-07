"""PostgreSQL storage adapter for Traderie.

Disabled by default. When enabled without TRADERIE_PG_URL, the adapter keeps
the historical in-memory dry store used by tests. When TRADERIE_PG_URL is set,
methods use PostgreSQL and failures are raised instead of silently falling back
to files.
"""

import hashlib
import json
import logging
import os
from typing import Any, Optional

from scripts.traderie_storage_adapter import TraderieStorageAdapter, FileTraderieAdapter, _observation_key

logger = logging.getLogger(__name__)

ENABLED_ENV_VAR = "TRADERIE_PG_ADAPTER_ENABLED"
PG_URL_ENV_VAR = "TRADERIE_PG_URL"


def _is_pg_enabled() -> bool:
    val = os.environ.get(ENABLED_ENV_VAR, "false").strip().lower()
    return val in ("1", "true", "yes")


class PgTraderieAdapter(TraderieStorageAdapter):
    """PG-backed storage adapter.

    Every storage method raises RuntimeError unless TRADERIE_PG_ADAPTER_ENABLED=true.
    When enabled without TRADERIE_PG_URL, uses _dry_store.
    When TRADERIE_PG_URL is set, PG failures are raised without file fallback.
    """

    def __init__(
        self,
        file_adapter: Optional[FileTraderieAdapter] = None,
        enabled: Optional[bool] = None,
        pg_url: Optional[str] = None,
    ):
        self._file_adapter = file_adapter
        self._enabled = enabled if enabled is not None else _is_pg_enabled()
        self._pg_url = pg_url if pg_url is not None else os.environ.get(PG_URL_ENV_VAR, "").strip()
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

    def _has_real_pg(self) -> bool:
        return bool(self._pg_url)

    def _connect(self):
        if not self._has_real_pg():
            raise RuntimeError(f"{PG_URL_ENV_VAR} is not configured")
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(self._pg_url, cursor_factory=RealDictCursor)
        conn.autocommit = False
        return conn

    def _fallback(self, method_name: str, *args, **kwargs) -> Any:
        if self._has_real_pg():
            raise RuntimeError(
                f"PG adapter {method_name} failed with explicit {PG_URL_ENV_VAR}; refusing file fallback"
            )
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

    def _fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
            conn.commit()
        return [dict(row) for row in rows]

    @staticmethod
    def _int_or_none(value: Any) -> Optional[int]:
        if value in (None, ""):
            return None
        return int(value)

    @staticmethod
    def _content_hash(trade: dict[str, Any]) -> str:
        existing = trade.get("content_hash") or trade.get("_content_hash")
        if existing:
            return str(existing)
        payload = json.dumps(trade, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _price_entries(trade: dict[str, Any]) -> list[dict[str, Any]]:
        price = trade.get("price", [])
        if not isinstance(price, list):
            return []
        entries = []
        for group_number, entry in enumerate(price):
            if not isinstance(entry, dict):
                continue
            item_name = entry.get("name") or entry.get("item_name")
            if not item_name:
                continue
            requested_item_id = PgTraderieAdapter._int_or_none(entry.get("item_id"))
            entries.append({
                "requested_item_id": requested_item_id,
                "item_name": item_name,
                "quantity": PgTraderieAdapter._int_or_none(entry.get("quantity")) or 1,
                "add_flag": bool(entry.get("add", entry.get("add_flag", False))),
                "group_number": group_number,
                "rune_item_id": requested_item_id,
            })
        return entries

    # ------------------------------------------------------------------
    # Segment, Items, Sources
    # ------------------------------------------------------------------

    def get_segments(self) -> list[dict[str, Any]]:
        self._check_enabled()
        try:
            if self._has_real_pg():
                return self._fetch_all(
                    "SELECT segment_slug, display_name, platform, mode, ladder, hardcore, enabled, description, created_at "
                    "FROM app.segments ORDER BY segment_slug"
                )
            return self._try_pg_or_dry("segments")
        except Exception as exc:
            logger.warning("PG get_segments failed: %s", exc)
            return self._fallback("get_segments")

    def get_items(self) -> list[dict[str, Any]]:
        self._check_enabled()
        try:
            if self._has_real_pg():
                return self._fetch_all(
                    "SELECT item_id, name, category, short_name, tier, created_at FROM app.items ORDER BY name"
                )
            return self._try_pg_or_dry("items")
        except Exception as exc:
            logger.warning("PG get_items failed: %s", exc)
            return self._fallback("get_items")

    def get_sources(self) -> list[dict[str, Any]]:
        self._check_enabled()
        try:
            if self._has_real_pg():
                return self._fetch_all(
                    "SELECT source_id, name, source_type, category, priority, status, base_url, enabled, metadata, created_at, updated_at "
                    "FROM app.sources ORDER BY source_id"
                )
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
            if self._has_real_pg():
                sql = (
                    "SELECT trade_observation_id, segment_slug, observation_key, listing_id, content_hash, item_id, item_name, "
                    "quantity, seller, seller_rating, seller_reviews, seller_score, seller_status, updated_at, captured_at, "
                    "active, completed, platform, mode, hardcore, ladder, game_version, ruleset, has_and_prices, "
                    "price_group_count, price_entry_count, source_payload, snapshot_run_id, ingested_at "
                    "FROM app.completed_trades"
                )
                params: tuple[Any, ...] = ()
                if segment_slug:
                    sql += " WHERE segment_slug = %s"
                    params = (segment_slug,)
                sql += " ORDER BY captured_at, listing_id, observation_key"
                return self._fetch_all(sql, params)
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
            if self._has_real_pg():
                sql = (
                    "SELECT pe.price_entry_id, pe.trade_id, ct.observation_key AS trade_observation_key, ct.segment_slug, "
                    "pe.requested_item_id, pe.item_name, pe.quantity, pe.add_flag, pe.group_number, pe.rune_item_id, pe.created_at "
                    "FROM app.price_entries pe "
                    "JOIN app.completed_trades ct ON ct.trade_observation_id = pe.trade_id"
                )
                params: tuple[Any, ...] = ()
                if segment_slug:
                    sql += " WHERE ct.segment_slug = %s"
                    params = (segment_slug,)
                sql += " ORDER BY ct.captured_at, ct.listing_id, pe.group_number, pe.price_entry_id"
                return self._fetch_all(sql, params)
            return self._try_pg_or_dry("price_entries", "segment_slug", segment_slug)
        except Exception as exc:
            logger.warning("PG get_price_entries failed: %s", exc)
            return self._fallback("get_price_entries", segment_slug)

    def get_product_builds(self, segment_slug: Optional[str] = None) -> list[dict[str, Any]]:
        self._check_enabled()
        try:
            if self._has_real_pg():
                sql = (
                    "SELECT build_id, segment_slug, generated_at, status, schema_version, total_trades, unique_listings, "
                    "product_path, metadata, created_at FROM app.product_builds"
                )
                params: tuple[Any, ...] = ()
                if segment_slug:
                    sql += " WHERE segment_slug = %s"
                    params = (segment_slug,)
                sql += " ORDER BY generated_at DESC, segment_slug"
                return self._fetch_all(sql, params)
            return self._try_pg_or_dry("product_builds", "segment_slug", segment_slug)
        except Exception as exc:
            logger.warning("PG get_product_builds failed: %s", exc)
            return self._fallback("get_product_builds", segment_slug)

    def get_snapshot_runs(self, segment_slug: Optional[str] = None) -> list[dict[str, Any]]:
        self._check_enabled()
        try:
            if self._has_real_pg():
                sql = (
                    "SELECT snapshot_run_id, segment_slug, run_timestamp, status, item_count, listing_count, "
                    "error_count, duration_seconds, metadata, created_at FROM app.snapshot_runs"
                )
                params: tuple[Any, ...] = ()
                if segment_slug:
                    sql += " WHERE segment_slug = %s"
                    params = (segment_slug,)
                sql += " ORDER BY run_timestamp DESC, segment_slug"
                return self._fetch_all(sql, params)
            return self._try_pg_or_dry("snapshot_runs", "segment_slug", segment_slug)
        except Exception as exc:
            logger.warning("PG get_snapshot_runs failed: %s", exc)
            return self._fallback("get_snapshot_runs", segment_slug)

    def get_segment_rune_prices(self, segment_slug: Optional[str] = None, build_id: Optional[str] = None) -> list[dict[str, Any]]:
        self._check_enabled()
        try:
            if self._has_real_pg():
                sql = (
                    "SELECT rune_price_id, build_id, segment_slug, rune_id, rune_name, value_ist, bid_price, ask_price, "
                    "bid_count, ask_count, total_trades, confidence, confidence_reason, created_at "
                    "FROM app.segment_rune_prices WHERE (%s IS NULL OR segment_slug = %s) AND (%s IS NULL OR build_id = %s) "
                    "ORDER BY segment_slug, rune_name"
                )
                return self._fetch_all(sql, (segment_slug, segment_slug, build_id, build_id))
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
        if self._has_real_pg():
            segment_slug = trade.get("segment_slug")
            if not segment_slug and trade.get("source_slug"):
                segment_slug = str(trade["source_slug"]).split("/")[-1]
            price_entries = self._price_entries(trade)
            with self._connect() as conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO app.completed_trades (
                                segment_slug, observation_key, listing_id, content_hash, item_id, item_name,
                                quantity, seller, seller_rating, seller_reviews, seller_score, seller_status,
                                updated_at, captured_at, active, completed, platform, mode, hardcore, ladder,
                                game_version, ruleset, has_and_prices, price_group_count, price_entry_count,
                                source_payload, snapshot_run_id
                            )
                            VALUES (
                                %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s,
                                %s::jsonb, %s
                            )
                            ON CONFLICT (segment_slug, observation_key) DO UPDATE SET
                                listing_id = EXCLUDED.listing_id,
                                content_hash = EXCLUDED.content_hash,
                                item_id = EXCLUDED.item_id,
                                item_name = EXCLUDED.item_name,
                                quantity = EXCLUDED.quantity,
                                seller = EXCLUDED.seller,
                                seller_rating = EXCLUDED.seller_rating,
                                seller_reviews = EXCLUDED.seller_reviews,
                                seller_score = EXCLUDED.seller_score,
                                seller_status = EXCLUDED.seller_status,
                                updated_at = EXCLUDED.updated_at,
                                captured_at = EXCLUDED.captured_at,
                                active = EXCLUDED.active,
                                completed = EXCLUDED.completed,
                                platform = EXCLUDED.platform,
                                mode = EXCLUDED.mode,
                                hardcore = EXCLUDED.hardcore,
                                ladder = EXCLUDED.ladder,
                                game_version = EXCLUDED.game_version,
                                ruleset = EXCLUDED.ruleset,
                                has_and_prices = EXCLUDED.has_and_prices,
                                price_group_count = EXCLUDED.price_group_count,
                                price_entry_count = EXCLUDED.price_entry_count,
                                source_payload = EXCLUDED.source_payload,
                                snapshot_run_id = EXCLUDED.snapshot_run_id
                            RETURNING trade_observation_id
                            """,
                            (
                                segment_slug,
                                key,
                                self._int_or_none(trade.get("listing_id")),
                                self._content_hash(trade),
                                self._int_or_none(trade.get("item_id")),
                                trade.get("item_name"),
                                self._int_or_none(trade.get("quantity")) or 1,
                                trade.get("seller"),
                                trade.get("seller_rating"),
                                self._int_or_none(trade.get("seller_reviews")),
                                self._int_or_none(trade.get("seller_score")),
                                trade.get("seller_status"),
                                trade.get("updated_at"),
                                trade.get("captured_at") or trade.get("_captured_at"),
                                trade.get("active"),
                                trade.get("completed", True),
                                trade.get("platform", "pc"),
                                trade.get("mode"),
                                bool(trade.get("hardcore", False)),
                                trade.get("ladder"),
                                trade.get("game_version") or trade.get("version"),
                                trade.get("ruleset", "unknown"),
                                len(price_entries) > 1,
                                len({entry["group_number"] for entry in price_entries}) or 1,
                                len(price_entries) or 1,
                                json.dumps(trade, sort_keys=True, default=str),
                                trade.get("snapshot_run_id"),
                            ),
                        )
                        trade_id = cur.fetchone()["trade_observation_id"]
                        cur.execute("DELETE FROM app.price_entries WHERE trade_id = %s", (trade_id,))
                        for entry in price_entries:
                            cur.execute(
                                """
                                INSERT INTO app.price_entries (
                                    trade_id, requested_item_id, item_name, quantity, add_flag, group_number, rune_item_id
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                """,
                                (
                                    trade_id,
                                    entry["requested_item_id"],
                                    entry["item_name"],
                                    entry["quantity"],
                                    entry["add_flag"],
                                    entry["group_number"],
                                    entry["rune_item_id"],
                                ),
                            )
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
            return trade
        store = self._dry_store.setdefault("completed_trades", [])
        for i, existing in enumerate(store):
            if _observation_key(existing) == key:
                store[i] = trade
                return trade
        store.append(trade)
        return trade
