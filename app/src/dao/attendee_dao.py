"""
参会人员与出勤记录数据访问对象 (DAO)。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from app.config import DB_PATH
from app.resource.db import get_connection
from app.src.common.logger import get_logger
from app.src.model.models import Attendee

logger = get_logger("attendee_dao")


class AttendeeDao:
    """参会人员持久化数据访问类。"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def get_by_meeting_id(self, meeting_id: int) -> List[Attendee]:
        """读取指定会议的参会人员名单与出勤记录。"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.employee_id, a.name, a.department, a.position,
                       c.status, c.duration_seconds, c.distraction_count
                FROM attendees a
                JOIN check_in_records c ON a.id = c.attendee_id
                WHERE c.meeting_id = ?
                ORDER BY a.id ASC
                """,
                (meeting_id,),
            )
            rows = cursor.fetchall()
            return [
                Attendee(
                    id=r["employee_id"],
                    name=r["name"],
                    department=r["department"],
                    role=r["position"] or "参会成员",
                    status=r["status"],
                    distraction_count=r["distraction_count"] or 0,
                    present_duration_seconds=r["duration_seconds"] or 0,
                )
                for r in rows
            ]

    def update_attendance_status(
        self,
        meeting_id: int,
        attendee_id: Union[int, str],
        status: str,
    ) -> bool:
        """更新参会人员在指定会议中的出勤状态（支持员工工号或自增主键）。"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            if isinstance(attendee_id, str) and not attendee_id.isdigit():
                cursor.execute(
                    """
                    UPDATE check_in_records
                    SET status = ?
                    WHERE meeting_id = ? AND attendee_id = (
                        SELECT id FROM attendees WHERE employee_id = ?
                    )
                    """,
                    (status, meeting_id, attendee_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE check_in_records
                    SET status = ?
                    WHERE meeting_id = ? AND attendee_id = ?
                    """,
                    (status, meeting_id, int(attendee_id)),
                )
            return cursor.rowcount > 0
