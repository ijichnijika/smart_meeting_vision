"""
数据库持久化服务门面，委托调用底层 DAO 与导入器。
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple, Union

from app.config import DB_PATH
from app.resource.db import get_connection, init_database
from app.src.dao.attendee_dao import AttendeeDao
from app.src.dao.meeting_dao import MeetingDao
from app.src.dao.seat_zone_dao import SeatZoneDao
from app.src.model.models import Attendee, MeetingInfo, SeatZone
from app.src.service.csv_importer import CsvAttendeeImporter


def get_active_meeting(db_path: Path = DB_PATH) -> MeetingInfo:
    return MeetingDao(db_path).get_active()


def get_all_meetings(db_path: Path = DB_PATH) -> List[MeetingInfo]:
    return MeetingDao(db_path).get_all()


def get_meeting_by_id(meeting_id: int, db_path: Path = DB_PATH) -> Optional[MeetingInfo]:
    return MeetingDao(db_path).get_by_id(meeting_id)


def delete_meeting(meeting_id: int, db_path: Path = DB_PATH) -> bool:
    return MeetingDao(db_path).delete(meeting_id)


def save_meeting(meeting: MeetingInfo, db_path: Path = DB_PATH) -> MeetingInfo:
    return MeetingDao(db_path).save(meeting)


def get_attendees(meeting_id: int, db_path: Path = DB_PATH) -> List[Attendee]:
    return AttendeeDao(db_path).get_by_meeting_id(meeting_id)


def update_attendee_attendance_status(
    meeting_id: int,
    attendee_id: Union[int, str],
    status: str,
    db_path: Path = DB_PATH,
) -> bool:
    return AttendeeDao(db_path).update_attendance_status(meeting_id, attendee_id, status)


def get_seat_zones(meeting_id: int, db_path: Path = DB_PATH) -> List[SeatZone]:
    return SeatZoneDao(db_path).get_by_meeting_id(meeting_id)


def save_seat_zone(zone: SeatZone, db_path: Path = DB_PATH) -> SeatZone:
    return SeatZoneDao(db_path).save(zone)


def save_seat_zones(meeting_id: int, zones: List[SeatZone], db_path: Path = DB_PATH) -> List[SeatZone]:
    return SeatZoneDao(db_path).save_all(meeting_id, zones)


def delete_seat_zone(zone_id: int, db_path: Path = DB_PATH) -> bool:
    return SeatZoneDao(db_path).delete(zone_id)


def clear_seat_zones(meeting_id: int, db_path: Path = DB_PATH) -> bool:
    return SeatZoneDao(db_path).clear(meeting_id)


def update_seat_zone_status(zone_id: int, status: str, db_path: Path = DB_PATH) -> bool:
    return SeatZoneDao(db_path).update_status(zone_id, status)


def import_attendees_csv(
    meeting_id: int,
    file_path: Union[str, Path],
    db_path: Path = DB_PATH,
) -> Tuple[int, int, List[str]]:
    return CsvAttendeeImporter(db_path).import_csv(meeting_id, file_path)
