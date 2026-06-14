#!/usr/bin/env bash
# Universal Booking Bot — stop containers and optionally remove install directory
set -euo pipefail

INSTALL_DIR="/opt/universal_booking_bot"

read -r -p "Stop bot and remove $INSTALL_DIR? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Cancelled."
  exit 0
fi

if [ -f "$INSTALL_DIR/docker-compose.yml" ]; then
  (cd "$INSTALL_DIR" && docker compose down) || true
fi

read -r -p "Delete database and backups in $INSTALL_DIR? [y/N] " wipe
if [[ "$wipe" =~ ^[Yy]$ ]]; then
  sudo rm -rf "$INSTALL_DIR"
  echo "Removed $INSTALL_DIR"
else
  echo "Containers stopped. Files kept at $INSTALL_DIR"
fi
