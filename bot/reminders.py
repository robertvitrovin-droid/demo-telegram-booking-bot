import asyncio
import logging
from datetime import datetime, timedelta

from .config import SERVICES

log = logging.getLogger(__name__)


async def send_due(bot, db, hours: int, now: datetime) -> int:
    n = 0
    for x in db.due_reminders(now + timedelta(hours=hours), now):
        try:
            await bot.send_message(x["user_id"], f"⏰ Нагадування: {SERVICES[x['service']][0]} "
                                                 f"сьогодні о {x['starts_at'][11:16]}.")
            db.mark_reminded(x["id"]); n += 1
        except Exception:  # user blocked bot etc.
            log.exception("reminder failed for %s", x["id"])
    return n


async def loop(bot, db, hours: int, interval: int = 60):
    while True:
        await send_due(bot, db, hours, datetime.now())
        await asyncio.sleep(interval)
