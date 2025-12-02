import logging

import aiohttp
from aiohttp import web

from database.db import ensure_schema, upsert_user_google_data
from google_api.auth import (
    create_folder_and_sheets,
    exchange_code_for_tokens,
    generate_authorization_url,
)
from utils.config import settings
from utils.logging_setup import setup_logging
from utils.state import parse_state


logger = logging.getLogger(__name__)


async def send_telegram_message(chat_id: int, text: str) -> None:
    """
    Отправка сообщения пользователю напрямую через Telegram Bot API.
    Используется backend-ом после успешной/неуспешной авторизации.
    """
    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error(
                        "Failed to send Telegram message: %s %s", resp.status, body
                    )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error sending Telegram message: %s", exc)


async def handle_auth(request: web.Request) -> web.Response:
    state = request.query.get("state")
    if not state:
        return web.Response(text="Missing state", status=400)

    auth_url = generate_authorization_url(state)
    html = f"""
    <html>
      <head><title>Google Auth</title></head>
      <body>
        <a href="{auth_url}">Login with Google</a>
      </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")


async def handle_auth_callback(request: web.Request) -> web.Response:
    try:
        code = request.query.get("code")
        state = request.query.get("state")
        error = request.query.get("error")

        # user_id восстанавливаем из подписанного state
        user_id = parse_state(state) if state else None

        if error:
            logger.error("Google OAuth error: %s", error)
            if user_id is not None:
                await send_telegram_message(
                    chat_id=user_id,
                    text="Ошибка авторизации, попробуйте еще раз, или обратитесь в поддержку.",
                )
            return web.Response(
                text="Ошибка авторизации, попробуйте еще раз, или обратитесь в поддержку.",
                content_type="text/plain",
            )

        if not code or not state or user_id is None:
            logger.error("Missing/invalid code or state in callback")
            if user_id is not None:
                await send_telegram_message(
                    chat_id=user_id,
                    text="Ошибка авторизации, попробуйте еще раз, или обратитесь в поддержку.",
                )
            return web.Response(
                text="Ошибка авторизации, попробуйте еще раз, или обратитесь в поддержку.",
                content_type="text/plain",
            )

        refresh_token, creds = exchange_code_for_tokens(code, state)
        if not refresh_token:
            logger.error("No refresh_token returned for user_id=%s", user_id)
            await send_telegram_message(
                chat_id=user_id,
                text="Ошибка авторизации, попробуйте еще раз, или обратитесь в поддержку.",
            )
            return web.Response(
                text="Ошибка авторизации, попробуйте еще раз, или обратитесь в поддержку.",
                content_type="text/plain",
            )

        opiu_url, sku_url, settings_url = create_folder_and_sheets(creds)

        await upsert_user_google_data(
            user_id=user_id,
            refresh_token=refresh_token,
            opiu_url=opiu_url,
            sku_url=sku_url,
            settings_url=settings_url,
        )

        # Отправляем пользователю уведомление в Telegram об успешной авторизации
        await send_telegram_message(
            chat_id=user_id,
            text="Google успешно подключен.",
        )

        return web.Response(
            text="Google успешно подключен. Вернитесь в Telegram.",
            content_type="text/plain",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error in auth callback: %s", exc)
        # Попробуем уведомить пользователя, если удалось восстановить user_id из state
        state = request.query.get("state")
        user_id = parse_state(state) if state else None
        if user_id is not None:
            await send_telegram_message(
                chat_id=user_id,
                text="Ошибка авторизации, попробуйте еще раз, или обратитесь в поддержку.",
            )
        return web.Response(
            text="Ошибка авторизации, попробуйте еще раз, или обратитесь в поддержку.",
            content_type="text/plain",
        )


async def init_app() -> web.Application:
    setup_logging()
    await ensure_schema()

    app = web.Application()
    app.router.add_get("/auth", handle_auth)
    app.router.add_get("/auth/callback", handle_auth_callback)
    return app


def main() -> None:
    app = web.Application()

    async def _startup(app_: web.Application) -> None:
        setup_logging()
        await ensure_schema()

    app.on_startup.append(_startup)
    app.router.add_get("/auth", handle_auth)
    app.router.add_get("/auth/callback", handle_auth_callback)

    web.run_app(
        app,
        host=settings.backend_host,
        port=settings.backend_port,
    )


if __name__ == "__main__":
    main()


