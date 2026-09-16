"""
SQLite 数据库连接工厂与表结构初始化。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import DB_PATH, INITIAL_ATTENDEES
from app.src.common.logger import get_logger

logger = get_logger("db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    department TEXT NOT NULL,
    host_name TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    expected_count INTEGER DEFAULT 0,
    status TEXT CHECK(status IN ('scheduled', 'in_progress', 'completed', 'active')) DEFAULT 'in_progress',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    position TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS check_in_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER NOT NULL,
    attendee_id INTEGER NOT NULL,
    first_seen_time DATETIME,
    check_in_time DATETIME,
    duration_seconds INTEGER DEFAULT 0,
    distraction_count INTEGER DEFAULT 0,
    status TEXT CHECK(status IN ('present', 'late', 'absent', 'excused')) DEFAULT 'absent',
    is_manual_override INTEGER DEFAULT 0,
    FOREIGN KEY(meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
    FOREIGN KEY(attendee_id) REFERENCES attendees(id) ON DELETE CASCADE,
    UNIQUE(meeting_id, attendee_id)
);

CREATE TABLE IF NOT EXISTS distraction_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER NOT NULL,
    attendee_id INTEGER,
    tracking_id INTEGER,
    timestamp DATETIME NOT NULL,
    event_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    snapshot_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
    FOREIGN KEY(attendee_id) REFERENCES attendees(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS seat_zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER NOT NULL,
    seat_index INTEGER NOT NULL,
    x1 INTEGER NOT NULL,
    y1 INTEGER NOT NULL,
    x2 INTEGER NOT NULL,
    y2 INTEGER NOT NULL,
    assigned_attendee_id INTEGER,
    current_status TEXT CHECK(current_status IN ('occupied', 'absent', 'empty')) DEFAULT 'empty',
    FOREIGN KEY(meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
    FOREIGN KEY(assigned_attendee_id) REFERENCES attendees(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_records_meeting ON check_in_records(meeting_id);
CREATE INDEX IF NOT EXISTS idx_records_attendee ON check_in_records(attendee_id);
CREATE INDEX IF NOT EXISTS idx_events_meeting ON distraction_events(meeting_id);
CREATE INDEX IF NOT EXISTS idx_events_attendee ON distraction_events(attendee_id);
CREATE INDEX IF NOT EXISTS idx_zones_meeting ON seat_zones(meeting_id);
"""


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """获取启用了外键约束的数据库连接。"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_database(db_path: Path = DB_PATH):
    """初始化数据库表结构并自动载入初始基准数据。"""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA_SQL)

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM meetings")
        meeting_count = cursor.fetchone()[0]

        if meeting_count == 0:
            cursor.execute(
                """
                INSERT INTO meetings (title, department, host_name, start_time, end_time, expected_count, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "软件工程项目训练 中期进度评审",
                    "研发中心",
                    "夏一帆",
                    "2026-09-08 10:00:00",
                    "2026-09-08 12:00:00",
                    len(INITIAL_ATTENDEES),
                    "in_progress",
                ),
            )
            meeting_id = cursor.lastrowid

            for att in INITIAL_ATTENDEES:
                cursor.execute(
                    """
                    INSERT INTO attendees (employee_id, name, department, position)
                    VALUES (?, ?, ?, ?)
                    """,
                    (att["id"], att["name"], att["department"], att.get("role", "参会成员")),
                )
                att_db_id = cursor.lastrowid
                cursor.execute(
                    """
                    INSERT INTO check_in_records (meeting_id, attendee_id, status)
                    VALUES (?, ?, ?)
                    """,
                    (meeting_id, att_db_id, att.get("status", "present")),
                )
            logger.info(f"数据库初始化完成，已载入默认会议 (ID: {meeting_id}) 与初始参会名单。")
