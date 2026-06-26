# Codex Handoff
Your instructions are below.
Write your output to:
```text
data/research/codex_graph_pricing_model_output.md
```

Do not write the final artifact anywhere else.

After writing the output file, respond with a brief completion note.

Instructions

Use this for fresh Codex. It includes only the context and files needed for the graph-model prototype.

You are working in the traderie repo for D2R Market Helper.
Goal: prototype a graph-based rune pricing model. Do not replace production pricing yet.
Project context:
- The project collects completed Diablo II: Resurrected trades from Traderie.
- Existing production prices are Ist-normalized rune values.
- Current production calculator only uses direct Ist↔Rune trades.
- Recent audit found this is materially incomplete:
  - 4,995 non-Ist rune trades exist in data/research CSVs.
  - Non-Ist trades are 40–70% of extracted rows depending on segment.
  - Jah↔Ber 1:1 is the most common high-rune trade pattern.
  - Example: pc_sc_l has 513 Jah↔Ber 1:1 trades.
  - Current Ist-only model reports Ber ≈ 1.49× Jah in softcore, while observed Jah↔Ber trades are 1:1.
- We need a side-by-side prototype, not a production replacement.
- Ist remains the normalization anchor: Ist = 1.0.
- Do not call Traderie API.
- Do not run launchctl.
- Do not touch external TraderieTools repo.
- Do not modify website deployment.
- Do not regenerate product JSON unless explicitly needed and approved.
Read these files first:
1. `scripts/calculate_rune_prices.py`
   - Understand current Ist-only pricing logic.
2. `scripts/build_traderie_dataset_from_history.py`
   - Understand extracted CSV structure and basket fields.
3. `scripts/audit_rune_pairs.py`
   - Understand existing non-Ist pair audit and parsing helpers.
4. `data/research/extracted_trades_pc_sc_l.csv`
5. `data/research/extracted_trades_pc_sc_nl.csv`
6. `data/research/extracted_trades_pc_hc_l.csv`
7. `data/research/extracted_trades_pc_hc_nl.csv`
8. `data/products/in_game_rune_values.json`
   - Use this for current production prices to compare against.
Task:
Create a prototype script:
`scripts/prototype_graph_rune_prices.py`
Model goal:
Represent rune-only completed trades as equations over rune values:
`sum(offered_qty_i * value_i) = sum(requested_qty_j * value_j)`
Examples:
- `Ber = Jah`
- `Ber = Jah + Ist`
- `Jah = Ohm + 3 Lo`
- `5 Ohm = Ber + Jah`
Requirements:
1. Parse rune baskets from existing extracted trade CSVs.
2. Include rune-only completed trades:
   - Ist↔Rune
   - Rune↔Rune
   - multi-rune basket ↔ rune
   - rune ↔ multi-rune basket
   - multi-rune ↔ multi-rune if parseable
3. Exclude:
   - non-rune items
   - malformed rows
   - empty baskets
4. Solve independently per segment:
   - `pc_sc_l`
   - `pc_sc_nl`
   - `pc_hc_l`
   - `pc_hc_nl`
5. Anchor Ist at exactly `1.0`.
6. Use a reasonable first-pass model:
   - linear least squares is acceptable
   - avoid negative rune values if possible
   - if SciPy is available, prefer non-negative least squares or robust least squares
   - if SciPy is not available, use NumPy least squares plus clipping/diagnostics
7. Add diagnostics:
   - total rows read
   - equations used
   - equations skipped
   - connected rune count
   - whether each rune is connected to Ist
   - residual/error summary
   - top conflicting equations by residual
8. Compare graph prices to current production prices:
   - segment
   - rune
   - current `value_ist`
   - graph `value_ist`
   - percent difference
   - graph support/equation count if available
9. Special focus:
   - Jah
   - Ber
   - Sur
   - Lo
   - Ohm
   - Vex
   - Gul
   - Ist
   - Mal
   - Jah/Ber ratio by segment
10. Do not write production JSON.
11. Acceptable outputs:
   - stdout tables
   - optional `data/research/graph_rune_prices_prototype.csv`
   - optional `data/research/graph_rune_model_diagnostics.csv`
Validation:
Run:
```bash
python3 -m py_compile scripts/prototype_graph_rune_prices.py
python3 scripts/prototype_graph_rune_prices.py
```

Return:

* modeling approach chosen
* files changed
* commands run
* graph prices for key runes by segment
* Jah/Ber comparison by segment
* largest differences from current Ist-only model
* diagnostics/residual summary
* recommendation:
    A) keep Ist-only production model
    B) add graph model as experimental product
    C) replace production pricing later after more validation

Important: this is research/prototyping. The immediate goal is to quantify whether a graph model solves the Jah/Ber problem without introducing worse instability elsewhere.