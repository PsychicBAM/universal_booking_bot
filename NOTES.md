# Implementation Notes — Universal Booking Bot

🇷🇺 **Russian:** [NOTES_RU.md](NOTES_RU.md)

**Repository:** https://github.com/PsychicBAM/universal_booking_bot

## MVP status

Core flows implemented and stabilized. Run checklists in [README.md](README.md) before production.

## Feature list

### Client
- Booking: service → media card → (location) → date → time → name → phone → confirm
- Fixed service locations + optional client address/comment
- My bookings: reschedule, change location/address/comment, cancel
- RU/EN language switch

### Admin
- Services CRUD, archive/restore, duration/buffer presets
- Service locations (fixed places per service)
- Media: 5 photos, 1 video, cover, client visibility
- Working hours, unavailable dates
- Bookings: confirm, cancel, message client
- Bot settings: auto_confirm, reminders, contact, Google Calendar toggle + test

### Platform
- Availability: WH + unavailable + bookings + buffer + Google freebusy
- Reminders: client ×2 + admin, test mode
- SQLite additive migrations (data preserved)
- Docker + persistent volume
- Google Calendar optional (`GOOGLE_CALENDAR_ENABLED=false` default)

## Google Calendar (technical)

- Effective sync = env `GOOGLE_CALENDAR_ENABLED=true` **AND** admin DB toggle
- `CalendarService.update_event` — patch or recreate on 404
- Setup guide: [README.md#google-calendar-setup](README.md#google-calendar-setup)
- Troubleshooting (redirect_uri_mismatch, 403 test users, invalid_grant, etc.): same README section

## How to run

```bash
docker compose up -d --build
docker compose logs -f booking-bot
```

Server: `/opt/universal_booking_bot` — see [DEPLOYMENT.md](DEPLOYMENT.md).

## Security

Never commit: `.env`, `BOT_TOKEN`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`, `data/*.db`.

## Known limitations

1. No Alembic — SQLite additive migrations only
2. Manual Google OAuth (refresh token via Playground)
3. Pagination: 14 dates, 20 bookings
4. Rare concurrent double-book race at confirm
5. Calendar event language follows `DEFAULT_LANGUAGE` in `.env`

## Next improvements

- Alembic + PostgreSQL
- In-bot Google OAuth
- Web admin panel
- Payment integration
- Export bookings CSV
