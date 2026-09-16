"""
会议数据访问对象 (DAO)。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional

from app.config import DB_PATH
from app.resource.db import get_connection, init_database
from app.src.common.logger import get_logger
from app.src.model.models import MeetingInfo

logger = get_logger("meeting_dao")


class MeetingDao:
    """会议持久化数据访问类。"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def get_active(self) -> MeetingInfo:
        """获取当前活跃会议或最近一次会议记录。"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, title, department, host_name, start_time, end_time, expected_count, status
                FROM meetings
                ORDER BY id DESC LIMIT 1
                """
            )
            row = cursor.fetchone()
            if not row:
                init_database(self.db_path)
                return self.get_active()

            return MeetingInfo(
                id=int(row["id"]),
                title=row["title"],
                department=row["department"],
                host_name=row["host_name"],
                start_time=str(row["start_time"]),
                end_time=str(row["end_time"]),
                expected_count=int(row["expected_count"]),
                status=row["status"],
            )

    def get_all(self) -> List[MeetingInfo]:
        """获取全部会议记录。"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, title, department, host_name, start_time, end_time, expected_count, status
                FROM meetings
                ORDER BY id DESC
                """
            )
            rows = cursor.fetchall()
            return [
                MeetingInfo(
                    id=int(row["id"]),
                    title=row["title"],
                    department=row["department"],
                    host_name=row["host_name"],
                    start_time=str(row["start_time"]),
                    end_time=str(row["end_time"]),
                    expected_count=int(row["expected_count"]),
                    status=row["status"],
                )
                for row in rows
            ]

    def get_by_id(self, meeting_id: int) -> Optional[MeetingInfo]:
        """根据主键 ID 查询会议。"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, title, department, host_name, start_time, end_time, expected_count, status
                FROM meetings
                WHERE id = ?
                """,
                (meeting_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return MeetingInfo(
                id=int(row["id"]),
                title=row["title"],
                department=row["department"],
                host_name=row["host_name"],
                start_time=str(row["start_time"]),
                end_time=str(row["end_time"]),
                expected_count=int(row["expected_count"]),
                status=row["status"],
            )

    def save(self, meeting: MeetingInfo) -> MeetingInfo:
        """创建或更新会议记录。"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            if meeting.id and int(meeting.id) > 0:
                cursor.execute(
                    """
                    UPDATE meetings
                    SET title = ?, department = ?, host_name = ?, start_time = ?, end_time = ?, expected_count = ?, status = ?
                    WHERE id = ?
                    """,
                    (
                        meeting.title,
                        meeting.department,
                        meeting.host_name,
                        meeting.start_time,
                        meeting.end_time,
                        meeting.expected_count,
                        meeting.status,
                        int(meeting.id),
                    ),
                )
                logger.info(f"会议信息更新完成 (ID: {meeting.id}): {meeting.title}")
            else:
                cursor.execute(
                    """
                    INSERT INTO meetings (title, department, host_name, start_time, end_time, expected_count, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        meeting.title,
                        meeting.department,
                        meeting.host_name,
                        meeting.start_time,
                        meeting.end_time,
                        meeting.expected_count,
                        meeting.status,
                    ),
                )
                meeting.id = cursor.lastrowid
                logger.info(f"新会议已创建 (ID: {meeting.id}): {meeting.title}")
            return meeting

    def delete(self, meeting_id: int) -> bool:
        """根据主键 ID 级联删除会议。"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"已删除会议记录 (ID: {meeting_id})")
            return deleted
