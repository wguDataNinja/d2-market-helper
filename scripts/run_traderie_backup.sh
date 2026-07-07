#!/bin/bash
set -euo pipefail

REPO_DIR="${TRADERIE_REPO_DIR:-/home/scraper/apps/traderie}"
BACKUP_ROOT="${TRADERIE_BACKUP_ROOT:-/home/scraper/backups/postgres/traderie}"
DATABASE="${TRADERIE_PG_DATABASE:-traderie}"
BACKUP_USER="${TRADERIE_PG_BACKUP_USER:-traderie_backup}"
PG_DUMP="${TRADERIE_PG_DUMP:-pg_dump}"
PG_URL="${TRADERIE_BACKUP_PG_URL:-postgresql://${BACKUP_USER}@localhost/${DATABASE}}"
STAMP="$(date -u '+%Y%m%dT%H%M%SZ')"

mkdir -p "$BACKUP_ROOT"
cd "$REPO_DIR"

if [[ "${TRADERIE_PG_ADAPTER_ENABLED:-false}" != "true" ]]; then
    MANIFEST="${BACKUP_ROOT}/traderie_backup_${STAMP}.skip.json"
    cat > "$MANIFEST" <<EOF
{"generated_at":"$(date -u '+%Y-%m-%dT%H:%M:%SZ')","database":"${DATABASE}","backup_state":"not_applicable","reason":"TRADERIE_PG_ADAPTER_ENABLED is not true"}
EOF
    echo "PostgreSQL backup skipped; manifest written to $MANIFEST"
    exit 0
fi

DUMP_PATH="${BACKUP_ROOT}/traderie_${STAMP}.dump"
SHA_PATH="${DUMP_PATH}.sha256"
MANIFEST="${DUMP_PATH}.manifest.json"

"$PG_DUMP" --format=custom --compress=9 --dbname="$PG_URL" --file="$DUMP_PATH"
shasum -a 256 "$DUMP_PATH" > "$SHA_PATH"

cat > "$MANIFEST" <<EOF
{"generated_at":"$(date -u '+%Y-%m-%dT%H:%M:%SZ')","database":"${DATABASE}","backup_state":"ok","dump_path":"${DUMP_PATH}","sha256_path":"${SHA_PATH}"}
EOF

echo "PostgreSQL backup written to $DUMP_PATH"
