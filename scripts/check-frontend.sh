#!/usr/bin/env bash
# check-frontend.sh — Run frontend code quality checks
set -euo pipefail

FRONTEND_DIR="$(cd "$(dirname "$0")/../frontend" && pwd)"

echo "==> Frontend quality checks"
echo "    Directory: $FRONTEND_DIR"

cd "$FRONTEND_DIR"

# Install deps if node_modules is missing
if [ ! -d "node_modules" ]; then
  echo "==> Installing dependencies..."
  npm install
fi

echo "==> Running Prettier format check..."
npx prettier --check .

echo ""
echo "All checks passed."
echo ""
echo "To auto-fix formatting, run:"
echo "  cd frontend && npm run format"
