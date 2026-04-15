## Telegram-бот: Google OAuth 2.0 и создание таблиц

Бот по кнопке «Подключить Google» запускает Authorization Code Flow, создаёт в аккаунте пользователя папку «Маржа24» с тремя таблицами (`ОПиУ`, `SKU`, `Настройки`), сохраняет `refresh_token` и URL таблиц в PostgreSQL и уведомляет в Telegram об успехе/ошибке.

### Структура
- `bot/` — aiogram 3 бот и aiohttp web_server, FSM.
- `handlers/` — хендлеры команд/кнопок.
- `database/` — `asyncpg`, таблица `users`.
- `google_api/` — OAuth, Drive/Sheets.
- `utils/` — конфиг, логирование, HMAC state.

### Требования
- Python 3.10+
- PostgreSQL 14+
- Установка:
  ```bash
  pip install -r requirements.txt
  ```

### .env (пример)
```bash
BOT_TOKEN=your_telegram_bot_token

POSTGRES_DSN=postgresql://tguser:your_db_password@localhost:5433/tggoogle

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8001
BACKEND_BASE_URL=https://your-domain.com

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://your-domain.com/auth/callback

STATE_SECRET=long_random_string_for_hmac_state
LOG_FILE=/opt/Bot-TG-Google-Sheets/bot.log
```

### Google OAuth 2.0 (кратко)
1) Google Cloud Console → проект → **APIs & Services → Library**: включить **Drive API**, **Sheets API**.  
2) **OAuth consent screen**: External, App name, support/developer email, scopes:  
   `https://www.googleapis.com/auth/drive.file`, `https://www.googleapis.com/auth/spreadsheets`; добавить тестовых пользователей.  
3) **Credentials → Create Credentials → OAuth client ID**: Web application, redirect URI: `https://your-domain.com/auth/callback`. Скопировать `client_id/secret` в `.env`.

### Локальный запуск (dev)
В двух терминалах:
```bash
python -m bot.web_server   # aiohttp backend
python -m bot.main         # Telegram бот
```

### Production (как настроено на сервере)
1. **PostgreSQL** (порт 5433 в нашем кейсе):
   ```bash
   su - postgres
   psql
   CREATE DATABASE tggoogle;
   CREATE USER tguser WITH PASSWORD 'your_db_password';
   GRANT ALL PRIVILEGES ON DATABASE tggoogle TO tguser;
   \q
   ```
   Таблица (создаётся авт.) или вручную:
   ```sql
   CREATE TABLE IF NOT EXISTS users (
       user_id BIGINT PRIMARY KEY,
       google_token TEXT,
       opiu_url TEXT,
       sku_url TEXT,
       setings_url TEXT,
       created_at TIMESTAMP DEFAULT NOW()
   );
   ```

2. **Виртуальное окружение**:
   ```bash
   cd /opt/Bot-TG-Google-Sheets
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **systemd** (пути как на сервере):
   - `/etc/systemd/system/tg-google-web.service`
     ```
     [Unit]
     Description=Telegram Google Bot Web Server
     After=network.target postgresql@16-main.service

     [Service]
     Type=simple
     User=root
     WorkingDirectory=/opt/Bot-TG-Google-Sheets
     Environment="PATH=/opt/Bot-TG-Google-Sheets/venv/bin"
     ExecStart=/opt/Bot-TG-Google-Sheets/venv/bin/python -m bot.web_server
     Restart=always
     RestartSec=10

     [Install]
     WantedBy=multi-user.target
     ```
   - `/etc/systemd/system/tg-google-bot.service`
     ```
     [Unit]
     Description=Telegram Google Bot
     After=network.target postgresql@16-main.service tg-google-web.service

     [Service]
     Type=simple
     User=root
     WorkingDirectory=/opt/Bot-TG-Google-Sheets
     Environment="PATH=/opt/Bot-TG-Google-Sheets/venv/bin"
     ExecStart=/opt/Bot-TG-Google-Sheets/venv/bin/python -m bot.main
     Restart=always
     RestartSec=10

     [Install]
     WantedBy=multi-user.target
     ```
   Активировать:
   ```bash
   systemctl daemon-reload
   systemctl enable tg-google-web.service tg-google-bot.service
   systemctl start tg-google-web.service tg-google-bot.service
   ```

4. **nginx + HTTPS (Let’s Encrypt)**, прокси на 127.0.0.1:8001:
   `/etc/nginx/sites-available/your-domain.com`
   ```
   server {
     listen 80;
     server_name your-domain.com;
     return 301 https://$server_name$request_uri;
   }
   server {
     listen 443 ssl http2;
     server_name your-domain.com;
     ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
     ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
     location / {
       proxy_pass http://127.0.0.1:8001;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
     }
   }
   ```
   Активировать и сертификат:
   ```bash
   ln -sf /etc/nginx/sites-available/your-domain.com /etc/nginx/sites-enabled/your-domain.com
   nginx -t && systemctl restart nginx
   certbot --nginx -d your-domain.com
   ```

### Чек-лист ТЗ
- `/start` — только кнопка «Подключить Google» (без текста), `/support` — заглушка.
- Кнопка → `/auth` (HTML с «Login with Google»), Authorization Code Flow.
- Успех: папка `Маржа24` + 3 таблицы, запись в `users` (refresh_token + URL’ы), уведомление «Google успешно подключен».
- Ошибка: уведомление «Ошибка авторизации…», лог в `bot.log`, сервисы не падают.
- Мультипользовательски: у каждого Telegram `user_id` своя папка/таблицы и своя запись в `users`.


