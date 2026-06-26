#!/bin/bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PUBLIC_DATA_DIR="${REPO_DIR}/web/public/data"
PRODUCTS_DIR="${REPO_DIR}/data/products"

echo "=== Deploy: D2R Market Helper Web ==="

# 1. Copy product JSONs to public/ for runtime fetch (userscript etc.)
echo "Copying product JSONs to web/public/data/..."
mkdir -p "$PUBLIC_DATA_DIR"
cp "$PRODUCTS_DIR"/in_game_rune_values.json "$PUBLIC_DATA_DIR/"
cp "$PRODUCTS_DIR"/traderie_tools_prices.json "$PUBLIC_DATA_DIR/"
cp "$PRODUCTS_DIR"/rune_prices_legacy.json "$PUBLIC_DATA_DIR/"
cp "$PRODUCTS_DIR"/external_cash_prices.sample.json "$PUBLIC_DATA_DIR/"
cp "${REPO_DIR}/data/source_manifest.json" "$PUBLIC_DATA_DIR/"
cp "${REPO_DIR}/data/rune_registry.json" "$PUBLIC_DATA_DIR/"
echo "  Done: $(ls "$PUBLIC_DATA_DIR" | wc -l) files"

# 2. Build production site
echo "Building web app..."
npm --prefix "${REPO_DIR}/web" run build
echo "  Done: web/dist/ ready"

# 3. Summary
echo ""
echo "=== Deploy Summary ==="
echo "  Build: web/dist/"
echo "  Public data: web/public/data/ (served at /data/*)"
echo "  Deploy target: GitHub Pages (push web/dist/ or use Actions)"
echo "  To publish:"
echo "    1. Ensure git remote is set"
echo "    2. Push master branch"
echo "    3. GitHub Actions will deploy, or run:"
echo "       npx gh-pages -d web/dist -b gh-pages"
echo "=== Done ==="
