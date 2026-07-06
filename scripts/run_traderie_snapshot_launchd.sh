#!/bin/bash
set -euo pipefail

REPO_DIR="${TRADERIE_REPO_DIR:-/Users/buddy/projects/traderie}"
LOCK_DIR="${REPO_DIR}/.run/locks/snapshot-traderie.lock"
PYTHON="${REPO_DIR}/.venv/bin/python"
SNAPSHOT_SCRIPT="${REPO_DIR}/scripts/snapshot_traderie.py"
LOG_DIR="${REPO_DIR}/logs/launchd"

# Ensure run dirs exist
mkdir -p "$(dirname "$LOCK_DIR")" "$LOG_DIR"

# Lock: prevent overlapping runs (mkdir is atomic on macOS)
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] ERROR: Another snapshot run is in progress (lock held). Exiting."
    exit 1
fi

# Ensure lock auto-releases on exit
trap 'rm -rf "$LOCK_DIR"' EXIT

echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Traderie snapshot collection starting"
echo "Python: $PYTHON"
echo "PID: $$"

SEGMENTS=("pc_sc_nl" "pc_sc_l" "pc_hc_l" "pc_hc_nl")
EXIT_CODE=0

for SEGMENT in "${SEGMENTS[@]}"; do
    echo ""
    echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] --- Segment: $SEGMENT ---"
    if "$PYTHON" "$SNAPSHOT_SCRIPT" --segment "$SEGMENT" 2>>"${LOG_DIR}/snapshot-traderie.err.log"; then
        echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Segment $SEGMENT completed successfully"
    else
        echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] ERROR: Segment $SEGMENT failed (exit code $?)" >&2
        EXIT_CODE=1
    fi
done

echo ""
echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Traderie snapshot collection finished (exit code $EXIT_CODE)"
exit "$EXIT_CODE"
