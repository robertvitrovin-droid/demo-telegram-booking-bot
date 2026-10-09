from datetime import date, datetime, time
from bot.slots import bookable_days, free_slots, overlaps
from bot.db import DB

D = date(2026, 10, 12)  # Monday


def test_full_day_60min():
    s = free_slots(D, 60, [])
    assert s[0] == time(10, 0) and s[-1] == time(18, 0) and len(s) == 17


def test_busy_blocks_overlap():
    busy = [(datetime(2026, 10, 12, 12, 0), 60)]
    s = free_slots(D, 60, busy)
    assert time(11, 30) not in s and time(12, 30) not in s
    assert time(11, 0) in s and time(13, 0) in s


def test_long_service_fits_before_close():
    assert free_slots(D, 90, [])[-1] == time(17, 30)


def test_past_slots_hidden():
    s = free_slots(D, 30, [], now=datetime(2026, 10, 12, 15, 10))
    assert s[0] == time(15, 30)


def test_sunday_closed():
    days = bookable_days(date(2026, 10, 10), 7)  # Sat
    assert all(d.weekday() != 6 for d in days) and len(days) == 7


def test_overlap_edges():
    a = datetime(2026, 1, 1, 10)
    assert not overlaps(a, 60, datetime(2026, 1, 1, 11), 30)  # touching is fine
    assert overlaps(a, 60, datetime(2026, 1, 1, 10, 30), 30)


def test_db_prevents_double_booking(tmp_path):
    db = DB(str(tmp_path / "t.db"))
    t = datetime(2026, 10, 12, 12)
    assert db.create(1, "A", "haircut", 60, t)
    assert db.create(2, "B", "beard", 30, datetime(2026, 10, 12, 12, 30)) is None
    bid = db.create(2, "B", "beard", 30, datetime(2026, 10, 12, 13))
    assert db.cancel(bid) and not db.cancel(bid)
    assert b"haircut" in db.export_csv()


def test_reminders_due(tmp_path):
    db = DB(str(tmp_path / "t.db"))
    db.create(1, "A", "haircut", 60, datetime(2026, 10, 12, 12))
    now = datetime(2026, 10, 12, 10, 30)
    from datetime import timedelta
    assert len(db.due_reminders(now + timedelta(hours=2), now)) == 1
    assert len(db.due_reminders(now + timedelta(hours=1), now)) == 0
