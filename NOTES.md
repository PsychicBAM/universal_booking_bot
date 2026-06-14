# Implementation Notes — Universal Booking Bot

## MVP status: ready for first real user testing

Core flows are implemented and stabilized. Run the manual checklist in README.md before production use.

## Feature list (complete)

### Client
- Booking: service → connected media card → date → time → name → phone → confirm
- Address + comment when service requires location
- My bookings: view detail, reschedule, change location/address/comment, cancel
- Reschedule uses same availability engine; excludes current booking from slot conflicts
- Ownership + time window enforced on all edits
- Cancel (reply + inline) returns to main menu; cancel during edit returns to booking detail

### Admin
- Services: create, edit, enable/disable, archive/restore/permanent delete
- Duration + buffer preset buttons + manual input
- Client address toggle per service
- Media: 5 photos, 1 video, cover, preview, client visibility toggle
- Working hours (button UI, presets, manual)
- Unavailable dates (full day + time ranges, presets, list/delete)
- Bookings: view, confirm, cancel, message client
- Bot settings (button UI): auto_confirm, reminders, contact, language, Google Calendar
- Calendar settings screen (also via Bot settings → 📅 Google Calendar)

### Platform
- Availability: working hours, unavailable, bookings, buffer, Google busy times
- Reminders: client ×2 + admin, test mode, duplicate prevention
- SQLite + additive migrations (data preserved)
- Docker + persistent volume
- Google Calendar optional (disabled by default; see README)

## Final stabilization pass (fixes)

| Issue | Fix |
|-------|-----|
| Cancel unhandled after media booking | Middleware no longer clears FSM on Cancel; cancel handler handles empty state |
| Disconnected photo + service card | `send_service_card_with_media`: photo + full caption + buttons in one message |
| Stale inline buttons infinite spinner | Fallback handlers in `common.py` (registered last) |
| `edit_text` on photo messages | Shared `edit_or_send()` helper |
| `svc:arch:*` crash on client list | Client handler uses `^svc:\d+$` regexp |
| Archived/inactive service from stale card | `is_service_bookable()` check |
| HTML in booking confirm summary | User input escaped |
| Admin cancel booking crash | try/except + access_denied answer |
| Client race on first booking | `IntegrityError` retry in `get_or_create` |
| Booking archived services | `archived_at` check in `create_booking` |

## How to run

```bash
docker compose down
docker compose up -d --build
docker compose logs -f booking-bot
```

Local: `python -m app.main` after `.env` setup.

## Test flows (priority order)

1. **Full booking** — admin service + WH → client books → admin sees booking
2. **Media card** — photo with caption + buttons; Book works; Cancel at each step
3. **Buffer** — 60 min service + 30 buffer → verify slot gap after booking
4. **Unavailable** — block tomorrow → hidden; block 12–15 → slots removed
5. **Reminders** — test mode, booking 6–10 min ahead
6. **Archive** — archived service hidden from clients; restore works
7. **Language** — RU/EN switch on all main screens

## Google Calendar integration

**Status:** Optional module — audited and stabilized.

### Architecture

- `CalendarService` — lazy Google API imports; no crash if packages missing when disabled
- Effective sync = `GOOGLE_CALENDAR_ENABLED=true` (env) **AND** admin DB toggle
- Credentials from `.env` or `calendar_settings.google_refresh_token`
- `AvailabilityService._collect_blocked_ranges` adds Google freebusy as extra layer (does not replace local DB logic)
- `BookingService._sync_calendar` on confirm; `_update_calendar` on client edits; `delete_event` on cancel
- `CalendarService.update_event` patches start/end/location/description; recreates on 404

### Admin UX

Bot settings → **📅 Google Calendar**:
- Status, calendar ID, sync on/off
- Toggle sync (when env allows)
- **Test connection** — reports disabled / missing credentials / success / API errors (no secrets shown)

Legacy admin menu button **📆 Calendar settings** opens the same screen.

### OAuth limitation (MVP)

Google Calendar is **optional** and disabled by default. The live OAuth refresh token must be configured **manually** in `.env` (see README — Google Calendar setup). There is no in-bot OAuth flow yet; **in-bot OAuth is a planned future improvement**.

Required OAuth scope: `https://www.googleapis.com/auth/calendar`

Setup guide: see README.md → **Google Calendar setup** (Google Cloud project, OAuth client, OAuth Playground refresh token).

### Error handling

| Error | Behavior |
|-------|----------|
| Missing credentials | Log warning; sync skipped; booking continues |
| Invalid/expired token | Logged; test connection shows message |
| Permission denied | Logged; test connection shows message |
| Event not found on delete | Warning only; booking cancel continues |
| Network/API errors | Logged; returns empty busy / no event id |

### Check script

`python scripts/check_google_calendar.py` — config, imports, credentials, optional connection test.

## Known limitations (post-MVP)

1. Alembic migrations for production PostgreSQL
2. Google OAuth in-bot flow (refresh token is manual via .env)
3. Pagination for dates/slots/bookings
4. Phone format validation
5. Min booking notice (e.g. 2 hours ahead)
6. Reminder retry on Telegram failure
7. DB-level double-booking lock (TOCTOU race on concurrent confirm)
8. Admin callback guards without `callback.answer()` on old messages (non-admin spinner)
9. Calendar event language follows `DEFAULT_LANGUAGE` in .env (not per-client)
10. `unav:next7` includes today

## Next recommended improvements

1. Alembic + PostgreSQL for multi-tenant production
2. Web admin panel
3. Service categories / staff calendars
4. Payment prepay (YooKassa/Stripe)
5. Reminder template editor in admin UI
6. Export bookings CSV

## Commercial deployment

- Per client: unique bot token, `.env`, database volume
- White-label via admin-configured services and contact username
- Google Calendar as optional paid setup step

## Template source

Built from `E:\bot_templates\simple_telegram_bot` patterns with layered handlers → services → repositories.
