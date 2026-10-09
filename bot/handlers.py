from datetime import date, datetime, time

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .config import SERVICES
from .slots import bookable_days, free_slots

WD = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]


def setup(db, cfg, clock=datetime.now) -> Router:
    r = Router()

    def kb_services():
        b = InlineKeyboardBuilder()
        for k, (name, mins, price) in SERVICES.items():
            b.button(text=f"{name} · {mins} хв · {price} грн", callback_data=f"svc:{k}")
        return b.adjust(1).as_markup()

    @r.message(CommandStart())
    async def start(m: Message):
        await m.answer("Вітаю! Я бот запису до барбершопу (демо).\nОберіть послугу:",
                       reply_markup=kb_services())

    @r.callback_query(F.data.startswith("svc:"))
    async def pick_service(c: CallbackQuery):
        svc = c.data.split(":")[1]
        b = InlineKeyboardBuilder()
        for d in bookable_days(clock().date()):
            b.button(text=f"{WD[d.weekday()]} {d:%d.%m}", callback_data=f"day:{svc}:{d.isoformat()}")
        b.button(text="« Назад", callback_data="back")
        await c.message.edit_text(f"Послуга: {SERVICES[svc][0]}\nОберіть дату:",
                                  reply_markup=b.adjust(4).as_markup())
        await c.answer()

    @r.callback_query(F.data == "back")
    async def back(c: CallbackQuery):
        await c.message.edit_text("Оберіть послугу:", reply_markup=kb_services())
        await c.answer()

    @r.callback_query(F.data.startswith("day:"))
    async def pick_day(c: CallbackQuery):
        _, svc, d = c.data.split(":", 2)
        day = date.fromisoformat(d)
        slots = free_slots(day, SERVICES[svc][1], db.busy_on(day), now=clock())
        if not slots:
            await c.answer("На цей день вільних слотів немає", show_alert=True)
            return
        b = InlineKeyboardBuilder()
        for t in slots:
            b.button(text=f"{t:%H:%M}", callback_data=f"slot:{svc}:{d}:{t:%H%M}")
        b.button(text="« Інша дата", callback_data=f"svc:{svc}")
        await c.message.edit_text(f"{SERVICES[svc][0]}, {day:%d.%m}\nОберіть час:",
                                  reply_markup=b.adjust(4).as_markup())
        await c.answer()

    @r.callback_query(F.data.startswith("slot:"))
    async def pick_slot(c: CallbackQuery):
        _, svc, d, hm = c.data.split(":")
        b = InlineKeyboardBuilder()
        b.button(text="✅ Підтвердити", callback_data=f"ok:{svc}:{d}:{hm}")
        b.button(text="« Інший час", callback_data=f"day:{svc}:{d}")
        name, mins, price = SERVICES[svc]
        await c.message.edit_text(f"Перевірте запис:\n{name} ({mins} хв, {price} грн)\n"
                                  f"{date.fromisoformat(d):%d.%m.%Y} о {hm[:2]}:{hm[2:]}",
                                  reply_markup=b.adjust(1).as_markup())
        await c.answer()

    @r.callback_query(F.data.startswith("ok:"))
    async def confirm(c: CallbackQuery):
        _, svc, d, hm = c.data.split(":")
        start_at = datetime.combine(date.fromisoformat(d), time(int(hm[:2]), int(hm[2:])))
        bid = db.create(c.from_user.id, c.from_user.full_name, svc, SERVICES[svc][1], start_at)
        if bid is None:
            await c.message.edit_text("На жаль, цей час щойно зайняли. Спробуйте /start ще раз.")
        else:
            await c.message.edit_text(f"Готово! Запис №{bid}: {SERVICES[svc][0]}, "
                                      f"{start_at:%d.%m о %H:%M}.\nНагадаю за {cfg.reminder_hours} год. "
                                      f"Мої записи: /my")
        await c.answer()

    @r.message(Command("my"))
    async def my(m: Message):
        rows = db.list(user_id=m.from_user.id)
        await m.answer("\n".join(f"№{x['id']} {SERVICES[x['service']][0]} — {x['starts_at'].replace('T', ' ')}"
                                 for x in rows) or "Активних записів немає.")

    # ---------- admin ----------
    def is_admin(uid): return uid in cfg.admin_ids

    @r.message(Command("admin"))
    async def admin(m: Message):
        if not is_admin(m.from_user.id):
            return await m.answer("Немає доступу.")
        b = InlineKeyboardBuilder()
        b.button(text="📋 Список записів", callback_data="adm:list")
        b.button(text="📤 Експорт CSV", callback_data="adm:export")
        await m.answer("Адмін-панель", reply_markup=b.adjust(1).as_markup())

    @r.callback_query(F.data == "adm:list")
    async def adm_list(c: CallbackQuery):
        if not is_admin(c.from_user.id):
            return await c.answer("Немає доступу", show_alert=True)
        rows = db.list()
        b = InlineKeyboardBuilder()
        for x in rows:
            b.button(text=f"❌ №{x['id']} {x['starts_at'][5:].replace('T', ' ')} {x['user_name']}",
                     callback_data=f"adm:cancel:{x['id']}")
        await c.message.answer(f"Активних записів: {len(rows)}" + ("\nНатисніть, щоб скасувати:" if rows else ""),
                               reply_markup=b.adjust(1).as_markup())
        await c.answer()

    @r.callback_query(F.data.startswith("adm:cancel:"))
    async def adm_cancel(c: CallbackQuery):
        if not is_admin(c.from_user.id):
            return await c.answer("Немає доступу", show_alert=True)
        bid = int(c.data.rsplit(":", 1)[1])
        ok = db.cancel(bid)
        await c.answer(f"Запис №{bid} скасовано" if ok else "Вже скасовано", show_alert=True)

    @r.callback_query(F.data == "adm:export")
    async def adm_export(c: CallbackQuery):
        if not is_admin(c.from_user.id):
            return await c.answer("Немає доступу", show_alert=True)
        await c.message.answer_document(BufferedInputFile(db.export_csv(), "bookings.csv"))
        await c.answer()

    return r
