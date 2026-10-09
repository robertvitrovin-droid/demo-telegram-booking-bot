"""Token-free demo: drives the REAL aiogram handlers through a fake Telegram API session,
records the conversation and writes demo/transcript.json (+ renders screenshots if Chrome exists).

    python -m demo.run_demo
"""
import asyncio
import json
import os
import tempfile
from datetime import datetime
from itertools import count
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.methods import AnswerCallbackQuery, EditMessageText, SendDocument, SendMessage
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from bot.config import Config
from bot.db import DB
from bot.handlers import setup
from bot.reminders import send_due

CLIENT = User(id=1001, is_bot=False, first_name="Олена", last_name="(тест)")
ADMIN = User(id=9001, is_bot=False, first_name="Адмін")
BOT_USER = User(id=42, is_bot=True, first_name="DemoBookingBot", username="demo_booking_bot")
NOW = datetime(2026, 10, 12, 9, 0)  # fixed clock -> reproducible output
mid = count(100)
log: list[dict] = []


def kb(markup):
    if not markup:
        return []
    return [[b.text for b in row] for row in markup.inline_keyboard]


class FakeSession(BaseSession):
    async def make_request(self, bot, method, timeout=None):
        chat = Chat(id=getattr(method, "chat_id", 0) or 0, type="private")
        if isinstance(method, SendMessage):
            log.append({"who": "bot", "chat": method.chat_id, "text": method.text, "kb": kb(method.reply_markup)})
        elif isinstance(method, EditMessageText):
            log.append({"who": "bot", "chat": method.chat_id, "text": method.text,
                        "kb": kb(method.reply_markup), "edited": True})
        elif isinstance(method, SendDocument):
            log.append({"who": "bot", "chat": method.chat_id, "file": method.document.filename})
        elif isinstance(method, AnswerCallbackQuery):
            if method.text:
                log.append({"who": "toast", "text": method.text})
            return True
        return Message(message_id=next(mid), date=NOW, chat=chat, from_user=BOT_USER,
                       text=getattr(method, "text", None))

    async def close(self): ...
    async def stream_content(self, *a, **k):
        yield b""


async def main(out=Path(__file__).parent):
    cfg = Config()
    cfg.admin_ids = {ADMIN.id}
    db = DB(os.path.join(tempfile.mkdtemp(), "demo.sqlite3"))
    bot = Bot("42:DEMO", session=FakeSession())
    dp = Dispatcher()
    dp.include_router(setup(db, cfg, clock=lambda: NOW))
    uid = count(1)

    async def say(user, text):
        log.append({"who": "user", "user": user.first_name, "text": text})
        m = Message(message_id=next(mid), date=NOW, chat=Chat(id=user.id, type="private"), from_user=user, text=text)
        await dp.feed_update(bot, Update(update_id=next(uid), message=m))

    async def tap(user, data, label):
        log.append({"who": "tap", "user": user.first_name, "text": label})
        msg = Message(message_id=next(mid), date=NOW, chat=Chat(id=user.id, type="private"), from_user=BOT_USER, text="")
        cq = CallbackQuery(id=str(next(mid)), from_user=user, chat_instance="x", data=data, message=msg)
        await dp.feed_update(bot, Update(update_id=next(uid), callback_query=cq))

    # pre-existing booking so one slot shows as taken
    db.create(2002, "Інший клієнт", "haircut", 60, datetime(2026, 10, 12, 11, 0))

    log.append({"scene": "client"})
    await say(CLIENT, "/start")
    await tap(CLIENT, "svc:haircut", "Стрижка · 60 хв · 400 грн")
    await tap(CLIENT, "day:haircut:2026-10-12", "Пн 12.10")
    await tap(CLIENT, "slot:haircut:2026-10-12:1200", "12:00")
    await tap(CLIENT, "ok:haircut:2026-10-12:1200", "✅ Підтвердити")
    await say(CLIENT, "/my")
    log.append({"scene": "reminder"})
    sent = await send_due(bot, db, cfg.reminder_hours, datetime(2026, 10, 12, 10, 5))
    log.append({"scene": "admin"})
    await say(CLIENT, "/admin")
    await say(ADMIN, "/admin")
    await tap(ADMIN, "adm:list", "📋 Список записів")
    await tap(ADMIN, "adm:cancel:1", "❌ №1 10-12 11:00 Інший клієнт")
    await tap(ADMIN, "adm:export", "📤 Експорт CSV")

    (out / "transcript.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    for e in log:
        if "scene" in e:
            print(f"\n===== {e['scene']} =====")
        elif e["who"] in ("user", "tap"):
            print(f"[{e['user']}] {'(tap) ' if e['who']=='tap' else ''}{e['text']}")
        elif e["who"] == "toast":
            print(f"  <toast> {e['text']}")
        else:
            print(f"  BOT: {e.get('text') or '📎 ' + e['file']}".replace("\n", "\n       "))
            for row in e.get("kb", []):
                print("       [" + "] [".join(row) + "]")
    print(f"\nreminders sent: {sent}; active bookings left: {len(db.list())}")
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
