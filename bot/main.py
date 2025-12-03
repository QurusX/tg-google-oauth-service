import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

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


def get_connect_keyboard(user_id: int) -> InlineKeyboardMarkup:
    # Генерируем безопасный state (подписанный HMAC) и сразу формируем URL на /auth.
    state_token = generate_state(user_id)
    auth_page_url = f"{settings.backend_base_url}/auth?state={state_token}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подключить Google",
                    url=auth_page_url,
                )
            ]
        ]
    )


async def cmd_start(message: Message, state: FSMContext) -> None:
    # Сбрасываем состояние авторизации при новом /start
    await state.clear()
    user_id = message.from_user.id
    await message.answer(
        # Telegram не принимает полностью пустой текст,
        # используем невидимый символ, чтобы визуально не было лишнего текста.
        text="\u2060",
        reply_markup=get_connect_keyboard(user_id),
    )


async def cmd_support(message: Message) -> None:
    # Муляжная команда "Поддержка" по ТЗ.
    await message.answer("Поддержка: данный раздел будет доступен позже.")


async def main() -> None:
    setup_logging()

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_support, Command("support"))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


