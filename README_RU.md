# Universal Booking Bot

🇬🇧 **English documentation:** [README.md](README.md)

Telegram-бот для записи на услуги — уроки, консультации, beauty, медицина и любые услуги с расписанием.

**Репозиторий:** https://github.com/PsychicBAM/universal_booking_bot

---

## Описание проекта

Клиенты записываются через Telegram. Администратор управляет услугами, расписанием, медиа, местами проведения, записями, напоминаниями и опциональной синхронизацией с Google Calendar — всё из бота.

| Область | Возможности |
|---------|-------------|
| **Клиент** | Запись, карточки услуг с фото/видео, выбор места, адрес и комментарий, мои записи, перенос/редактирование, отмена, связь с админом через бота, RU/EN |
| **Админ** | Услуги CRUD, архив, длительность/буфер, медиа (5 фото + 1 видео), места проведения, рабочие часы, недоступные даты, записи, настройки (текст и фото /start), напоминания |
| **Движок** | Доступность (рабочие часы + блоки + записи + буфер + занятость Google Calendar), SQLite, Docker |

---

## Установка одной командой (Linux-сервер)

Нужны **Docker**, **Docker Compose** и **git**:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/PsychicBAM/universal_booking_bot/main/install.sh)
```

Путь установки: `/opt/universal_booking_bot`

После установки отредактируйте `.env` (`BOT_TOKEN`, `ADMIN_IDS`), затем:

```bash
cd /opt/universal_booking_bot
docker compose up -d --build
docker compose logs -f booking-bot
```

**Подробнее:** [QUICK_START_RU.md](QUICK_START_RU.md) · [DEPLOYMENT_RU.md](DEPLOYMENT_RU.md)

---

## Запуск через Docker (локально / вручную)

```bash
git clone https://github.com/PsychicBAM/universal_booking_bot.git
cd universal_booking_bot
cp .env.example .env
# Отредактируйте .env — BOT_TOKEN и ADMIN_IDS
docker compose up -d --build
docker compose logs -f booking-bot
```

База данных: `./data/booking_bot.db`.

---

## Настройка `.env`

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | От @BotFather (**обязательно**) |
| `ADMIN_IDS` | Telegram ID админов через запятую (**обязательно**) |
| `DATABASE_URL` | По умолчанию `sqlite+aiosqlite:///data/booking_bot.db` |
| `TIMEZONE` | Например `Europe/Moscow` |
| `DEFAULT_LANGUAGE` | `ru` или `en` |
| `DEFAULT_SLOT_STEP_MINUTES` | Шаг слотов (по умолчанию 30) |
| `BOOKING_DAYS_AHEAD` | На сколько дней вперёд можно записаться (30) |
| `CANCEL_BOOKING_HOURS_BEFORE` | За сколько часов можно отменить (2) |
| `RESCHEDULE_BOOKING_HOURS_BEFORE` | За сколько часов можно перенести (как отмена) |
| `CONTACT_ADMIN_USERNAME` | @username для связи с админом |
| `REMINDERS_ENABLED` | `true` / `false` |
| `CLIENT_REMINDER_1_MINUTES` | Первое напоминание клиенту (1440 = 24 ч) |
| `CLIENT_REMINDER_2_MINUTES` | Второе напоминание (120 = 2 ч) |
| `ADMIN_REMINDER_MINUTES` | Напоминание админу (60) |
| `GOOGLE_CALENDAR_*` | Опционально — см. [Настройка Google Calendar](#настройка-google-calendar) |

Скопируйте из `.env.example`. **Никогда не коммитьте `.env` в git.**

---

## Админ-панель (первый запуск)

1. Откройте бота → `/start`
2. Отправьте `/admin` с аккаунта админа (`ADMIN_IDS`)
3. **Услуги** — создайте услугу (название, описание, длительность, буфер, цена)
4. **Места проведения** — фиксированные адреса/офисы для выбора клиентом
5. **Медиа** — фото/видео, обложка, показ клиентам
6. **Рабочее время** — дни и часы приёма
7. **Недоступные даты** — блокировка дней или интервалов
8. **Настройки бота** — автоподтверждение, напоминания, контакт, язык, **👋 Стартовое сообщение** (текст и фото /start), Google Calendar
9. Проверьте полный цикл записи клиентом

### Стартовое сообщение (/start)

Админ настраивает приветствие без правки кода:

1. `/admin` → **⚙️ Настройки бота** → **👋 Стартовое сообщение**
2. Текст RU/EN отдельно (до 1000 символов)
3. Отдельные фото RU и EN (только Telegram `file_id`, без локальных файлов)
4. Вкл/выкл фото по языкам, предпросмотр RU/EN, сброс к стандарту

При `/start` пользователь видит текст и фото своего языка (RU или EN).

### Доступные языки

В **⚙️ Настройки бота → 🌐 Доступные языки** админ выбирает:

- **Только русский** — скрывается кнопка 🌐 Язык; все видят русский интерфейс и только RU-настройки старта
- **English only** — без переключения языка; только EN-настройки старта
- **Русский + English** — кнопка языка доступна; настройки старта для RU и EN

Сохранённые тексты и фото RU/EN не удаляются при скрытии языка. Опционально в `.env`: `ENABLED_LANGUAGES=ru,en`.

**Совместимость:** если остался только старый `start_photo_file_id`, он используется как запасной вариант, когда фото для языка не задано и старое фото включено.

### Связь с админом (поддержка в боте)

Клиент нажимает **📞 Связаться с админом** и видит **меню поддержки** с темами, связанными с записями (вопрос по записи, перенос, отмена, оплата, другое).

- **📝 Новое обращение** — выбор темы и отправка сообщения
- **📋 Мои обращения** — история обращений и ответы админа
- Для переноса/отмены можно привязать активную запись
- Все админы из `ADMIN_IDS` получают обращение с кнопками **Ответить** / **Закрыть**
- Сообщения сохраняются в `support_messages` с темой и опциональным `booking_id`
- `contact_admin_username` — опциональный прямой `@username` на стартовом экране

**✉️ Написать клиенту** в карточке записи не изменено.

### Услуги

Создание, редактирование, вкл/выкл, архив, восстановление. Для каждой услуги: длительность, буфер после услуги, цена, запрос адреса у клиента, медиа, места проведения.

### Рабочее время

Кнопочный интерфейс: дни недели, пресеты, ручной ввод времени. Без рабочих часов на день — слотов нет.

### Недоступные даты

Целый день или диапазон времени. Клиент не увидит заблокированные слоты.

### Напоминания

Клиенту (2 напоминания) и админу. Тестовый режим — в минутах для быстрой проверки. Настройка в **⚙️ Настройки бота**.

### Медиа услуги

До 5 фото и 1 видео. Обложка, превью, вкл/выкл показ клиентам. Карточка услуги — фото + описание + кнопки.

### Места проведения услуги

Админ добавляет офисы/адреса. Если есть активные места — клиент выбирает одно перед датой. Отдельно от «адреса клиента» (`requires_location`).

---

## Настройка Google Calendar

Google Calendar **не обязателен**. Бот полностью работает без него.

### Режим по умолчанию

```env
GOOGLE_CALENDAR_ENABLED=false
```

Без календаря:

- Google-учётные данные не нужны
- Записи только в локальной SQLite
- Доступность по рабочим часам, блокировкам и существующим записям

### Нужные переменные `.env` (если включено)

```env
GOOGLE_CALENDAR_ENABLED=true
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://developers.google.com/oauthplayground
GOOGLE_REFRESH_TOKEN=your_refresh_token
GOOGLE_CALENDAR_ID=primary
```

### Шаг 1 — Проект Google Cloud

1. [Google Cloud Console](https://console.cloud.google.com/).
2. Создайте проект (например **Booking Bot**).
3. Включите **Google Calendar API**.

### Шаг 2 — OAuth consent screen

1. **Google Auth Platform** → **OAuth consent screen**.
2. **External** (или **Internal** для Workspace).
3. Заполните название, email поддержки, контакт разработчика.
4. В режиме **Testing**: **Audience** → **Test users** → **Add users** → ваш Gmail.

### Шаг 3 — OAuth client (Web application)

1. **Credentials** → **Create credentials** → **OAuth client ID**.
2. Тип: **Web application**.
3. **Authorized redirect URI** точно:

   ```
   https://developers.google.com/oauthplayground
   ```

4. Сохраните. **Client ID** и **Client Secret** → в `.env`.

### Шаг 4 — Refresh token (OAuth 2.0 Playground)

1. [OAuth 2.0 Playground](https://developers.google.com/oauthplayground).
2. **Шестерёнка** → **Use your own OAuth credentials**.
3. Вставьте Client ID и Client Secret.
4. Scope: `https://www.googleapis.com/auth/calendar`
5. **Authorize APIs** → войти → разрешить.
6. **Exchange authorization code for tokens**.
7. Скопируйте **Refresh token** (не Access token) → `GOOGLE_REFRESH_TOKEN` в `.env`.

#### Access token и Refresh token

| Токен | Назначение |
|-------|------------|
| **Access token** | Временный (~1 час). **Не кладите в `.env`.** |
| **Refresh token** | Долгоживущий. Бот получает новые access token. **Именно он в `.env`.** |

### Шаг 5 — Calendar ID

```env
GOOGLE_CALENDAR_ID=primary
```

Отдельный календарь: Google Calendar → Настройки → Calendar ID.

### Шаг 6 — Перезапуск Docker

```bash
cd /opt/universal_booking_bot
docker compose down
docker compose up -d --build
docker compose logs -f booking-bot
```

### Шаг 7 — Включение в Telegram

1. `/admin` → **⚙️ Настройки бота** → **📅 Google Calendar**
2. **📋 Проверить подключение**
3. Включите синхронизацию на том же экране

### Шаг 8 — Проверка

| Тест | Ожидание |
|------|----------|
| **Занятые слоты** | Личное событие в Google Calendar → слот скрыт у клиента |
| **Создание события** | Подтверждённая запись → событие в календаре |
| **Обновление** | Клиент переносит/меняет место → событие обновляется |
| **Удаление** | Отмена записи → событие удаляется |

```bash
docker compose exec booking-bot python scripts/check_google_calendar.py
```

### Что делает Google Calendar

- Занятость в Google скрывает слоты
- Подтверждённые записи создают события
- Отмена удаляет события
- Редактирование клиентом обновляет событие
- Локация: адрес клиента → адрес места проведения → пусто

### Частые ошибки Google Calendar

#### Ошибка: Error 400: redirect_uri_mismatch

**Причина:** redirect URI в Google Cloud не совпадает с OAuth Playground.

**Решение:** создать OAuth Client типа **Web application** и добавить **Authorized redirect URI** точно:

```
https://developers.google.com/oauthplayground
```

---

#### Ошибка: Access blocked: app has not completed the Google verification process / Error 403: access_denied

**Причина:** приложение в Testing mode, а email не добавлен в Test users.

**Решение:** Google Auth Platform → **Audience** → **Test users** → **Add users** → добавить свой Gmail.

---

#### Ошибка: Access token expires

**Объяснение:** Access token временный, обычно живёт около 1 часа. В `.env` нужен **Refresh token**, не Access token.

---

#### Ошибка: No refresh token appears

**Решение:** в OAuth Playground включить **Use your own OAuth credentials**, **Offline access** если видно, **Force prompt** / **Consent** если доступно, либо удалить старое разрешение приложения из [Google Account permissions](https://myaccount.google.com/permissions) и авторизоваться заново.

---

#### Ошибка: invalid_grant

**Решение:** получить новый refresh token и проверить, что Client ID/Secret от **того же** Google Cloud проекта.

---

#### Другие проверки

| Симптом | Что проверить |
|---------|---------------|
| Нет подключения | ID, Secret, Refresh token; API включён; test user |
| События не создаются | `GOOGLE_CALENDAR_ENABLED=true`; синхронизация ВКЛ; запись **подтверждена** |
| Слоты не скрываются | Тот же `GOOGLE_CALENDAR_ID`; `TIMEZONE`; событие в этом календаре |

Английская версия: [README.md#google-calendar-setup](README.md#google-calendar-setup)

---

## Безопасность — никогда не публиковать

- `.env`
- `BOT_TOKEN`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
- файлы базы `data/*.db`

В репозитории только `.env.example` с плейсхолдерами.

---

## Обновление и бэкап

| Действие | Команда |
|----------|---------|
| **Обновление** | `bash /opt/universal_booking_bot/update.sh` |
| **Бэкап БД** | `bash /opt/universal_booking_bot/backup.sh` |
| **Логи** | `cd /opt/universal_booking_bot && docker compose logs -f booking-bot` |

Подробнее: [DEPLOYMENT_RU.md](DEPLOYMENT_RU.md)

---

## Документация

| English | Русский |
|---------|---------|
| [README.md](README.md) | [README_RU.md](README_RU.md) |
| [QUICK_START.md](QUICK_START.md) | [QUICK_START_RU.md](QUICK_START_RU.md) |
| [DEPLOYMENT.md](DEPLOYMENT.md) | [DEPLOYMENT_RU.md](DEPLOYMENT_RU.md) |
| [NOTES.md](NOTES.md) | [NOTES_RU.md](NOTES_RU.md) |

---

## Известные ограничения

- Миграции SQLite без Alembic
- OAuth вручную через Playground (нет OAuth в боте)
- Медиа только через Telegram `file_id`
- Пагинация: 14 дат, 20 записей на экран

См. [NOTES_RU.md](NOTES_RU.md).
