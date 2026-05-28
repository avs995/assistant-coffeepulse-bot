from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings

router = Router()


async def _ensure_owner(message: Message) -> bool:
    if message.from_user is None or message.from_user.id != settings.owner_id:
        await message.answer("Доступ закрыт.")
        return False
    return True


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    await message.answer(
        "CoffeePulse Sales Assistant запущен.\n"
        "Доступные команды:\n"
        "/help"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    if not await _ensure_owner(message):
        return

    await message.answer(
        "CoffeePulse Sales Assistant — приватный помощник для ведения лидов CoffeePulse.\n"
        "В этом MVP бот будет помогать собирать лиды, готовить сообщения и вести статусы.\n"
        "Автоматическая холодная рассылка не используется."
    )
