#!/usr/bin/env bash
# Universal Booking Bot — backup SQLite database
set -euo pipefail

INSTALL_DIR="/opt/universal_booking_bot"
DB_PATH="$INSTALL_DIR/data/booking_bot.db"
BACKUP_DIR="$INSTALL_DIR/backups"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/booking_bot_${STAMP}.db"

if [ ! -f "$DB_PATH" ]; then
  echo "ERROR: Database not found at $DB_PATH"
  exit 1
fi

mkdir -p "$BACKUP_DIR"
cp "$DB_PATH" "$BACKUP_FILE"

echo "Backup saved: $BACKUP_FILE"
