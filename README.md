# Universal Booking Bot

Telegram booking bot for service providers — lessons, consultations, beauty, medical, and any bookable service.

**Repository:** https://github.com/PsychicBAM/universal_booking_bot

## Server install (Linux)

Requires Docker, Docker Compose, and git:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh)
```

Installs to `/opt/universal_booking_bot`. See [DEPLOYMENT.md](DEPLOYMENT.md) for update, backup, and operations.

## Features

| Area | Capabilities |
|------|----------------|
| **Client** | Book appointments, connected photo/video service cards, address + comment, my bookings, reschedule/edit, cancel, language RU/EN |
| **Admin** | Services CRUD, archive/restore, duration/buffer buttons, media (5 photos + 1 video), working hours, unavailable dates, bookings, bot settings, reminders |
| **Engine** | Availability (WH + blocks + bookings + buffer + Google Calendar), reminders, SQLite migrations, Docker |

## Quick start (Docker)

```bash
git clone https://github.com/PsychicBAM/universal_booking_bot.git
cd universal_booking_bot
copy .env.example .env
# Set BOT_TOKEN and ADMIN_IDS in .env
docker compose down
docker compose up -d --build
docker compose logs -f booking-bot
```

Data persists in `./data/booking_bot.db` (mounted volume).

## Configure `.env`

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | From @BotFather |
| `ADMIN_IDS` | Comma-separated Telegram user IDs |
| `DATABASE_URL` | Default `sqlite+aiosqlite:///data/booking_bot.db` |
| `TIMEZONE` | e.g. `Europe/Moscow` |
| `DEFAULT_LANGUAGE` | `ru` or `en` |
| `DEFAULT_SLOT_STEP_MINUTES` | Slot grid (default 30) |
| `BOOKING_DAYS_AHEAD` | How far clients can book (default 30) |
| `CANCEL_BOOKING_HOURS_BEFORE` | Client cancel window |
| `RESCHEDULE_BOOKING_HOURS_BEFORE` | Client reschedule window (defaults to cancel window if unset) |
| `REMINDERS_ENABLED` | `true` / `false` |
| `CLIENT_REMINDER_1_MINUTES` | Default 1440 (24h) |
| `CLIENT_REMINDER_2_MINUTES` | Default 120 (2h) |
| `ADMIN_REMINDER_MINUTES` | Default 60 |
| `REMINDER_TEST_MODE` | Quick test in minutes |
| `TEST_CLIENT_REMINDER_MINUTES` | Default 5 |
| `TEST_ADMIN_REMINDER_MINUTES` | Default 3 |
| `GOOGLE_CALENDAR_*` | Optional calendar sync — see [Google Calendar setup](#google-calendar-setup) |

## Google Calendar setup

Google Calendar is **optional**. The bot works fully without it.

### Default mode

```env
GOOGLE_CALENDAR_ENABLED=false
```

In this mode:

- the bot works without Google Calendar
- bookings are saved only in the local database
- no Google credentials are required

### Enable Google Calendar

Set these values in `.env`:

```env
GOOGLE_CALENDAR_ENABLED=true
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://developers.google.com/oauthplayground
GOOGLE_REFRESH_TOKEN=your_refresh_token
GOOGLE_CALENDAR_ID=primary
```

### 1. Create Google Cloud project

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project, for example: **Booking Bot**.
3. Enable **Google Calendar API** for this project.

### 2. Configure OAuth consent screen

1. Open **Google Auth Platform** → **OAuth consent screen**.
2. Choose **External** or **Internal** depending on account type.
3. Fill app name, support email, and developer contact email.
4. Add your Google account as a **test user** if the app is in testing mode.

### 3. Create OAuth client

1. Open **Credentials** → **OAuth clients**.
2. Create a new OAuth client.
3. For simple testing, choose **Web application** or **Desktop app**.
4. If using OAuth 2.0 Playground, add this redirect URI:

   `https://developers.google.com/oauthplayground`

5. Save the client.
6. Copy:
   - **Client ID**
   - **Client Secret**

Use them in:

```env
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

### 4. Get refresh token using OAuth 2.0 Playground

1. Open [Google OAuth 2.0 Playground](https://developers.google.com/oauthplayground).
2. Click the **settings** icon (gear).
3. Enable **Use your own OAuth credentials**.
4. Paste your **Client ID** and **Client Secret**.
5. Select or enter this scope:

   `https://www.googleapis.com/auth/calendar`

6. Click **Authorize APIs**.
7. Sign in with the Google account that owns the calendar.
8. Allow access.
9. Click **Exchange authorization code for tokens**.
10. Copy the **Refresh token**.

Use it in:

```env
GOOGLE_REFRESH_TOKEN=
```

### 5. Calendar ID

For the main calendar, use:

```env
GOOGLE_CALENDAR_ID=primary
```

If using a separate calendar:

1. Open [Google Calendar](https://calendar.google.com/).
2. Open calendar **Settings**.
3. Find **Calendar ID**.
4. Put it into `GOOGLE_CALENDAR_ID`.

### 6. Restart the bot

After editing `.env`, restart Docker:

```bash
docker compose down
docker compose up -d --build
docker compose logs -f booking-bot
```

### 7. Test connection in Telegram

In Telegram:

1. `/admin`
2. **⚙️ Bot settings**
3. **📅 Google Calendar**
4. **📋 Test connection**

If successful, enable Google Calendar sync from the same screen.

### 8. What Google Calendar does

When enabled and connected:

- busy Google Calendar events hide unavailable slots from clients
- confirmed bookings create Google Calendar events
- cancelled bookings delete related Google Calendar events
- when a client reschedules or edits location/address/comment, the existing event is updated (or recreated if missing)
- event location priority: client address → fixed service location address → empty
- client name, phone, service, locations, address, comment, and booking ID are added to the event description

### Client booking edits

From **My bookings**, clients can open a booking and:

- **Reschedule** — pick a new date/time (same availability rules; current booking is excluded from conflict checks)
- **Change service location** — if the service has active fixed locations
- **Change client address / comment** — if the service requires client address

Limitations:

- Only pending/confirmed bookings can be edited
- Reschedule is blocked within `RESCHEDULE_BOOKING_HOURS_BEFORE` (defaults to `CANCEL_BOOKING_HOURS_BEFORE`)
- Cancel during an edit flow returns to the booking detail — the booking is not deleted
- Google Calendar sync failures do not roll back local booking changes

### 9. Safety notes

Never share:

- `BOT_TOKEN`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

Do not commit `.env` to Git. Only `.env.example` should be in the template.

### 10. Troubleshooting

**Problem:** Google Calendar is enabled but connection fails.

**Check:**

- `GOOGLE_CLIENT_ID` is correct
- `GOOGLE_CLIENT_SECRET` is correct
- `GOOGLE_REFRESH_TOKEN` is not empty
- Google Calendar API is enabled
- OAuth consent screen has the correct test user
- `GOOGLE_CALENDAR_ID` is correct
- redirect URI matches OAuth client settings

**Problem:** Bot works but calendar events are not created.

**Check:**

- `GOOGLE_CALENDAR_ENABLED=true`
- Google Calendar is enabled in Bot settings
- Test connection succeeds
- booking is **confirmed**, not pending

**Problem:** Busy times are not hidden.

**Check:**

- calendar event exists in the same calendar ID
- event time zone is correct
- bot `TIMEZONE` matches expected local timezone
- Test connection succeeds

### Check script

```bash
python scripts/check_google_calendar.py
```

Or inside Docker:

```bash
docker compose exec booking-bot python scripts/check_google_calendar.py
```

## Manual test checklist

### Admin service flow
1. `/admin` → Services → Add service (name, description, duration, buffer, price)
2. Toggle client address, add photos/video, set cover, preview
3. Toggle media display OFF/ON, edit duration/buffer
4. Archive → restore service

### Client booking with media
1. `/start` → Book → open service (connected photo card + buttons)
2. Book → date → time → name → phone → (address/comment) → confirm
3. Press **Cancel** at each step → main menu, no unhandled updates

### Working hours & unavailable
- Set Mon 10:00–19:00, Sat off, presets
- Block tomorrow / time range → verify client slots update

### Buffer
- Service 60 min + 30 min buffer → book 09:00 → 10:00 slot hidden, 10:30 available

### Reminders (test mode)
- Bot settings → enable test mode, 5 min client / 3 min admin
- Confirmed booking 6–10 min ahead → both receive reminders once

### Language
- Switch RU/EN — UI changes, service names stay as entered

### Security
- Client cannot cancel others' bookings
- Archived/inactive services hidden from client list
- Non-admin gets access denied on admin actions

### Logs
```bash
docker compose logs -f booking-bot
```
Expect no `Update is not handled`, tracebacks, or IntegrityError during normal use.

## First-client deployment checklist

1. Copy project folder for new client
2. New `BOT_TOKEN`, `ADMIN_IDS`, `CONTACT_ADMIN_USERNAME` in `.env`
3. Fresh `data/` volume or empty database
4. `docker compose up -d --build`
5. Admin: create services, working hours, unavailable dates
6. Bot settings: `auto_confirm`, reminders, contact username
7. Test full client booking end-to-end
8. Optional: [Google Calendar setup](#google-calendar-setup)

## Database migrations

Startup runs `create_all` + safe SQLite `ALTER TABLE`. **Existing data is never deleted.**

## Known limitations

- No Alembic — additive SQLite migrations only
- Google OAuth manual setup — refresh token via OAuth Playground (see Google Calendar setup); in-bot OAuth planned for future
- Media via Telegram `file_id` only
- Pagination: 14 dates, 20 bookings per screen
- Buffer may extend past closing for last slot (overlap blocking only)
- Concurrent double-book rare race (re-check at confirm, not DB lock)

See [NOTES.md](NOTES.md) for implementation details and roadmap.

## Server operations

| Task | Command |
|------|---------|
| View logs | `cd /opt/universal_booking_bot && docker compose logs -f booking-bot` |
| Update | `bash /opt/universal_booking_bot/update.sh` |
| Backup DB | `bash /opt/universal_booking_bot/backup.sh` |

Quick reference: [QUICK_START.md](QUICK_START.md) · Full guide: [DEPLOYMENT.md](DEPLOYMENT.md)
