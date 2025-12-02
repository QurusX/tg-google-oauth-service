## Telegram-бот: подключение Google OAuth 2.0 и создание таблиц

Проект реализует Telegram-бота, который по нажатию кнопки «Подключить Google» запускает OAuth 2.0 авторизацию через Google, создаёт в аккаунте пользователя папку «Маржа24» и три таблицы внутри, а также сохраняет `refresh_token` и URL таблиц в PostgreSQL.

### Структура проекта

- `bot/` – запуск Telegram-бота и FSM.
- `handlers/` – хендлеры команд и кнопок.
- `database/` – работа с PostgreSQL через `asyncpg`.
- `google_api/` – интеграция с Google OAuth 2.0 и Google Drive/Sheets.
- `utils/` – конфигурация, логирование и вспомогательные функции.

### Требования

- Python 3.10+
- PostgreSQL 14+
- Установленные зависимости:

```bash
pip install -r requirements.txt
```

### Переменные окружения

Создайте файл `.env` в корне проекта и заполните:

```bash
BOT_TOKEN=your_telegram_bot_token_here

POSTGRES_DSN=postgresql://postgres.hjlaytpocdeahabkiivw:YOUR_DB_PASSWORD@aws-1-eu-central-1.pooler.supabase.com:6543/postgres

BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
BACKEND_BASE_URL=http://127.0.0.1:8000

GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/auth/callback

STATE_SECRET=your_long_random_secret_here

LOG_FILE=bot.log
```

### Как создать OAuth 2.0 client ID в Google Cloud

См. раздел «Google OAuth 2.0 настройка» ниже.

### Запуск бота и backend (локально)

В двух терминалах:

```bash
# 1. Backend (aiohttp)
python -m bot.web_server

# 2. Telegram-бот
python -m bot.main
```

### Google OAuth 2.0 настройка (кратко)

1. Зайдите в [Google Cloud Console](https://console.cloud.google.com/).
2. Создайте или выберите проект.
3. Включите API:
   - Google Drive API
   - Google Sheets API
4. В меню «OAuth consent screen»:
   - Тип: External.
   - Заполните название приложения и e-mail.
   - Добавьте нужные скопы (Drive, Sheets).
   - Добавьте тестовых пользователей (e-mail, на которых будете тестировать).
5. В меню «Credentials» → «Create Credentials» → «OAuth client ID»:
   - Application type: Web application.
   - Authorized redirect URIs: `http://127.0.0.1:8000/auth/callback` (и/или ваш боевой домен).
6. Сохраните выданные `client_id` и `client_secret` и пропишите их в `.env`.


