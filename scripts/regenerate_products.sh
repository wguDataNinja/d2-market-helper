#!/bin/bash
set -euo pipefail

REPO_DIR="/Users/buddy/projects/traderie"
PYTHON="${REPO_DIR}/.venv/bin/python"

"$PYTHON" scripts/build_traderie_dataset_from_history.py --write-research
"$PYTHON" scripts/calculate_rune_prices.py --input-dir data/research
"$PYTHON" scripts/generate_prices_json.py
"$PYTHON" scripts/generate_external_cash_prices.py
"$PYTHON" scripts/validate_in_game_rune_values.py
"$PYTHON" scripts/validate_external_cash_prices.py
"$PYTHON" scripts/collection_status.py
echo "Regeneration complete."
