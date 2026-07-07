#!/bin/bash
set -euo pipefail

REPO_DIR="${TRADERIE_REPO_DIR:-/home/scraper/apps/traderie}"
VENV_DIR="${TRADERIE_VENV:-${REPO_DIR}/.venv}"
PYTHON="${TRADERIE_PYTHON:-${VENV_DIR}/bin/python}"
SNAPSHOT_SCRIPT="${REPO_DIR}/scripts/snapshot_traderie.py"

if [[ ! -x "$PYTHON" ]]; then
    PYTHON="python3"
fi

cd "$REPO_DIR"

SEGMENTS_VALUE="${TRADERIE_SEGMENTS:-pc_sc_nl pc_sc_l pc_hc_l pc_hc_nl}"
read -r -a SEGMENTS <<< "$SEGMENTS_VALUE"

echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Traderie snapshot collection starting"
echo "Python: $PYTHON"
echo "Segments: ${SEGMENTS[*]}"

EXIT_CODE=0
for SEGMENT in "${SEGMENTS[@]}"; do
    echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Segment: $SEGMENT"
    if "$PYTHON" "$SNAPSHOT_SCRIPT" --segment "$SEGMENT"; then
        echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Segment $SEGMENT completed"
    else
        echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] ERROR: segment $SEGMENT failed" >&2
        EXIT_CODE=1
    fi
done

echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Traderie snapshot collection finished"
exit "$EXIT_CODE"
