"""Storage adapter boundary for Traderie.

Abstract base class defining the storage interface, plus the file-backed
adapter which is the DEFAULT and AUTHORITATIVE backend.

See CODEX_SESSION_1_ARCHITECTURE.md §12-14.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TraderieStorageAdapter(ABC):
    """Abstract base for Traderie storage backends.

    Methods map to tables in app schema. Returns dicts with snake_case keys
    matching the PostgreSQL column names defined in db/migrations/.
    """

    @abstractmethod
    def get_segments(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_items(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_sources(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_completed_trades(self, segment_slug: Optional[str] = None) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_price_entries(self, segment_slug: Optional[str] = None) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_product_builds(self, segment_slug: Optional[str] = None) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_snapshot_runs(self, segment_slug: Optional[str] = None) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_segment_rune_prices(self, segment_slug: Optional[str] = None, build_id: Optional[str] = None) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def upsert_completed_trade(self, trade: dict[str, Any]) -> dict[str, Any]:
        ...


def _observation_key(trade: dict[str, Any]) -> str:
    return trade.get("_observation_key", trade.get("observation_key", ""))


class FileTraderieAdapter(TraderieStorageAdapter):
    """File-backed storage adapter.

    Reads from existing JSONL history files and data artifacts.
    This is the DEFAULT and AUTHORITATIVE backend. No write-back to files.
    In-memory upsert for test/dedup validation only.
    """

    def __init__(self, data_root: Optional[Path] = None):
        self._root = Path(data_root) if data_root else Path(__file__).resolve().parent.parent
        self._history_root = self._root / "data" / "history" / "traderie"
        self._product_path = self._root / "data" / "products" / "traderie_tools_prices.json"
        self._item_catalog_path = self._root / "scripts" / "item_catalog.json"
        self._source_manifest_path = self._root / "data" / "source_manifest.json"
        self._raw_snapshot_root = self._root / "data" / "snapshots" / "raw" / "traderie"

        self._in_memory_trades: list[dict[str, Any]] = []
        self._in_memory_keys: set[str] = set()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        records = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning("Skipping malformed JSONL line in %s", path)
                    continue
        return records

    def _segments_from_dirs(self) -> list[dict[str, Any]]:
        if not self._history_root.exists():
            return []
        segments = []
        for p in sorted(self._history_root.iterdir()):
            if not p.is_dir():
                continue
            slug = p.name
            parts = slug.split("_")
            hardcore = "hc" in parts
            ladder = parts[-1] == "l" if len(parts) >= 3 else False
            mode = "hardcore" if hardcore else "softcore"
            segments.append({
                "segment_slug": slug,
                "display_name": f"PC {'Hardcore' if hardcore else 'Softcore'} {'Ladder' if ladder else 'Non-Ladder'}",
                "platform": "pc",
                "mode": mode,
                "ladder": ladder,
                "hardcore": hardcore,
                "enabled": True,
            })
        return segments

    def _parse_price_entries(self, trade: dict[str, Any]) -> list[dict[str, Any]]:
        entries = []
        key = _observation_key(trade)
        slug = trade.get("segment_slug", trade.get("source_slug", ""))
        price = trade.get("price", [])
        if isinstance(price, list):
            for i, p in enumerate(price):
                entries.append({
                    "trade_observation_key": key,
                    "segment_slug": slug,
                    "requested_item_id": p.get("item_id"),
                    "item_name": p.get("name", ""),
                    "quantity": p.get("quantity", 1),
                    "add_flag": False,
                    "group_number": i,
                    "rune_item_id": p.get("item_id"),
                })
        return entries

    # ------------------------------------------------------------------
    # Segment, Items, Sources
    # ------------------------------------------------------------------

    def get_segments(self) -> list[dict[str, Any]]:
        return self._segments_from_dirs()

    def get_items(self) -> list[dict[str, Any]]:
        if not self._item_catalog_path.exists():
            return []
        with open(self._item_catalog_path) as f:
            data = json.load(f)
        return [
            {
                "item_id": e.get("item_id"),
                "name": e.get("name"),
                "category": e.get("category", "rune"),
                "short_name": e.get("short_name"),
                "tier": e.get("tier"),
            }
            for e in (data if isinstance(data, list) else [])
            if e.get("item_id")
        ]

    def get_sources(self) -> list[dict[str, Any]]:
        if not self._source_manifest_path.exists():
            return []
        with open(self._source_manifest_path) as f:
            data = json.load(f)
        return [
            {
                "source_id": slug,
                "name": info.get("name", slug),
                "source_type": info.get("source_type", "api"),
                "category": info.get("category", "completed_player_trades"),
                "priority": info.get("priority"),
                "status": info.get("status", "integrated"),
                "base_url": info.get("base_url"),
                "enabled": info.get("enabled", True),
            }
            for slug, info in (data.items() if isinstance(data, dict) else {}.items())
        ]

    # ------------------------------------------------------------------
    # Completed trades
    # ------------------------------------------------------------------

    def get_completed_trades(self, segment_slug: Optional[str] = None) -> list[dict[str, Any]]:
        if self._in_memory_trades:
            trades = self._in_memory_trades
            if segment_slug:
                return [t for t in trades if t.get("segment_slug") == segment_slug or t.get("source_slug", "").endswith(segment_slug)]
            return list(trades)
        trades = []
        paths: list[Path] = []
        if segment_slug:
            seg_dir = self._history_root / segment_slug
            if seg_dir.exists():
                paths = sorted(seg_dir.glob("*.jsonl"))
        elif self._history_root.exists():
            for d in sorted(self._history_root.iterdir()):
                if d.is_dir():
                    paths.extend(sorted(d.glob("*.jsonl")))
        for p in paths:
            trades.extend(self._load_jsonl(p))
        return trades

    # ------------------------------------------------------------------
    # Derived reads
    # ------------------------------------------------------------------

    def get_price_entries(self, segment_slug: Optional[str] = None) -> list[dict[str, Any]]:
        trades = self.get_completed_trades(segment_slug)
        entries = []
        for t in trades:
            entries.extend(self._parse_price_entries(t))
        return entries

    def get_product_builds(self, segment_slug: Optional[str] = None) -> list[dict[str, Any]]:
        if not self._product_path.exists():
            return []
        with open(self._product_path) as f:
            data = json.load(f)
        segs_data = data.get("segments", {})
        segs = [segment_slug] if segment_slug else list(segs_data.keys())
        builds = []
        for slug in segs:
            if slug not in segs_data:
                continue
            seg_prices = segs_data[slug]
            total = sum(t.get("total_trades", 0) for t in seg_prices.values()) if isinstance(seg_prices, dict) else 0
            builds.append({
                "build_id": f"file::{slug}::{data.get('generated_at', '')}",
                "segment_slug": slug,
                "generated_at": data.get("generated_at"),
                "status": "completed",
                "schema_version": data.get("schema_version"),
                "total_trades": total,
                "unique_listings": total,
                "product_path": str(self._product_path),
            })
        return builds

    def get_snapshot_runs(self, segment_slug: Optional[str] = None) -> list[dict[str, Any]]:
        if not self._raw_snapshot_root.exists():
            return []
        runs = []
        segs = [segment_slug] if segment_slug else [d.name for d in self._raw_snapshot_root.iterdir() if d.is_dir()]
        for slug in segs:
            seg_path = self._raw_snapshot_root / slug
            if not seg_path.exists():
                continue
            for ts_dir in sorted(seg_path.iterdir()):
                if not ts_dir.is_dir():
                    continue
                try:
                    dt = datetime.strptime(ts_dir.name, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                runs.append({
                    "snapshot_run_id": f"file::{slug}::{ts_dir.name}",
                    "segment_slug": slug,
                    "run_timestamp": dt.isoformat(),
                    "status": "completed",
                    "item_count": None,
                    "listing_count": None,
                    "error_count": None,
                    "duration_seconds": None,
                })
        return runs

    def get_segment_rune_prices(self, segment_slug: Optional[str] = None, build_id: Optional[str] = None) -> list[dict[str, Any]]:
        if not self._product_path.exists():
            return []
        with open(self._product_path) as f:
            data = json.load(f)
        segs_data = data.get("segments", {})
        segs = [segment_slug] if segment_slug else list(segs_data.keys())
        prices = []
        for slug in segs:
            if slug not in segs_data:
                continue
            build_key = f"file::{slug}::{data.get('generated_at', '')}"
            if build_id and build_id != build_key:
                continue
            seg_prices = segs_data[slug]
            if not isinstance(seg_prices, dict):
                continue
            for rune_name, info in seg_prices.items():
                prices.append({
                    "rune_price_id": f"file::{slug}::{rune_name}",
                    "build_id": build_key,
                    "segment_slug": slug,
                    "rune_id": None,
                    "rune_name": rune_name,
                    "value_ist": info.get("ist_value"),
                    "bid_price": info.get("bid_price"),
                    "ask_price": info.get("ask_price"),
                    "bid_count": 0,
                    "ask_count": 0,
                    "total_trades": info.get("total_trades", 0),
                    "confidence": info.get("confidence", "unavailable"),
                })
        return prices

    # ------------------------------------------------------------------
    # In-memory upsert (for dedup test, not production writer)
    # ------------------------------------------------------------------

    def upsert_completed_trade(self, trade: dict[str, Any]) -> dict[str, Any]:
        key = _observation_key(trade)
        if not key:
            raise ValueError("Trade must have _observation_key or observation_key")
        for i, existing in enumerate(self._in_memory_trades):
            if _observation_key(existing) == key:
                self._in_memory_trades[i] = trade
                return trade
        self._in_memory_trades.append(trade)
        self._in_memory_keys.add(key)
        return trade
