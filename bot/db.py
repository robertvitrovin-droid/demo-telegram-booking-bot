import csv
import io
import sqlite3
from datetime import datetime

SCHEMA = """
CREATE TABLE IF NOT EXISTS bookings(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL, user_name TEXT, service TEXT NOT NULL,
  duration_min INTEGER NOT NULL, starts_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active', reminded INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS ix_starts ON bookings(starts_at, status);
"""


class DB:
    def __init__(self, path: str):
        self.c = sqlite3.connect(path)
        self.c.row_factory = sqlite3.Row
        self.c.executescript(SCHEMA)

    def busy_on(self, day) -> list[tuple[datetime, int]]:
        rows = self.c.execute("SELECT starts_at, duration_min FROM bookings WHERE status='active' "
                              "AND date(starts_at)=?", (day.isoformat(),)).fetchall()
        return [(datetime.fromisoformat(r[0]), r[1]) for r in rows]

    def create(self, user_id, user_name, service, duration, starts_at: datetime) -> int | None:
        """Atomic: re-checks overlap inside a transaction so two clients can't take one slot."""
        from .slots import overlaps
        with self.c:
            self.c.execute("BEGIN IMMEDIATE")
            for b, m in self.busy_on(starts_at.date()):
                if overlaps(starts_at, duration, b, m):
                    return None
            cur = self.c.execute("INSERT INTO bookings(user_id,user_name,service,duration_min,starts_at)"
                                 " VALUES(?,?,?,?,?)", (user_id, user_name, service, duration,
                                                        starts_at.isoformat(timespec="minutes")))
            return cur.lastrowid

    def list(self, status="active", user_id=None):
        q, p = "SELECT * FROM bookings WHERE status=?", [status]
        if user_id is not None:
            q += " AND user_id=?"; p.append(user_id)
        return self.c.execute(q + " ORDER BY starts_at", p).fetchall()

    def cancel(self, booking_id: int) -> bool:
        with self.c:
            return self.c.execute("UPDATE bookings SET status='cancelled' WHERE id=? AND status='active'",
                                  (booking_id,)).rowcount == 1

    def due_reminders(self, until: datetime, now: datetime):
        return self.c.execute("SELECT * FROM bookings WHERE status='active' AND reminded=0 "
                              "AND starts_at<=? AND starts_at>?",
                              (until.isoformat(timespec="minutes"), now.isoformat(timespec="minutes"))).fetchall()

    def mark_reminded(self, booking_id: int):
        with self.c:
            self.c.execute("UPDATE bookings SET reminded=1 WHERE id=?", (booking_id,))

    def export_csv(self) -> bytes:
        buf = io.StringIO()
        rows = self.c.execute("SELECT id,user_id,user_name,service,starts_at,status,created_at "
                              "FROM bookings ORDER BY starts_at").fetchall()
        w = csv.writer(buf)
        w.writerow(["id", "user_id", "user_name", "service", "starts_at", "status", "created_at"])
        w.writerows([tuple(r) for r in rows])
        return buf.getvalue().encode("utf-8-sig")
