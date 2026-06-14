# Быстрый старт

🇬🇧 **English:** [QUICK_START.md](QUICK_START.md)

**Репозиторий:** https://github.com/PsychicBAM/universal_booking_bot

---

## Чеклист

1. **Создать бота в BotFather** → получить `BOT_TOKEN`
2. **Получить Telegram ID админа** (например [@userinfobot](https://t.me/userinfobot)) → `ADMIN_IDS`
3. **Запустить install.sh** на Linux-сервере с Docker и git:

   ```bash
   bash <(curl -Ls https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh)
   ```

4. Отредактировать `/opt/universal_booking_bot/.env` — `BOT_TOKEN`, `ADMIN_IDS`
5. Запустить бота:

   ```bash
   cd /opt/universal_booking_bot
   docker compose up -d --build
   ```

6. Открыть бота → **`/admin`**
7. **Создать первую услугу**
8. **Добавить фото** (по желанию), выбрать обложку
9. **Настроить рабочее время**
10. **Проверить запись** клиентом (дата → время → имя → телефон → подтверждение)
11. При необходимости — **[подключить Google Calendar](README_RU.md#настройка-google-calendar)**

---

## Установка одной командой

```bash
bash <(curl -Ls https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh)
```

Путь: `/opt/universal_booking_bot`

---

## Локально / Windows

```bash
git clone https://github.com/PsychicBAM/universal_booking_bot.git
cd universal_booking_bot
copy .env.example .env
docker compose up -d --build
docker compose logs -f booking-bot
```

---

## Полезные команды

| Действие | Команда |
|----------|---------|
| Логи | `cd /opt/universal_booking_bot && docker compose logs -f booking-bot` |
| Обновление | `bash /opt/universal_booking_bot/update.sh` |
| Бэкап | `bash /opt/universal_booking_bot/backup.sh` |
| Перезапуск | `cd /opt/universal_booking_bot && docker compose restart` |

---

## Безопасность

Не публиковать: `.env`, `BOT_TOKEN`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`, файлы базы данных.

---

## Документация

- [README_RU.md](README_RU.md) — полное руководство + Google Calendar
- [DEPLOYMENT_RU.md](DEPLOYMENT_RU.md) — развёртывание на сервере
