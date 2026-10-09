import os
from dataclasses import dataclass, field


@dataclass
class Config:
    token: str = os.getenv("BOT_TOKEN", "")
    admin_ids: set[int] = field(default_factory=lambda: {
        int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x})
    db_path: str = os.getenv("DB_PATH", "bookings.sqlite3")
    tz: str = os.getenv("TZ_NAME", "Europe/Kyiv")
    reminder_hours: int = int(os.getenv("REMINDER_HOURS", "2"))


SERVICES = {
    "haircut": ("Стрижка", 60, 400),
    "beard": ("Корекція бороди", 30, 250),
    "combo": ("Стрижка + борода", 90, 600),
}
WORK_START, WORK_END = 10, 19      # 10:00–19:00
SLOT_STEP_MIN = 30
DAYS_AHEAD = 7
CLOSED_WEEKDAYS = {6}              # Sunday
