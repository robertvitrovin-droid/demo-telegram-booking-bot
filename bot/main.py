import asyncio
import logging

from aiogram import Bot, Dispatcher

from .config import Config
from .db import DB
from .handlers import setup
from .reminders import loop


async def main():
    logging.basicConfig(level=logging.INFO)
    cfg = Config()
    if not cfg.token:
        raise SystemExit("BOT_TOKEN is not set. For a no-token run use: python -m demo.run_demo")
    db = DB(cfg.db_path)
    bot = Bot(cfg.token)
    dp = Dispatcher()
    dp.include_router(setup(db, cfg))
    asyncio.create_task(loop(bot, db, cfg.reminder_hours))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
