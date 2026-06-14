# Заметки по реализации — Universal Booking Bot

🇬🇧 **English:** [NOTES.md](NOTES.md)

**Репозиторий:** https://github.com/PsychicBAM/universal_booking_bot

## Статус MVP

Основные сценарии реализованы. Перед продакшеном — чеклисты в [README_RU.md](README_RU.md).

## Список функций

### Клиент
- Запись: услуга → медиа → (место) → дата → время → имя → телефон → подтверждение
- Места проведения + опциональный адрес/комментарий клиента
- Мои записи: перенос, смена места/адреса/комментария, отмена
- Языки RU/EN

### Админ
- Услуги: CRUD, архив, длительность/буфер
- Места проведения услуги
- Медиа: 5 фото, 1 видео, обложка
- Рабочее время, недоступные даты
- Записи: подтверждение, отмена, сообщение клиенту
- Настройки: автоподтверждение, напоминания, Google Calendar

### Платформа
- Доступность: рабочие часы + блокировки + записи + буфер + Google freebusy
- Напоминания клиенту и админу, тестовый режим
- SQLite, миграции без удаления данных
- Docker
- Google Calendar опционален (`GOOGLE_CALENDAR_ENABLED=false` по умолчанию)

## Google Calendar (технически)

- Синхронизация = `.env` **и** переключатель в настройках бота
- Обновление событий при редактировании записи клиентом
- **Настройка:** [README_RU.md#настройка-google-calendar](README_RU.md#настройка-google-calendar)
- **Ошибки:** redirect_uri_mismatch, 403 test users, invalid_grant — в том же разделе

## Запуск

```bash
docker compose up -d --build
docker compose logs -f booking-bot
```

Сервер: `/opt/universal_booking_bot` — [DEPLOYMENT_RU.md](DEPLOYMENT_RU.md).

## Безопасность

Не коммитить: `.env`, `BOT_TOKEN`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`, `data/*.db`.

## Ограничения

1. SQLite без Alembic
2. OAuth Google вручную через Playground
3. Пагинация: 14 дат, 20 записей
4. Редкая гонка при одновременном подтверждении
5. Язык событий календаря = `DEFAULT_LANGUAGE` в `.env`

## Планируемые улучшения

- Alembic + PostgreSQL
- OAuth внутри бота
- Веб-админка
- Оплата
- Экспорт записей в CSV
