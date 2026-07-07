#!/bin/bash
set -euo pipefail

REPO_DIR="${TRADERIE_REPO_DIR:-/home/scraper/apps/traderie}"
VENV_DIR="${TRADERIE_VENV:-${REPO_DIR}/.venv}"
PYTHON="${TRADERIE_PYTHON:-${VENV_DIR}/bin/python}"

if [[ ! -x "$PYTHON" ]]; then
    PYTHON="python3"
fi

cd "$REPO_DIR"

"$PYTHON" scripts/validate_in_game_rune_values.py
"$PYTHON" scripts/validate_external_cash_prices.py
"$PYTHON" scripts/validate_source_manifest.py
"$PYTHON" scripts/validate_item_profiles.py
"$PYTHON" scripts/collection_status.py --json
