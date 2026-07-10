#!/bin/bash
set -euo pipefail

REPO_DIR="${TRADERIE_REPO_DIR:-/home/scraper/apps/traderie}"
VENV_DIR="${TRADERIE_VENV:-${REPO_DIR}/.venv}"
PYTHON="${TRADERIE_PYTHON:-${VENV_DIR}/bin/python}"
SNAPSHOT_SCRIPT="${REPO_DIR}/scripts/snapshot_traderie.py"

# Per-segment timeout in seconds, derived from observed VPS bounded runs.
# Observed max: pc_sc_nl=35s, pc_sc_l=104s, pc_hc_l=132s, pc_hc_nl=329s+
# Timeout = observed max * ~2 or theoretical worst case, whichever is lower.
segment_timeout() {
    case "$1" in
        pc_sc_nl) echo 180 ;;
        pc_sc_l)  echo 240 ;;
        pc_hc_l)  echo 360 ;;
        pc_hc_nl) echo 480 ;;
        *)        echo 300 ;;
    esac
}

if [[ ! -x "$PYTHON" ]]; then
    PYTHON="python3"
fi

cd "$REPO_DIR"

SEGMENTS_VALUE="${TRADERIE_SEGMENTS:-pc_sc_nl pc_sc_l pc_hc_l pc_hc_nl}"
read -r -a SEGMENTS <<< "$SEGMENTS_VALUE"

echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Traderie generation starting"
echo "Python: $PYTHON"
echo "Segments: ${SEGMENTS[*]}"

OVERALL_EXIT=0
for SEGMENT in "${SEGMENTS[@]}"; do
    SEG_TIMEOUT="$(segment_timeout "$SEGMENT")"
    echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Segment: $SEGMENT (timeout=${SEG_TIMEOUT}s)"

    START_TS=$(date -u +%s)
    if timeout "$SEG_TIMEOUT" "$PYTHON" "$SNAPSHOT_SCRIPT" --segment "$SEGMENT"; then
        END_TS=$(date -u +%s)
        ELAPSED=$((END_TS - START_TS))
        echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Segment $SEGMENT completed (${ELAPSED}s)"
    else
        EXIT_STATUS=$?
        END_TS=$(date -u +%s)
        ELAPSED=$((END_TS - START_TS))
        if [ "$EXIT_STATUS" -eq 124 ]; then
            echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] ERROR: segment $SEGMENT timed out after ${SEG_TIMEOUT}s" >&2
        else
            echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] ERROR: segment $SEGMENT failed (exit=${EXIT_STATUS}, ${ELAPSED}s)" >&2
        fi
        OVERALL_EXIT=1
        # Continue to next segment on failure (do not stop the generation)
    fi
done

echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Traderie generation finished (exit=${OVERALL_EXIT})"
exit "$OVERALL_EXIT"
