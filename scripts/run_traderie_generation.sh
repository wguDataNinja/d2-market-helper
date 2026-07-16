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
GLOBAL_START_TS=$(date -u +%s)
for SEGMENT in "${SEGMENTS[@]}"; do
    SEG_TIMEOUT="$(segment_timeout "$SEGMENT")"
    GLOBAL_ELAPSED=$(( $(date -u +%s) - GLOBAL_START_TS ))
    echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] [PHASE] segment_start segment=${SEGMENT} timeout=${SEG_TIMEOUT}s elapsed=${GLOBAL_ELAPSED}s"

    START_TS=$(date -u +%s)
    if timeout "$SEG_TIMEOUT" "$PYTHON" "$SNAPSHOT_SCRIPT" --segment "$SEGMENT"; then
        END_TS=$(date -u +%s)
        ELAPSED=$((END_TS - START_TS))
        PCT=$(( 100 * ELAPSED / SEG_TIMEOUT ))
        echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] [PHASE] segment_end segment=${SEGMENT} result=ok elapsed=${ELAPSED}s timeout=${SEG_TIMEOUT}s pct=${PCT}%"
    else
        EXIT_STATUS=$?
        END_TS=$(date -u +%s)
        ELAPSED=$((END_TS - START_TS))
        PCT=$(( 100 * ELAPSED / SEG_TIMEOUT ))
        if [ "$EXIT_STATUS" -eq 124 ]; then
            echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] [PHASE] segment_end segment=${SEGMENT} result=timeout elapsed=${ELAPSED}s timeout=${SEG_TIMEOUT}s pct=${PCT}%" >&2
        else
            echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] [PHASE] segment_end segment=${SEGMENT} result=fail exit=${EXIT_STATUS} elapsed=${ELAPSED}s timeout=${SEG_TIMEOUT}s pct=${PCT}%" >&2
        fi
        OVERALL_EXIT=1
        # Continue to next segment on failure (do not stop the generation)
    fi
done

GLOBAL_ELAPSED=$(( $(date -u +%s) - GLOBAL_START_TS ))
echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] [PHASE] generation_end result=$([ "$OVERALL_EXIT" -eq 0 ] && echo ok || echo partial_failure) elapsed=${GLOBAL_ELAPSED}s exit=${OVERALL_EXIT}"
exit "$OVERALL_EXIT"
