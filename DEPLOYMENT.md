# Deployment Guide

🇷🇺 **Russian:** [DEPLOYMENT_RU.md](DEPLOYMENT_RU.md)

## Repository

- **GitHub:** https://github.com/PsychicBAM/universal_booking_bot
- **Install script:** https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh

```bash
bash <(curl -Ls https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh)
```

---

## Requirements

| Requirement | Notes |
|-------------|-------|
| Linux VPS | Ubuntu 22.04+ / Debian 11+ recommended |
| Docker | Engine 20.10+ |
| Docker Compose | v2 plugin (`docker compose`) or standalone |
| git | For clone and updates |
| Outbound HTTPS | Telegram API + optional Google APIs |

Minimum: 1 vCPU, 512 MB RAM, 5 GB disk (SQLite + Docker images).

---

## Recommended install

```bash
bash <(curl -Ls https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh)
```

The script:

1. Clones `https://github.com/PsychicBAM/universal_booking_bot.git` → `/opt/universal_booking_bot`
2. Creates `data/` and `backups/`
3. Copies `.env.example` → `.env` if missing
4. Runs `docker compose up -d --build` when `.env` has a real `BOT_TOKEN`

---

## Install directory

```
/opt/universal_booking_bot
```

| Script | Purpose |
|--------|---------|
| `install.sh` | First-time clone + Docker build |
| `update.sh` | `git pull` + rebuild |
| `backup.sh` | DB → `backups/booking_bot_YYYYMMDD_HHMMSS.db` |
| `uninstall.sh` | Stop containers; optional delete |

---

## Manual install

```bash
sudo mkdir -p /opt/universal_booking_bot
sudo chown $USER:$USER /opt/universal_booking_bot
git clone https://github.com/PsychicBAM/universal_booking_bot.git /opt/universal_booking_bot
cd /opt/universal_booking_bot
cp .env.example .env
nano .env   # BOT_TOKEN, ADMIN_IDS
docker compose up -d --build
```

---

## Configuration (`.env`)

**Required:**

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | @BotFather |
| `ADMIN_IDS` | Telegram user ID(s), comma-separated |

**Common optional:**

| Variable | Default | Description |
|----------|---------|-------------|
| `TIMEZONE` | `Europe/Moscow` | Local timezone |
| `DEFAULT_LANGUAGE` | `ru` | Bot default language |
| `CONTACT_ADMIN_USERNAME` | empty | Shown to clients |
| `CANCEL_BOOKING_HOURS_BEFORE` | `2` | Cancel/reschedule window |
| `REMINDERS_ENABLED` | `true` | Reminder job |

**Google Calendar (optional):**

| Variable | Description |
|----------|-------------|
| `GOOGLE_CALENDAR_ENABLED` | `false` by default |
| `GOOGLE_CLIENT_ID` | OAuth client |
| `GOOGLE_CLIENT_SECRET` | OAuth secret |
| `GOOGLE_REDIRECT_URI` | `https://developers.google.com/oauthplayground` |
| `GOOGLE_REFRESH_TOKEN` | Long-lived token (not access token) |
| `GOOGLE_CALENDAR_ID` | `primary` or calendar ID |

**Full Google Calendar guide:** [README.md — Google Calendar setup](README.md#google-calendar-setup) · [README_RU.md](README_RU.md#настройка-google-calendar)

---

## Operations

### View logs

```bash
cd /opt/universal_booking_bot
docker compose logs -f booking-bot
```

### Update (`update.sh`)

```bash
bash /opt/universal_booking_bot/update.sh
```

Equivalent manual steps:

```bash
cd /opt/universal_booking_bot
git pull origin main
docker compose down
docker compose up -d --build
```

### Backup (`backup.sh`)

```bash
bash /opt/universal_booking_bot/backup.sh
```

Output: `/opt/universal_booking_bot/backups/booking_bot_*.db`

**Cron example:**

```cron
0 3 * * * /opt/universal_booking_bot/backup.sh
```

### Restore

```bash
cd /opt/universal_booking_bot
docker compose down
cp backups/booking_bot_YYYYMMDD_HHMMSS.db data/booking_bot.db
docker compose up -d
```

### Uninstall (`uninstall.sh`)

```bash
bash /opt/universal_booking_bot/uninstall.sh
```

Interactive: stops containers, optionally deletes `/opt/universal_booking_bot`.

### After `.env` changes

```bash
docker compose down && docker compose up -d --build
```

---

## Security checklist

- [ ] `.env` not in git
- [ ] `data/*.db` not in git
- [ ] Never share `BOT_TOKEN`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`
- [ ] Firewall: SSH only; bot needs outbound HTTPS
- [ ] Regular backups

---

## Troubleshooting

| Issue | Action |
|-------|--------|
| Bot not responding | `docker compose ps`; check logs |
| DB locked | Single container instance only |
| Google Calendar | [README troubleshooting](README.md#google-calendar-troubleshooting); `python scripts/check_google_calendar.py` |
| Placeholder `.env` | Replace `{{BOT_TOKEN}}` and restart |

---

## Related docs

- [QUICK_START.md](QUICK_START.md)
- [README.md](README.md)
- [NOTES.md](NOTES.md)
