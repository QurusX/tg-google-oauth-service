# Secure Telegram & Google OAuth 2.0 Integration 🔐📊

**Высокопроизводительный асинхронный сервис для интеграции Telegram-ботов с Google Workspace (Drive/Sheets) через протокол OAuth 2.0.**

Этот проект реализует надежный механизм авторизации пользователей Telegram в сервисах Google с использованием **Server-Side Authorization Code Flow**. Основной фокус сделан на безопасности данных и автоматизации создания рабочего пространства пользователя.

## ✨ Ключевые возможности

*   **Промышленный OAuth 2.0:** Реализация полного цикла авторизации с получением и надежным хранением `refresh_token`.
*   **Автоматический Workspace Provisioning:** Сразу после авторизации система создает в Google Drive пользователя папку `Маржа24` и генерирует три необходимых шаблона таблиц (`ОПиУ`, `SKU`, `Настройки`).
*   **Безопасность (Anti-CSRF):** Использование HMAC-подписанных токенов в параметре `state` для верификации запросов и защиты от подделки.
*   **Полная асинхронность:** Построено на базе `Aiogram 3.x` и `Aiohttp` для обеспечения высокой пропускной способности.
*   **Хранение данных:** Интеграция с PostgreSQL через `asyncpg` для эффективной работы с токенами и метаданными пользователей.

## 🛠 Технологический стек

*   **Framework:** Aiogram 3.x (Telegram API)
*   **Web Server:** Aiohttp (OAuth Backend)
*   **Database:** PostgreSQL + Asyncpg
*   **Google API:** google-auth, google-api-python-client
*   **Security:** HMAC-SHA256 (State signing)
*   **Config:** Pydantic Settings

## 📂 Архитектура

```text
├── bot/            # Логика Telegram-бота и Backend-сервер
├── database/       # Асинхронные операции с БД (PostgreSQL)
├── google_api/     # Интеграция с Google OAuth, Drive и Sheets
├── handlers/       # Обработчики команд и событий бота
├── utils/          # Конфигурация, логирование и безопасность (State)
└── .env.example    # Шаблон конфигурации окружения
```

## 🚀 Быстрый старт

1.  **Клонирование и установка:**
    ```bash
    git clone https://github.com/nickalymov/tg-google-oauth-service.git
    cd tg-google-oauth-service
    python -m venv venv
    source venv/bin/activate # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Настройка окружения:**
    Создайте файл `.env` на основе `.env.example`. Вам потребуются учетные данные из Google Cloud Console (Client ID и Client Secret).

3.  **Запуск:**
    Сервис состоит из двух частей, работающих в одной связке:
    ```bash
    python -m bot.web_server   # Запуск backend для OAuth
    python -m bot.main         # Запуск Telegram-бота
    ```

## 🔒 Безопасность

Проект реализует защиту процесса авторизации:
1.  При генерации ссылки на авторизацию создается уникальный `state`.
2.  `state` подписывается секретным ключом сервера (HMAC).
3.  При получении callback от Google, подпись проверяется. Это гарантирует, что запрос инициировал именно ваш сервер и именно этот пользователь.

---

### Разработано
[Николай Алымов] — [nickalymov](t.me/nickalymov)
