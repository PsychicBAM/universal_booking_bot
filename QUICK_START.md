# Quick Start

## One-line install (Linux server)

Requires Docker, Docker Compose, and git.

```bash
bash <(curl -Ls https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh)
```

Install path: `/opt/universal_booking_bot`

After install, edit `/opt/universal_booking_bot/.env`:

- `BOT_TOKEN` — from @BotFather
- `ADMIN_IDS` — your Telegram user ID(s)

Then start (if install stopped at placeholder warning):

```bash
cd /opt/universal_booking_bot
docker compose up -d --build
docker compose logs -f booking-bot
```

## Local / Windows (Docker)

```bash
git clone https://github.com/PsychicBAM/universal_booking_bot.git
cd universal_booking_bot
copy .env.example .env   # Windows
# or: cp .env.example .env
# Edit .env — set BOT_TOKEN and ADMIN_IDS
docker compose up -d --build
docker compose logs -f booking-bot
```

## First steps in Telegram

1. Open your bot → `/start`
2. Send `/admin` from an admin account
3. Create a service, set working hours, test a client booking

See [README.md](README.md) for Google Calendar, reminders, and full checklist.

## Useful commands

| Task | Command |
|------|---------|
| View logs | `cd /opt/universal_booking_bot && docker compose logs -f booking-bot` |
| Update bot | `bash /opt/universal_booking_bot/update.sh` |
| Backup DB | `bash /opt/universal_booking_bot/backup.sh` |
| Restart | `cd /opt/universal_booking_bot && docker compose restart` |

Repository: https://github.com/PsychicBAM/universal_booking_bot
