#!/usr/bin/env bash
# Universal Booking Bot — pull latest and rebuild
set -euo pipefail

INSTALL_DIR="/opt/universal_booking_bot"
BRANCH="main"

cd "$INSTALL_DIR"

if [ ! -d .git ]; then
  echo "ERROR: $INSTALL_DIR is not a git repository. Run install.sh first."
  exit 1
fi

echo "=== Universal Booking Bot — update ==="

git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull origin "$BRANCH"

docker compose down
docker compose up -d --build

echo ""
echo "=== Update complete ==="
echo "View logs: docker compose logs -f booking-bot"
