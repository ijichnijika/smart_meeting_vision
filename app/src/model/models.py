"""
业务模型与数据结构。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Attendee:
    id: str
    name: str
    department: str
    role: str = "参会成员"
    status: str = "present"
    track_id: Optional[str] = None
    checkin_time: Optional[str] = None
    distraction_count: int = 0
    present_duration_seconds: int = 0


@dataclass
class MeetingInfo:
    id: str = "MTG-20260908-01"
    title: str = "软件工程项目训练"
    host: str = "夏一帆"
    room: str = "第一报告厅 (自由席位监控源)"
    date: str = "2026-09-08"
    start_time: str = "10:00"
    end_time: str = "12:00"
    status: str = "active"
    total_expected: int = 12
    total_present: int = 9


@dataclass
class DetectionBox:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str
    track_id: Optional[int] = None
    behavior_label: Optional[str] = None
    is_distracted: bool = False
    bound_attendee_name: Optional[str] = None


@dataclass
class DistractionAlert:
    id: str
    track_id: str
    attendee_name: str
    event_type: str
    event_label: str
    timestamp: str
    duration_seconds: int = 0
    snapshot_path: Optional[str] = None


@dataclass
class AttendanceStats:
    total_expected: int = 12
    current_present: int = 9
    current_absent: int = 3
    distraction_total: int = 2
    attendance_rate: float = 75.0
