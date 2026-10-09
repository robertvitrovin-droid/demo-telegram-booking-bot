"""Pure slot logic (no Telegram / DB) — fully unit-tested."""
from datetime import date, datetime, time, timedelta

from .config import CLOSED_WEEKDAYS, DAYS_AHEAD, SLOT_STEP_MIN, WORK_END, WORK_START


def bookable_days(today: date, days_ahead: int = DAYS_AHEAD) -> list[date]:
    return [today + timedelta(d) for d in range(days_ahead + 1)
            if (today + timedelta(d)).weekday() not in CLOSED_WEEKDAYS]


def overlaps(a_start: datetime, a_min: int, b_start: datetime, b_min: int) -> bool:
    return a_start < b_start + timedelta(minutes=b_min) and b_start < a_start + timedelta(minutes=a_min)


def free_slots(day: date, duration_min: int, busy: list[tuple[datetime, int]],
               now: datetime | None = None) -> list[time]:
    """Start times on `day` where a service of `duration_min` fits inside working hours,
    does not overlap any busy (start, duration) and is not in the past."""
    out = []
    t = datetime.combine(day, time(WORK_START))
    end = datetime.combine(day, time(WORK_END))
    while t + timedelta(minutes=duration_min) <= end:
        if (now is None or t > now) and not any(overlaps(t, duration_min, b, m) for b, m in busy):
            out.append(t.time())
        t += timedelta(minutes=SLOT_STEP_MIN)
    return out
