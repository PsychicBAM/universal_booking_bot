# Universal Booking Bot

🇷🇺 **Russian documentation:** [README_RU.md](README_RU.md)

Telegram booking bot for service providers — lessons, consultations, beauty, medical, and any bookable service.

**Repository:** https://github.com/PsychicBAM/universal_booking_bot

---

## Overview

Clients book appointments in Telegram. Admins manage services, schedule, media, fixed locations, bookings, reminders, and optional Google Calendar sync — all from the bot.

| Area | Capabilities |
|------|----------------|
| **Client** | Book appointments, service photo/video cards, fixed locations, client address + comment, my bookings, reschedule/edit, cancel, contact admin via bot, RU/EN |
| **Admin** | Services CRUD, archive/restore, duration/buffer, media (5 photos + 1 video), service locations, working hours, unavailable dates, bookings, bot settings (custom /start text + photo), reminders |
| **Engine** | Availability (working hours + blocks + bookings + buffer + Google Calendar busy times), SQLite migrations, Docker |

---

## One-command install (Linux server)

Use of this installer is allowed only for authorized deployments.

Requires **Docker**, **Docker Compose**, and **git**:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh)
```

Install path: `/opt/universal_booking_bot`

After install, edit `.env` (`BOT_TOKEN`, `ADMIN_IDS`), then:

```bash
cd /opt/universal_booking_bot
docker compose up -d --build
docker compose logs -f booking-bot
```

**More:** [QUICK_START.md](QUICK_START.md) · [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Docker run (local / manual clone)

```bash
git clone https://github.com/PsychicBAM/universal_booking_bot.git
cd universal_booking_bot
cp .env.example .env    # Windows: copy .env.example .env
# Edit .env — set BOT_TOKEN and ADMIN_IDS
docker compose up -d --build
docker compose logs -f booking-bot
```

Database: `./data/booking_bot.db` (Docker volume).

---

## Environment variables

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | From @BotFather (**required**) |
| `ADMIN_IDS` | Comma-separated Telegram user IDs (**required**) |
| `DATABASE_URL` | Default `sqlite+aiosqlite:///data/booking_bot.db` |
| `TIMEZONE` | e.g. `Europe/Moscow` |
| `DEFAULT_LANGUAGE` | `ru` or `en` |
| `DEFAULT_SLOT_STEP_MINUTES` | Slot grid (default 30) |
| `BOOKING_DAYS_AHEAD` | How far clients can book (default 30) |
| `CANCEL_BOOKING_HOURS_BEFORE` | Client cancel window (default 2) |
| `RESCHEDULE_BOOKING_HOURS_BEFORE` | Reschedule window (defaults to cancel window) |
| `CONTACT_ADMIN_USERNAME` | Optional @username shown to clients |
| `REMINDERS_ENABLED` | `true` / `false` |
| `CLIENT_REMINDER_1_MINUTES` | Default 1440 (24h) |
| `CLIENT_REMINDER_2_MINUTES` | Default 120 (2h) |
| `ADMIN_REMINDER_MINUTES` | Default 60 |
| `GOOGLE_CALENDAR_*` | Optional — see [Google Calendar setup](#google-calendar-setup) below |

Copy from `.env.example`. **Never commit `.env` to git.**

---

## Admin setup (first launch)

1. Open bot → `/start`
2. Send `/admin` from an admin Telegram account (`ADMIN_IDS`)
3. **Services** — create service (name, description, duration, buffer, price)
4. **Service locations** (optional) — fixed places client chooses at booking
5. **Media** — add photos/video, set cover, toggle client visibility
6. **Working hours** — set days and times clients can book
7. **Unavailable dates** — block full days or time ranges
8. **Bot settings** — auto-confirm, reminders, contact username, language, **👋 Start screen** (custom RU/EN `/start` text and optional photo), Google Calendar
9. Test a full client booking end-to-end

---

## Custom /start screen

Admins can customize the welcome screen without code changes:

1. `/admin` → **⚙️ Bot settings** → **👋 Start screen**
2. Edit RU/EN text separately (max 1000 characters — fits under a photo caption)
3. Upload separate RU and EN photos (stored as Telegram `file_id` only — no local media files)
4. Enable/disable each language photo independently, preview RU/EN separately, or reset to defaults

When a user sends `/start`, they see text and photo for their language (RU or EN).

### Available languages

In **⚙️ Bot settings → 🌐 Available languages**, the admin can choose:

- **Russian only** — hides the 🌐 Language button; all users see Russian UI and RU start screen settings only
- **English only** — hides language switching; EN start screen settings only
- **Russian + English** — language button appears; users can switch; both RU and EN start screen controls are shown

Stored RU/EN start screen content is never deleted when a language is hidden. Optional `.env` default: `ENABLED_LANGUAGES=ru,en`.

**Backward compatibility:** if only the legacy `start_photo_file_id` is set (old single-photo setup), it is used as a fallback when the language-specific photo is missing and legacy photo is enabled.

---

## Contact admin (in-bot support)

Clients tap **📞 Contact admin** to open a **support menu** with booking-related topics (booking question, reschedule, cancel, payment, other).

- **📝 New request** — choose a topic and send a message
- **📋 My requests** — view past support requests and admin replies
- For reschedule/cancel topics, clients can optionally attach an active booking
- All admins from `ADMIN_IDS` receive requests with **Reply** / **Close** buttons
- Messages are stored in `support_messages` (SQLite) with topic and optional `booking_id`
- Optional `contact_admin_username` in settings is shown as a direct `@username` fallback on the start screen

Booking-specific **✉️ Message client** in admin booking detail is unchanged.

---

## Google Calendar setup

Google Calendar is **optional**. The bot works fully without it.

### Default mode

```env
GOOGLE_CALENDAR_ENABLED=false
```

When disabled:

- No Google credentials required
- Bookings saved only in local SQLite database
- Availability uses working hours, unavailable dates, and existing bookings only

### Required `.env` values (when enabled)

```env
GOOGLE_CALENDAR_ENABLED=true
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://developers.google.com/oauthplayground
GOOGLE_REFRESH_TOKEN=your_refresh_token
GOOGLE_CALENDAR_ID=primary
```

### Step 1 — Create Google Cloud project

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project (e.g. **Booking Bot**).
3. Enable **Google Calendar API** for this project.

### Step 2 — Configure OAuth consent screen

1. Open **Google Auth Platform** → **OAuth consent screen**.
2. Choose **External** (or **Internal** for Workspace).
3. Fill app name, support email, developer contact.
4. If app is in **Testing** mode: **Audience** → **Test users** → **Add users** → add your Gmail.

### Step 3 — Create OAuth client (Web application)

1. **Credentials** → **Create credentials** → **OAuth client ID**.
2. Application type: **Web application**.
3. Add **Authorized redirect URI** exactly:

   ```
   https://developers.google.com/oauthplayground
   ```

4. Save. Copy **Client ID** and **Client Secret** into `.env`.

### Step 4 — Get Refresh token (OAuth 2.0 Playground)

1. Open [Google OAuth 2.0 Playground](https://developers.google.com/oauthplayground).
2. Click **gear** (settings) → enable **Use your own OAuth credentials**.
3. Paste **Client ID** and **Client Secret**.
4. Scope: `https://www.googleapis.com/auth/calendar`
5. **Authorize APIs** → sign in → allow.
6. **Exchange authorization code for tokens**.
7. Copy **Refresh token** (not Access token) into `.env` as `GOOGLE_REFRESH_TOKEN`.

#### Access token vs Refresh token

| Token | Purpose |
|-------|---------|
| **Access token** | Temporary (~1 hour). Used for API calls. **Do not put in `.env`.** |
| **Refresh token** | Long-lived. Bot uses it to obtain new access tokens. **This goes in `.env`.** |

### Step 5 — Calendar ID

```env
GOOGLE_CALENDAR_ID=primary
```

For a dedicated calendar: Google Calendar → Settings → select calendar → copy **Calendar ID**.

### Step 6 — Restart Docker

```bash
cd /opt/universal_booking_bot   # or your project folder
docker compose down
docker compose up -d --build
docker compose logs -f booking-bot
```

### Step 7 — Enable in Telegram admin settings

1. `/admin` → **⚙️ Bot settings** → **📅 Google Calendar**
2. **📋 Test connection** — must succeed
3. Turn **sync ON** on the same screen

### Step 8 — Verify behavior

| Test | Expected |
|------|----------|
| **Busy slots** | Create a personal event in Google Calendar during working hours → that slot hidden from clients |
| **Event creation** | Confirm a booking → event appears in Google Calendar |
| **Event update** | Client reschedules or edits location/address → event updated |
| **Event deletion** | Cancel booking → Google event removed |

Check script:

```bash
docker compose exec booking-bot python scripts/check_google_calendar.py
```

### What Google Calendar does when enabled

- Google busy times hide unavailable slots
- Confirmed bookings create calendar events
- Cancelled bookings delete events
- Client edits update existing events (or recreate if missing)
- Event location: client address → fixed service location address → empty
- Description includes client, phone, service, datetime, locations, comment, booking ID

### Google Calendar troubleshooting

#### Problem: Error 400: redirect_uri_mismatch

**Reason:** The redirect URI in Google Cloud does not match OAuth Playground.

**Fix:** Create OAuth Client type **Web application** and add **Authorized redirect URI** exactly:

```
https://developers.google.com/oauthplayground
```

---

#### Problem: Access blocked: app has not completed the Google verification process / Error 403: access_denied

**Reason:** The app is in Testing mode and the email is not added to Test users.

**Fix:** Google Auth Platform → **Audience** → **Test users** → **Add users** → add your Gmail.

---

#### Problem: Access token expires

**Explanation:** Access token is temporary and usually expires in about 1 hour. The bot needs **Refresh token** in `.env`, not Access token.

---

#### Problem: No refresh token appears

**Fix:** In OAuth Playground enable **Use your own OAuth credentials**, use **Offline access** if visible, **Force prompt** / **Consent** if available, or revoke old app permission from [Google Account permissions](https://myaccount.google.com/permissions) and authorize again.

---

#### Problem: invalid_grant

**Fix:** Generate a new refresh token and make sure Client ID/Secret are from the **same** Google Cloud project.

---

#### Other checks

| Symptom | Check |
|---------|-------|
| Connection fails | Client ID, Secret, Refresh token; Calendar API enabled; test user added |
| Events not created | `GOOGLE_CALENDAR_ENABLED=true`; sync ON in bot settings; booking **confirmed** |
| Busy times not hidden | Same `GOOGLE_CALENDAR_ID`; `TIMEZONE` matches; event in that calendar |
| Sync errors in logs | Run `check_google_calendar.py`; calendar failures do not block local bookings |

Full Russian guide: [README_RU.md#настройка-google-calendar](README_RU.md#настройка-google-calendar)

---

## Security — never commit or share

- `.env`
- `BOT_TOKEN`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
- `data/*.db` and any database files

Only `.env.example` with placeholders belongs in the repository.

---

## Update and backup (server)

| Task | Command |
|------|---------|
| **Update** | `bash /opt/universal_booking_bot/update.sh` |
| **Backup DB** | `bash /opt/universal_booking_bot/backup.sh` |
| **View logs** | `cd /opt/universal_booking_bot && docker compose logs -f booking-bot` |

Details: [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Documentation index

| English | Russian |
|---------|---------|
| [README.md](README.md) | [README_RU.md](README_RU.md) |
| [QUICK_START.md](QUICK_START.md) | [QUICK_START_RU.md](QUICK_START_RU.md) |
| [DEPLOYMENT.md](DEPLOYMENT.md) | [DEPLOYMENT_RU.md](DEPLOYMENT_RU.md) |
| [NOTES.md](NOTES.md) | [NOTES_RU.md](NOTES_RU.md) |

---

## Known limitations

- No Alembic — additive SQLite migrations only
- Google OAuth manual setup (no in-bot OAuth flow yet)
- Media via Telegram `file_id` only
- Pagination: 14 dates, 20 bookings per screen

See [NOTES.md](NOTES.md) for implementation details.

---

## License

All rights reserved.

This project is proprietary. You may not copy, modify, distribute, sell, or use this software without prior written permission from the copyright holder. See the [LICENSE](LICENSE) file for details.
