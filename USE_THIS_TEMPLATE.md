# Use This Template (Cursor Instructions)

When the user asks to create a new client bot from **universal_booking_bot**:

## Source repository

- https://github.com/PsychicBAM/universal_booking_bot

## Rules

1. **Do not modify** the GitHub template repo unless explicitly asked.
2. Copy or generate into a **new folder** under `E:\generated_bots\`, for example:
   - `E:\generated_bots\salon_booking_bot`
3. Never overwrite an existing client project unless the user explicitly asks.

## Steps for Cursor

1. **Copy** the project (or clone from GitHub) to `E:\generated_bots\<new_project_name>\`

2. **Create `.env`** from `.env.example`:
   ```bash
   copy .env.example .env
   ```

3. **Fill required values** in `.env`:
   - `BOT_TOKEN` — from @BotFather (replace `{{BOT_TOKEN}}`)
   - `ADMIN_IDS` — Telegram user ID(s), comma-separated (replace `{{ADMIN_IDS}}`)
   - Optional: `TIMEZONE`, `DEFAULT_LANGUAGE`, `CONTACT_ADMIN_USERNAME`

4. **Optional — Google Calendar** (see README.md):
   - Set `GOOGLE_CALENDAR_ENABLED=true`
   - Fill `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`, `GOOGLE_REDIRECT_URI`

5. Ensure `data/` folder exists (empty — database is created on first run)

6. **Build and run**:
   ```bash
   docker compose down
   docker compose up -d --build
   docker compose logs -f booking-bot
   ```

7. Do **not** copy `.env`, `data/*.db`, or secrets from other projects.

## Server deployment (client VPS)

```bash
bash <(curl -Ls https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh)
```

Install path: `/opt/universal_booking_bot`

See [DEPLOYMENT.md](DEPLOYMENT.md) for update, backup, and logs.

## What to customize per client

| Item | Where |
|------|--------|
| Bot token & admins | `.env` |
| Contact username | `.env` or admin Bot settings |
| Services, schedule, media, locations | Admin panel in Telegram |
| Google Calendar | `.env` + Bot settings → 📅 Google Calendar |
| Branding text | Service names/descriptions in admin (not in code) |

## Architecture — do not rewrite unless necessary

- `app/bot/handlers/` — Telegram handlers
- `app/services/` — business logic (booking, availability, media, reminders, calendar)
- `app/repositories/` — database access
- `app/models/` — SQLAlchemy models

Extend via admin settings and new services — avoid forking core booking logic for each client.

See [NOTES.md](NOTES.md) for implementation details.
