#!/usr/bin/env python3
"""Prototype graph-based rune pricing from local extracted Traderie CSVs.

This is intentionally research-only. It reads data/research extracted trade
CSVs, anchors Ist Rune at exactly 1.0, and solves one independent rune-value
system per economy segment.
"""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median

ROOT_DIR = Path(__file__).resolve().parent.parent
RESEARCH_DIR = ROOT_DIR / "data" / "research"
ITEMS_PATH = ROOT_DIR / "data" / "item_ids.json"
PRODUCT_PATH = ROOT_DIR / "data" / "products" / "in_game_rune_values.json"

SEGMENTS = ["pc_sc_l", "pc_sc_nl", "pc_hc_l", "pc_hc_nl"]
ANCHOR_RUNE = "Ist Rune"
ANCHOR_VALUE = 1.0
PRICE_OUTPUT = RESEARCH_DIR / "graph_rune_prices_prototype.csv"
DIAGNOSTICS_OUTPUT = RESEARCH_DIR / "graph_rune_model_diagnostics.csv"

RUNE_RE = re.compile(r"^(.+?\s+Rune)\s*:\s*(\d+)\s*$")
KEY_RUNES = ["Ist", "Gul", "Vex", "Ohm", "Lo", "Sur", "Ber", "Jah", "Cham", "Zod"]


@dataclass
class Equation:
    row_number: int
    trade_id: str
    offered: dict[str, int]
    requested: dict[str, int]
    coeffs: dict[str, int]
    rhs: float
    label: str


def load_valid_runes() -> list[str]:
    data = json.loads(ITEMS_PATH.read_text())
    return list(data["Runes"].keys())


def short_rune_name(rune: str) -> str:
    return rune.removesuffix(" Rune")


def parse_basket(raw: str, valid_runes: set[str]) -> tuple[dict[str, int] | None, str | None]:
    if raw is None:
        return None, "missing"

    basket: dict[str, int] = defaultdict(int)
    for part in raw.split(";"):
        part = part.strip()
        if not part:
            continue
        match = RUNE_RE.match(part)
        if not match:
            return None, f"malformed_part:{part}"
        rune, qty_text = match.groups()
        if rune not in valid_runes:
            return None, f"non_rune:{rune}"
        qty = int(qty_text)
        if qty <= 0:
            return None, f"non_positive_qty:{part}"
        basket[rune] += qty

    if not basket:
        return None, "empty"
    return dict(basket), None


def basket_label(basket: dict[str, int]) -> str:
    return "+".join(f"{short_rune_name(rune)}:{qty}" for rune, qty in sorted(basket.items()))


def load_current_prices() -> dict[str, dict[str, float | None]]:
    data = json.loads(PRODUCT_PATH.read_text())
    prices: dict[str, dict[str, float | None]] = {}
    for segment in SEGMENTS:
        runes = data.get("segments", {}).get(segment, {}).get("runes", {})
        prices[segment] = {
            rune: obs.get("value_ist")
            for rune, obs in runes.items()
            if isinstance(obs, dict)
        }
    return prices


def equation_from_trade(row_number: int, row: dict[str, str], valid_runes: set[str]) -> tuple[Equation | None, str | None]:
    offered, offered_error = parse_basket(row.get("Offered", ""), valid_runes)
    if offered_error:
        return None, f"offered_{offered_error}"
    requested, requested_error = parse_basket(row.get("Requested", ""), valid_runes)
    if requested_error:
        return None, f"requested_{requested_error}"

    coeffs: dict[str, int] = {}
    for rune in sorted(set(offered) | set(requested)):
        if rune == ANCHOR_RUNE:
            continue
        coeff = offered.get(rune, 0) - requested.get(rune, 0)
        if coeff:
            coeffs[rune] = coeff

    # sum(offered) = sum(requested)
    # non_ist_coeffs * x + (offered_ist - requested_ist) * 1.0 = 0
    rhs = float(requested.get(ANCHOR_RUNE, 0) - offered.get(ANCHOR_RUNE, 0))

    if not coeffs:
        return None, "anchor_only_or_cancelled"

    trade_id = row.get("TradeID") or row.get("listing_id") or f"row_{row_number}"
    label = f"{basket_label(offered)} -> {basket_label(requested)}"
    return Equation(row_number, trade_id, offered, requested, coeffs, rhs, label), None


