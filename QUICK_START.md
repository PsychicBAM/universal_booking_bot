# Quick Start

🇷🇺 **Russian:** [QUICK_START_RU.md](QUICK_START_RU.md)

**Repository:** https://github.com/PsychicBAM/universal_booking_bot

---

## Checklist

1. Create a bot in [@BotFather](https://t.me/BotFather) → get **BOT_TOKEN**
2. Get your Telegram user ID (e.g. [@userinfobot](https://t.me/userinfobot)) → **ADMIN_IDS**
3. On a Linux server with Docker + git, run:

   ```bash
   bash <(curl -Ls https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh)
   ```

4. Edit `/opt/universal_booking_bot/.env` — set `BOT_TOKEN` and `ADMIN_IDS`
5. Start (if install paused on placeholders):

   ```bash
   cd /opt/universal_booking_bot
   docker compose up -d --build
   ```

6. Telegram → `/admin` → create first **service**
7. Add **photos** (optional) → set cover
8. Set **working hours**
9. Test **client booking** end-to-end
10. Optional: [Google Calendar setup](README.md#google-calendar-setup) in README

---

## One-line install

```bash
bash <(curl -Ls https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh)
```

Install path: `/opt/universal_booking_bot`

---

## Local / Windows (Docker)

```bash
git clone https://github.com/PsychicBAM/universal_booking_bot.git
cd universal_booking_bot
copy .env.example .env   # Windows: copy
docker compose up -d --build
docker compose logs -f booking-bot
```

---

## Useful commands

| Task | Command |
|------|---------|
| View logs | `cd /opt/universal_booking_bot && docker compose logs -f booking-bot` |
| Update | `bash /opt/universal_booking_bot/update.sh` |
| Backup | `bash /opt/universal_booking_bot/backup.sh` |
| Restart | `cd /opt/universal_booking_bot && docker compose restart` |

---

## Security

Never commit or share: `.env`, `BOT_TOKEN`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`, database files.

---

## More documentation

- [README.md](README.md) — full guide + Google Calendar
- [DEPLOYMENT.md](DEPLOYMENT.md) — server operations
