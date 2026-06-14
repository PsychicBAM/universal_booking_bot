# Руководство по развёртыванию

🇬🇧 **English:** [DEPLOYMENT.md](DEPLOYMENT.md)

## Репозиторий

- **GitHub:** https://github.com/PsychicBAM/universal_booking_bot
- **Скрипт установки:** https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh

```bash
bash <(curl -Ls https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh)
```

---

## Требования

| Требование | Примечание |
|------------|------------|
| Linux VPS | Ubuntu 22.04+ / Debian 11+ |
| Docker | Engine 20.10+ |
| Docker Compose | плагин `docker compose` |
| git | клонирование и обновления |
| Исходящий HTTPS | Telegram API + опционально Google |

Минимум: 1 vCPU, 512 MB RAM, 5 GB диск.

---

## Установка одной командой

```bash
bash <(curl -Ls https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh)
```

Скрипт:

1. Клонирует репозиторий в `/opt/universal_booking_bot`
2. Создаёт `data/` и `backups/`
3. Копирует `.env.example` → `.env`
4. Запускает Docker, если в `.env` указан реальный `BOT_TOKEN`

---

## Каталог установки

```
/opt/universal_booking_bot
```

| Скрипт | Назначение |
|--------|------------|
| `install.sh` | Первая установка |
| `update.sh` | Обновление с GitHub |
| `backup.sh` | Резервная копия БД |
| `uninstall.sh` | Остановка и удаление |

---

## Ручная установка

```bash
sudo mkdir -p /opt/universal_booking_bot
sudo chown $USER:$USER /opt/universal_booking_bot
git clone https://github.com/PsychicBAM/universal_booking_bot.git /opt/universal_booking_bot
cd /opt/universal_booking_bot
cp .env.example .env
nano .env
docker compose up -d --build
```

---

## Переменные `.env`

**Обязательные:**

- `BOT_TOKEN` — от @BotFather
- `ADMIN_IDS` — Telegram ID админов

**Часто используемые:**

- `TIMEZONE`, `DEFAULT_LANGUAGE`, `CONTACT_ADMIN_USERNAME`
- `CANCEL_BOOKING_HOURS_BEFORE`, `RESCHEDULE_BOOKING_HOURS_BEFORE`
- `REMINDERS_ENABLED`, `CLIENT_REMINDER_*`, `ADMIN_REMINDER_MINUTES`

**Google Calendar (опционально):**

- `GOOGLE_CALENDAR_ENABLED=false` по умолчанию
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI=https://developers.google.com/oauthplayground`
- `GOOGLE_REFRESH_TOKEN` — **Refresh token**, не Access token
- `GOOGLE_CALENDAR_ID=primary`

**Подробная настройка Google Calendar:** [README_RU.md — Настройка Google Calendar](README_RU.md#настройка-google-calendar)

---

## Логи

```bash
cd /opt/universal_booking_bot
docker compose logs -f booking-bot
```

---

## Обновление (`update.sh`)

```bash
bash /opt/universal_booking_bot/update.sh
```

Вручную:

```bash
cd /opt/universal_booking_bot
git pull origin main
docker compose down
docker compose up -d --build
```

---

## Бэкап (`backup.sh`)

```bash
bash /opt/universal_booking_bot/backup.sh
```

Файлы: `/opt/universal_booking_bot/backups/booking_bot_*.db`

Cron:

```cron
0 3 * * * /opt/universal_booking_bot/backup.sh
```

### Восстановление

```bash
cd /opt/universal_booking_bot
docker compose down
cp backups/booking_bot_YYYYMMDD_HHMMSS.db data/booking_bot.db
docker compose up -d
```

---

## Удаление (`uninstall.sh`)

```bash
bash /opt/universal_booking_bot/uninstall.sh
```

---

## Безопасность

**Никогда не публиковать:**

- `.env`
- `BOT_TOKEN`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
- файлы `data/*.db`

---

## Устранение неполадок

| Проблема | Действие |
|----------|----------|
| Бот не отвечает | `docker compose ps`, логи |
| Google Calendar | [README_RU.md — частые ошибки](README_RU.md#частые-ошибки-google-calendar) |
| После смены `.env` | `docker compose down && docker compose up -d --build` |

---

## Связанные документы

- [QUICK_START_RU.md](QUICK_START_RU.md)
- [README_RU.md](README_RU.md)
- [NOTES_RU.md](NOTES_RU.md)