def connected_to_anchor(equations: list[Equation], runes: list[str]) -> set[str]:
    graph: dict[str, set[str]] = {rune: set() for rune in runes}
    for eq in equations:
        present = set(eq.offered) | set(eq.requested)
        for left in present:
            graph.setdefault(left, set())
            for right in present:
                if left != right:
                    graph[left].add(right)

    seen = {ANCHOR_RUNE}
    queue: deque[str] = deque([ANCHOR_RUNE])
    while queue:
        current = queue.popleft()
        for neighbor in graph.get(current, set()):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen


def solve_prices(equations: list[Equation], runes: list[str]) -> tuple[dict[str, float], str]:
    unknowns = [rune for rune in runes if rune != ANCHOR_RUNE]
    index = {rune: pos for pos, rune in enumerate(unknowns)}
    a = [[0.0 for _ in unknowns] for _ in equations]
    b = [0.0 for _ in equations]

    for row_idx, eq in enumerate(equations):
        for rune, coeff in eq.coeffs.items():
            a[row_idx][index[rune]] = coeff
        b[row_idx] = eq.rhs

    try:
        from scipy.optimize import nnls  # type: ignore

        solution, _ = nnls(a, b)
        solver_name = "scipy_nnls"
    except Exception:
        try:
            import numpy as np  # type: ignore

            solution, *_ = np.linalg.lstsq(np.array(a, dtype=float), np.array(b, dtype=float), rcond=None)
            solution = np.clip(solution, 0.0, None)
            solver_name = "numpy_lstsq_clipped"
        except Exception:
            solution = pure_python_lstsq_clipped(a, b)
            solver_name = "pure_python_normal_eq_clipped"

    prices = {ANCHOR_RUNE: ANCHOR_VALUE}
    for rune, pos in index.items():
        prices[rune] = float(solution[pos])
    return prices, solver_name


def pure_python_lstsq_clipped(a: list[list[float]], b: list[float]) -> list[float]:
    """Solve least squares with tiny ridge regularization using only stdlib.

    This is a validation fallback for environments without SciPy/NumPy. The
    intended path remains scipy.nnls or numpy.linalg.lstsq when available.
    """
    if not a:
        return []

    cols = len(a[0])
    ridge = 1e-9
    ata = [[0.0 for _ in range(cols)] for _ in range(cols)]
    atb = [0.0 for _ in range(cols)]

    for row, rhs in zip(a, b):
        for i in range(cols):
            atb[i] += row[i] * rhs
            for j in range(cols):
                ata[i][j] += row[i] * row[j]

    for i in range(cols):
        ata[i][i] += ridge

    solution = gaussian_solve(ata, atb)
    return [max(0.0, value) for value in solution]


def gaussian_solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    n = len(vector)
    aug = [row[:] + [vector[i]] for i, row in enumerate(matrix)]

    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(aug[row][col]))
        if abs(aug[pivot][col]) < 1e-12:
            continue
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]

        pivot_value = aug[col][col]
        for j in range(col, n + 1):
            aug[col][j] /= pivot_value

        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            if factor == 0:
                continue
            for j in range(col, n + 1):
                aug[row][j] -= factor * aug[col][j]

    return [aug[i][n] if abs(aug[i][i]) > 1e-12 else 0.0 for i in range(n)]


def residuals_for(equations: list[Equation], prices: dict[str, float]) -> list[dict[str, object]]:
    rows = []
    for eq in equations:
        lhs = sum(qty * prices.get(rune, 0.0) for rune, qty in eq.offered.items())
        rhs = sum(qty * prices.get(rune, 0.0) for rune, qty in eq.requested.items())
        residual = lhs - rhs
        rows.append(
            {
                "row_number": eq.row_number,
                "trade_id": eq.trade_id,
                "equation": eq.label,
                "lhs": lhs,
                "rhs": rhs,
                "residual": residual,
                "abs_residual": abs(residual),
            }
        )
    return rows


