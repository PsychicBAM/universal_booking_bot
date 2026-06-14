# Deployment Guide

## Repository

- **GitHub:** https://github.com/PsychicBAM/universal_booking_bot
- **Raw install script:** https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh

## Recommended install (Ubuntu / Debian VPS)

```bash
bash <(curl -Ls https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh)
```

The script:

1. Clones `https://github.com/PsychicBAM/universal_booking_bot.git` into `/opt/universal_booking_bot`
2. Creates `data/` and `backups/`
3. Copies `.env.example` → `.env` if missing
4. Runs `docker compose up -d --build` when `.env` has real `BOT_TOKEN`

## Install directory

All server scripts use:

```
/opt/universal_booking_bot
```

| Script | Purpose |
|--------|---------|
| `install.sh` | First-time clone + Docker build |
| `update.sh` | `git pull` + rebuild containers |
| `backup.sh` | Copy `data/booking_bot.db` → `backups/booking_bot_YYYYMMDD_HHMMSS.db` |
| `uninstall.sh` | Stop containers; optionally delete install dir |

## Configuration

Edit `/opt/universal_booking_bot/.env` before going live.

**Required:**

- `BOT_TOKEN`
- `ADMIN_IDS`

**Optional:**

- `TIMEZONE`, `DEFAULT_LANGUAGE`, `CONTACT_ADMIN_USERNAME`
- `GOOGLE_CALENDAR_*` — see [README.md](README.md#google-calendar-setup)
- `REMINDERS_*`, `CANCEL_BOOKING_HOURS_BEFORE`, `RESCHEDULE_BOOKING_HOURS_BEFORE`

Never commit `.env` to git. Only `.env.example` with placeholders belongs in the repository.

## Operations

### View logs

```bash
cd /opt/universal_booking_bot
docker compose logs -f booking-bot
```

### Update after a new release

```bash
bash /opt/universal_booking_bot/update.sh
```

Or manually:

```bash
cd /opt/universal_booking_bot
git pull origin main
docker compose down
docker compose up -d --build
```

### Backup database

```bash
bash /opt/universal_booking_bot/backup.sh
```

Backups are stored in `/opt/universal_booking_bot/backups/`.

### Restore from backup

```bash
cd /opt/universal_booking_bot
docker compose down
cp backups/booking_bot_YYYYMMDD_HHMMSS.db data/booking_bot.db
docker compose up -d
```

### Restart without rebuild

```bash
cd /opt/universal_booking_bot
docker compose restart
```

## Security checklist

- [ ] `.env` not in git
- [ ] `data/*.db` not in git
- [ ] Firewall: only SSH (+ optional reverse proxy) open; bot uses outbound Telegram API
- [ ] Google refresh token stored only in `.env` on server
- [ ] Regular backups via cron, e.g. `0 3 * * * /opt/universal_booking_bot/backup.sh`

## Troubleshooting

| Issue | Action |
|-------|--------|
| Bot not responding | `docker compose ps`, check logs |
| Database locked | Ensure single container instance |
| Google Calendar fails | `docker compose exec booking-bot python scripts/check_google_calendar.py` |
| After `.env` change | `docker compose down && docker compose up -d --build` |

## Manual install (no curl pipe)

```bash
sudo mkdir -p /opt/universal_booking_bot
sudo chown $USER:$USER /opt/universal_booking_bot
git clone https://github.com/PsychicBAM/universal_booking_bot.git /opt/universal_booking_bot
cd /opt/universal_booking_bot
cp .env.example .env
# edit .env
docker compose up -d --build
```
