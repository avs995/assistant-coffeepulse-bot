import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import settings
from app.db import init_db
from app.handlers import router


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    init_db(settings.database_path)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
