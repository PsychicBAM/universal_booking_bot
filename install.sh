#!/usr/bin/env bash
# Universal Booking Bot — server install (Docker)
set -euo pipefail

REPO_URL="https://github.com/PsychicBAM/universal_booking_bot.git"
INSTALL_DIR="/opt/universal_booking_bot"
BRANCH="main"

echo "=== Universal Booking Bot — install ==="

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is not installed. Install Docker first."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1 && ! docker-compose version >/dev/null 2>&1; then
  echo "ERROR: Docker Compose is not available. Install docker compose plugin or docker-compose."
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is not installed."
  exit 1
fi

if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Directory $INSTALL_DIR already exists with git repo."
  echo "Use update.sh to pull latest changes, or uninstall.sh first."
  exit 1
fi

sudo mkdir -p "$INSTALL_DIR"
sudo chown "$(whoami):$(id -gn)" "$INSTALL_DIR"

git clone --branch "$BRANCH" --depth 1 "$REPO_URL" "$INSTALL_DIR"
cd "$INSTALL_DIR"

mkdir -p data backups

if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "Created .env from .env.example"
  echo "IMPORTANT: Edit $INSTALL_DIR/.env before production use:"
  echo "  - BOT_TOKEN"
  echo "  - ADMIN_IDS (comma-separated Telegram user IDs, e.g. 123456789,987654321)"
  echo "  - Optional Google Calendar credentials"
  echo ""
fi

if grep -q '{{BOT_TOKEN}}' .env 2>/dev/null; then
  echo "WARNING: .env still contains placeholder {{BOT_TOKEN}}."
  echo "Set real values in .env, then run:"
  echo "  cd $INSTALL_DIR && docker compose up -d --build"
  exit 0
fi

docker compose up -d --build

echo ""
echo "=== Install complete ==="
echo "Project directory: $INSTALL_DIR"
echo "View logs:         cd $INSTALL_DIR && docker compose logs -f booking-bot"
echo "Update later:      bash $INSTALL_DIR/update.sh"
echo "Backup database:   bash $INSTALL_DIR/backup.sh"