def residual_summary(residual_rows: list[dict[str, object]]) -> dict[str, float]:
    if not residual_rows:
        return {"mean_abs": math.nan, "median_abs": math.nan, "p90_abs": math.nan, "max_abs": math.nan, "rmse": math.nan}

    abs_values = sorted(float(row["abs_residual"]) for row in residual_rows)
    residual_values = [float(row["residual"]) for row in residual_rows]
    p90_index = min(len(abs_values) - 1, math.ceil(0.90 * len(abs_values)) - 1)
    return {
        "mean_abs": mean(abs_values),
        "median_abs": median(abs_values),
        "p90_abs": abs_values[p90_index],
        "max_abs": abs_values[-1],
        "rmse": math.sqrt(mean(value * value for value in residual_values)),
    }


def pct_delta(model: float | None, production: float | None) -> float | None:
    if model is None or production in (None, 0):
        return None
    return (model - production) / production * 100.0


def fmt(value: object, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        if math.isnan(value):
            return "n/a"
        return f"{value:.{digits}f}"
    return str(value)


def analyze_segment(segment: str, valid_runes: list[str], current_prices: dict[str, dict[str, float | None]]) -> dict[str, object]:
    csv_path = RESEARCH_DIR / f"extracted_trades_{segment}.csv"
    rows_read = 0
    skip_reasons: defaultdict[str, int] = defaultdict(int)
    equations: list[Equation] = []

    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for rows_read, row in enumerate(reader, start=1):
            eq, skip_reason = equation_from_trade(rows_read, row, set(valid_runes))
            if skip_reason:
                skip_reasons[skip_reason] += 1
                continue
            equations.append(eq)

    prices, solver_name = solve_prices(equations, valid_runes)
    connected = connected_to_anchor(equations, valid_runes)
    residual_rows = residuals_for(equations, prices)
    summary = residual_summary(residual_rows)
    top_conflicts = sorted(residual_rows, key=lambda row: float(row["abs_residual"]), reverse=True)[:10]

    production = current_prices.get(segment, {})
    price_rows = []
    for rune in valid_runes:
        short = short_rune_name(rune)
        model_price = prices.get(rune)
        production_price = ANCHOR_VALUE if rune == ANCHOR_RUNE else production.get(short)
        price_rows.append(
            {
                "segment": segment,
                "rune": short,
                "model_value_ist": model_price,
                "production_value_ist": production_price,
                "delta_pct_vs_production": pct_delta(model_price, production_price),
                "connected_to_ist": rune in connected,
            }
        )

    jah = prices.get("Jah Rune")
    ber = prices.get("Ber Rune")
    prod_jah = production.get("Jah")
    prod_ber = production.get("Ber")
    jah_ber = (jah / ber) if jah and ber else None
    prod_jah_ber = (prod_jah / prod_ber) if prod_jah and prod_ber else None
    ber_jah = (ber / jah) if jah and ber else None
    prod_ber_jah = (prod_ber / prod_jah) if prod_jah and prod_ber else None

    return {
        "segment": segment,
        "rows_read": rows_read,
        "equations": equations,
        "equations_used": len(equations),
        "skip_reasons": dict(skip_reasons),
        "connected": connected,
        "connected_count": len(connected),
        "solver_name": solver_name,
        "prices": prices,
        "price_rows": price_rows,
        "residual_summary": summary,
        "top_conflicts": top_conflicts,
        "jah_ber": jah_ber,
        "prod_jah_ber": prod_jah_ber,
        "ber_jah": ber_jah,
        "prod_ber_jah": prod_ber_jah,
    }


def write_price_output(results: list[dict[str, object]]) -> None:
    fieldnames = [
        "segment",
        "rune",
        "model_value_ist",
        "production_value_ist",
        "delta_pct_vs_production",
        "connected_to_ist",
    ]
    with PRICE_OUTPUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            for row in result["price_rows"]:
                writer.writerow(row)


def write_diagnostics_output(results: list[dict[str, object]], valid_runes: list[str]) -> None:
    fieldnames = [
        "segment",
        "row_type",
        "rune",
        "metric",
        "value",
        "details",
    ]
    with DIAGNOSTICS_OUTPUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            segment = str(result["segment"])
            summary = result["residual_summary"]
            base_metrics = {
                "rows_read": result["rows_read"],
                "equations_used": result["equations_used"],
                "equations_skipped": int(result["rows_read"]) - int(result["equations_used"]),
                "connected_rune_count": result["connected_count"],
                "solver": result["solver_name"],
                **{f"residual_{key}": value for key, value in summary.items()},
            }
            for metric, value in base_metrics.items():
                writer.writerow({"segment": segment, "row_type": "summary", "metric": metric, "value": value, "rune": "", "details": ""})
            for reason, count in result["skip_reasons"].items():
                writer.writerow({"segment": segment, "row_type": "skip_reason", "metric": reason, "value": count, "rune": "", "details": ""})
            for rune in valid_runes:
                writer.writerow(
                    {
                        "segment": segment,
                        "row_type": "connection",
                        "rune": short_rune_name(rune),
                        "metric": "connected_to_ist",
                        "value": rune in result["connected"],
                        "details": "",
                    }
                )
            for conflict in result["top_conflicts"]:
                writer.writerow(
                    {
                        "segment": segment,
                        "row_type": "top_conflict",
                        "rune": "",
                        "metric": "abs_residual",
                        "value": conflict["abs_residual"],
                        "details": f"row={conflict['row_number']} trade={conflict['trade_id']} residual={conflict['residual']:.6f} equation={conflict['equation']}",
                    }
                )


def print_segment_summary(result: dict[str, object]) -> None:
    segment = result["segment"]
    summary = result["residual_summary"]
    print(f"\n--- {segment} ---")
    print(f"solver: {result['solver_name']}")
    print(f"rows read: {result['rows_read']}")
    print(f"equations used: {result['equations_used']}")
    print(f"equations skipped: {int(result['rows_read']) - int(result['equations_used'])}")
    print(f"connected rune count including Ist: {result['connected_count']}")
    print(
        "residual abs mean/median/p90/max/rmse: "
        f"{fmt(summary['mean_abs'])} / {fmt(summary['median_abs'])} / "
        f"{fmt(summary['p90_abs'])} / {fmt(summary['max_abs'])} / {fmt(summary['rmse'])}"
    )

    skip_reasons = result["skip_reasons"]
    if skip_reasons:
        skip_text = ", ".join(f"{reason}={count}" for reason, count in sorted(skip_reasons.items()))
        print(f"skip reasons: {skip_text}")

    prices = result["prices"]
    production = load_current_prices().get(str(segment), {})
    print("key rune comparison (model vs production Ist):")
    for rune in KEY_RUNES:
        full = f"{rune} Rune"
        if full not in prices and rune != "Ist":
            continue
        model_value = ANCHOR_VALUE if rune == "Ist" else prices.get(full)
        production_value = ANCHOR_VALUE if rune == "Ist" else production.get(rune)
        delta = pct_delta(model_value, production_value)
        print(f"  {rune:>4}: {fmt(model_value):>9} vs {fmt(production_value):>9} delta={fmt(delta, 1):>7}%")

    print(
        "Jah/Ber ratio: "
        f"model Jah/Ber={fmt(result['jah_ber'])}, production Jah/Ber={fmt(result['prod_jah_ber'])}; "
        f"model Ber/Jah={fmt(result['ber_jah'])}, production Ber/Jah={fmt(result['prod_ber_jah'])}"
    )
    print("top conflicting equations:")
    for conflict in result["top_conflicts"][:5]:
        print(
            f"  abs={float(conflict['abs_residual']):.4f} residual={float(conflict['residual']):.4f} "
            f"row={conflict['row_number']} {conflict['equation']}"
        )


def main() -> int:
    valid_runes = load_valid_runes()
    current_prices = load_current_prices()
    missing = [segment for segment in SEGMENTS if not (RESEARCH_DIR / f"extracted_trades_{segment}.csv").exists()]
    if missing:
        print(f"missing extracted research CSVs: {', '.join(missing)}", file=sys.stderr)
        return 2

    results = [analyze_segment(segment, valid_runes, current_prices) for segment in SEGMENTS]
    write_price_output(results)
    write_diagnostics_output(results, valid_runes)

    print("GRAPH RUNE PRICING PROTOTYPE")
    print(f"Ist anchor: {ANCHOR_VALUE:.1f}")
    print(f"price output: {PRICE_OUTPUT.relative_to(ROOT_DIR)}")
    print(f"diagnostics output: {DIAGNOSTICS_OUTPUT.relative_to(ROOT_DIR)}")
    for result in results:
        print_segment_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
