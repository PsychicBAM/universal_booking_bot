# E2E Audit Report — Universal Booking Bot

**Date:** 2026-06-26  
**Project:** `E:\generated_bots\universal_booking_bot`  
**Base commit:** `896729e` — *Fix mode-aware client menu and manual attendance button*  
**Branch:** `main` (up to date with `origin/main`)

## Safety checkpoint

Uncommitted work was present before this audit (not overwritten, not pushed):

| File | Area |
|------|------|
| `app/bot/handlers/admin.py` | Unified admin confirm + safe cancel/msg parsing |
| `app/bot/handlers/admin_bookings.py` | Booking detail prefix after confirm |
| `app/bot/handlers/client.py` | New-booking admin notification delegate |
| `app/bot/i18n.py` | Already-confirmed / cannot-confirm strings |
| `app/bot/keyboards/admin_bookings_kb.py` | Notification confirm/cancel keyboard |
| `app/services/admin_bookings_service.py` | `confirm_booking_by_admin`, parsers |
| `app/services/booking_notification_service.py` | New booking + client confirm notify |
| `scripts/check_project.py` | Extended tests + audit integration |

No production database was reset. `.env` was not modified.

## Automated commands

| Command | Result |
|---------|--------|
| `python -m compileall app` | PASS |
| `python scripts/check_project.py` | PASS |
| `python scripts/check_reminders.py` | PASS |
| `python scripts/audit_keyboards.py` | PASS |
| `python scripts/audit_callbacks.py` | PASS (WARN: duplicate exact handlers — see limitations) |
| `python scripts/e2e_full_audit.py` | PASS (12/12 scenarios, temp SQLite) |
| `docker compose up -d --build` | PASS |

## Scenario results (temp DB)

| # | Scenario | Result |
|---|----------|--------|
| 1 | DB migrations / schema columns | PASS |
| 2 | Mode menus (booking / order / both) | PASS |
| 3 | Booking flow: create → notify → confirm → idempotent confirm → cancel | PASS |
| 4 | Order flow: create → accept → progress → complete → decline → messages | PASS |
| 5 | Client identity via `event.from_user.id` | PASS |
| 6 | Reminders disabled smoke + attendance keyboard rules | PASS |
| 7 | Slot overlap / cancel frees slot | PASS |
| 8 | Price mode + service type display | PASS |
| 9 | RU client confirmation notification | PASS |
| 10 | Calendar RefreshError detection + booking survives sync noop | PASS |
| 11 | Admin handler security patterns (`is_admin` / `access_denied`) | PASS |
| 12 | Stale callback parsers (no uncaught `ValueError` on `abc` ids) | PASS |

## Bugs found and fixed

### 1. Unsafe `adm_cancel` / `adm_msg` parsing (real bug)

**Symptom:** Stale callbacks like `adm_cancel:abc` could raise uncaught `ValueError` from `int(...)`.

**Fix:** Added `parse_admin_simple_booking_id()` in `admin_bookings_service.py` and wired `admin_cancel_booking` / `admin_message_client` to return a safe “not found” response instead of crashing.

**Tests:** `check_project.py` tests I–J; `audit_callbacks.py` stale samples; `e2e_full_audit.py` stale parser scenario.

### 2. Double admin confirm (from prior session, verified in this audit)

**Fix already in working tree:** Single `confirm_booking_by_admin()` used by notification and detail confirm; idempotent client notification; notification keyboard with real `adm_confirm` / `adm_cancel` callbacks.

**Verified:** E2E booking flow scenario (one client message, confirmed keyboard with 🔔).

## New audit tooling

| Script | Purpose |
|--------|---------|
| `scripts/e2e_test_env.py` | Isolated SQLite bootstrap (`DATABASE_URL` override) |
| `scripts/e2e_full_audit.py` | Integration scenarios (booking, orders, modes, security) |
| `scripts/audit_keyboards.py` | `callback_data` length ≤ 64 bytes, back-navigation sampling |
| `scripts/audit_callbacks.py` | Required prefix coverage, stale parser safety, unknown fallback |

`check_project.py` now runs `audit_keyboards` + `audit_callbacks` on each CI-style check.

## Coverage notes

**Covered without Telegram API**

- Menu visibility for all three mode combinations (RU labels)
- Booking/order DB state transitions
- Admin notification keyboards
- Confirm idempotency
- Order accept/decline/message history
- Callback parser safety
- Callback_data length audit
- Admin handler permission patterns (source-level)
- Reminder service smoke (disabled config)
- Calendar `invalid_grant` classification

**Not fully automated (manual Telegram smoke recommended)**

- Full client FSM walk-through (date → period → time → phone) button-by-button
- Live reminder delivery at real scheduled windows
- Manual attendance send + client attendance button taps
- Admin UI navigation for every back path (sampled in keyboard audit only)
- Non-admin spoofed callback against running bot middleware
- Google Calendar live sync with real credentials
- Docker log monitoring during real user sessions

## Known limitations

1. **Duplicate exact callback handlers** (`bk:back:dates`, `confirm:yes`, etc.) — multiple routers register the same literal; intentional for stale-session fallbacks. Logged as WARN in `audit_callbacks.py`.
2. **E2E uses temp SQLite** — behavior matches production schema via `init_db()` migrations but not production data volume.
3. **Google Calendar packages** may be absent in dev; sync is scheduled in background — booking persistence verified with sync stubbed.
4. **Handler invocation** — most tests are integration/service/keyboard level; full aiogram dispatcher E2E would need a Telegram test harness.

## Manual smoke checklist (Telegram)

- [ ] A. Client creates booking
- [ ] B. Admin confirms once from notification
- [ ] C. Booking shows confirmed in Admin → Clients → booking
- [ ] D. 🔔 manual attendance button visible
- [ ] E. Client receives manual attendance question (RU)
- [ ] F. Client cancels → admin notified
- [ ] G. Client creates order → admin accepts
- [ ] H. Client/admin order message thread
- [ ] I. Back buttons from major screens
- [ ] J. Non-admin cannot execute admin callbacks

## Files changed in this audit

- `app/services/admin_bookings_service.py` — `parse_admin_simple_booking_id`
- `app/bot/handlers/admin.py` — safe cancel/msg parsing
- `scripts/e2e_test_env.py` (new)
- `scripts/e2e_full_audit.py` (new)
- `scripts/audit_keyboards.py` (new)
- `scripts/audit_callbacks.py` (new)
- `scripts/check_project.py` — audit integration + parser tests
- `E2E_AUDIT_REPORT.md` (this file)

Plus uncommitted booking-confirm unification files listed in the checkpoint table.
