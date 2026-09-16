"""
工位区域数据访问对象 (DAO)。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional

from app.config import DB_PATH
from app.resource.db import get_connection
from app.src.common.logger import get_logger
from app.src.model.models import SeatZone

logger = get_logger("seat_zone_dao")


class SeatZoneDao:
    """工位区域持久化数据访问类。"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    @staticmethod
    def _resolve_attendee_db_id(
        cursor: sqlite3.Cursor,
        attendee_id: Optional[int],
        employee_id: Optional[str],
    ) -> Optional[int]:
        if attendee_id is not None:
            return attendee_id
        if employee_id:
            cursor.execute("SELECT id FROM attendees WHERE employee_id = ?", (employee_id,))
            res = cursor.fetchone()
            if res:
                return res[0]
        return None

    def get_by_meeting_id(self, meeting_id: int) -> List[SeatZone]:
        """获取指定会议的所有工位区域列表。"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.id, s.meeting_id, s.seat_index, s.x1, s.y1, s.x2, s.y2,
                       s.assigned_attendee_id, s.current_status,
                       a.name AS attendee_name, a.employee_id
                FROM seat_zones s
                LEFT JOIN attendees a ON s.assigned_attendee_id = a.id
                WHERE s.meeting_id = ?
                ORDER BY s.seat_index ASC
                """,
                (meeting_id,),
            )
            rows = cursor.fetchall()
            return [
                SeatZone(
                    id=int(row["id"]),
                    meeting_id=int(row["meeting_id"]),
                    seat_index=int(row["seat_index"]),
                    x1=int(row["x1"]),
                    y1=int(row["y1"]),
                    x2=int(row["x2"]),
                    y2=int(row["y2"]),
                    assigned_attendee_id=row["assigned_attendee_id"],
                    assigned_attendee_name=row["attendee_name"],
                    assigned_employee_id=row["employee_id"],
                    current_status=row["current_status"] or "empty",
                )
                for row in rows
            ]

    def save(self, zone: SeatZone) -> SeatZone:
        """保存或更新单个工位区域。"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            att_id = self._resolve_attendee_db_id(cursor, zone.assigned_attendee_id, zone.assigned_employee_id)
            zone.assigned_attendee_id = att_id

            if zone.id and int(zone.id) > 0:
                cursor.execute(
                    """
                    UPDATE seat_zones
                    SET seat_index = ?, x1 = ?, y1 = ?, x2 = ?, y2 = ?, assigned_attendee_id = ?, current_status = ?
                    WHERE id = ?
                    """,
                    (zone.seat_index, zone.x1, zone.y1, zone.x2, zone.y2, att_id, zone.current_status, int(zone.id)),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO seat_zones (meeting_id, seat_index, x1, y1, x2, y2, assigned_attendee_id, current_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (zone.meeting_id, zone.seat_index, zone.x1, zone.y1, zone.x2, zone.y2, att_id, zone.current_status),
                )
                zone.id = cursor.lastrowid
            return zone

    def save_all(self, meeting_id: int, zones: List[SeatZone]) -> List[SeatZone]:
        """批量同步保存指定会议的工位配置列表（替换式写入）。"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM seat_zones WHERE meeting_id = ?", (meeting_id,))
            for idx, z in enumerate(zones):
                att_id = self._resolve_attendee_db_id(cursor, z.assigned_attendee_id, z.assigned_employee_id)
                z.assigned_attendee_id = att_id

                cursor.execute(
                    """
                    INSERT INTO seat_zones (meeting_id, seat_index, x1, y1, x2, y2, assigned_attendee_id, current_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (meeting_id, z.seat_index or (idx + 1), z.x1, z.y1, z.x2, z.y2, att_id, z.current_status or "empty"),
                )
                z.id = cursor.lastrowid
                z.meeting_id = meeting_id
        return self.get_by_meeting_id(meeting_id)

    def delete(self, zone_id: int) -> bool:
        """删除单个工位。"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM seat_zones WHERE id = ?", (zone_id,))
            return cursor.rowcount > 0

    def clear(self, meeting_id: int) -> bool:
        """清空指定会议的所有工位。"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM seat_zones WHERE meeting_id = ?", (meeting_id,))
            return cursor.rowcount > 0

    def update_status(self, zone_id: int, status: str) -> bool:
        """更新工位的物理在席状态。"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE seat_zones SET current_status = ? WHERE id = ?", (status, zone_id))
            return cursor.rowcount > 0
