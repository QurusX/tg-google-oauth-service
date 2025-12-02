import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from utils.config import settings
from utils.logging_setup import setup_logging
from utils.state import generate_state


logger = logging.getLogger(__name__)


CONNECT_GOOGLE_CALLBACK = "connect_google"


class AuthStates(StatesGroup):
    waiting_google = State()


async def on_startup(bot: Bot) -> None:
    logger.info("Bot started")


async def on_shutdown(bot: Bot) -> None:
    logger.info("Bot stopped")


def get_connect_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подключить Google", callback_data=CONNECT_GOOGLE_CALLBACK)]
        ]
    )


async def cmd_start(message: Message, state: FSMContext) -> None:
    # Сбрасываем состояние авторизации при новом /start
    await state.clear()
    await message.answer(
        # Telegram не принимает полностью пустой текст,
        # используем невидимый символ, чтобы визуально не было лишнего текста.
        text="\u2060",
        reply_markup=get_connect_keyboard(),
    )


async def on_connect_google(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    # Генерируем безопасный state (подписанный HMAC).
    state_token = generate_state(user_id)
    auth_page_url = f"{settings.backend_base_url}/auth?state={state_token}"

    # Переводим пользователя в состояние ожидания авторизации Google.
    await state.set_state(AuthStates.waiting_google)

    await callback.message.answer(
        "Перейдите по ссылке для подключения Google:\n" f"{auth_page_url}"
    )
    await callback.answer()


async def main() -> None:
    setup_logging()

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.message.register(cmd_start, Command("start"))
    dp.callback_query.register(on_connect_google, F.data == CONNECT_GOOGLE_CALLBACK)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


