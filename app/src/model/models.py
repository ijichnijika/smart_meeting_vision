"""
业务模型与数据结构。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from app.src.model.enums import AttendanceStatus


@dataclass
class BBox:
    """几何包围盒值对象，封装边界与重叠计算。"""
    x1: int = 0
    y1: int = 0
    x2: int = 0
    y2: int = 0

    @property
    def width(self) -> int:
        return max(0, self.x2 - self.x1)

    @property
    def height(self) -> int:
        return max(0, self.y2 - self.y1)

    @property
    def center(self) -> Tuple[float, float]:
        return (self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0

    def contains_point(self, x: float, y: float) -> bool:
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def calculate_intersection_ratio(self, x1: float, y1: float, x2: float, y2: float) -> float:
        ix1 = max(float(self.x1), float(x1))
        iy1 = max(float(self.y1), float(y1))
        ix2 = min(float(self.x2), float(x2))
        iy2 = min(float(self.y2), float(y2))
        if ix1 >= ix2 or iy1 >= iy2:
            return 0.0
        inter_area = (ix2 - ix1) * (iy2 - iy1)
        zone_area = max(1.0, float(self.width * self.height))
        return inter_area / zone_area


@dataclass
class Attendee:
    id: str
    name: str
    department: str
    role: str = "参会成员"
    status: str = AttendanceStatus.PRESENT.value
    track_id: Optional[str] = None
    checkin_time: Optional[str] = None
    distraction_count: int = 0
    present_duration_seconds: int = 0

    @property
    def numeric_track_id(self) -> Optional[int]:
        if self.track_id:
            cleaned = self.track_id.lstrip("#")
            return int(cleaned) if cleaned.isdigit() else None
        return None


@dataclass
class MeetingInfo:
    id: Union[int, str] = 0
    title: str = ""
    department: str = ""
    host_name: str = ""
    start_time: str = ""
    end_time: str = ""
    expected_count: int = 0
    status: str = "scheduled"
    room: str = ""
    total_present: int = 0

    @property
    def host(self) -> str:
        return self.host_name

    @host.setter
    def host(self, val: str):
        self.host_name = val

    @property
    def total_expected(self) -> int:
        return self.expected_count

    @total_expected.setter
    def total_expected(self, val: int):
        self.expected_count = val


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

    @property
    def formatted_track_id(self) -> Optional[str]:
        return f"#{self.track_id}" if self.track_id is not None else None

    @property
    def bbox(self) -> BBox:
        return BBox(int(self.x1), int(self.y1), int(self.x2), int(self.y2))


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
    total_expected: int = 0
    current_present: int = 0
    current_absent: int = 0
    distraction_total: int = 0
    attendance_rate: float = 0.0
    category_counts: Optional[dict] = None

    @classmethod
    def calculate(
        cls,
        attendees: List[Attendee],
        distraction_total: int = 0,
        category_counts: Optional[dict] = None,
    ) -> AttendanceStats:
        total = len(attendees)
        present = sum(1 for a in attendees if a.status == AttendanceStatus.PRESENT.value)
        absent = total - present
        rate = round(present / total * 100.0, 1) if total > 0 else 0.0
        return cls(
            total_expected=total,
            current_present=present,
            current_absent=absent,
            distraction_total=distraction_total,
            attendance_rate=rate,
            category_counts=category_counts,
        )


@dataclass
class SeatZone:
    id: Optional[int] = None
    meeting_id: int = 1
    seat_index: int = 1
    x1: int = 0
    y1: int = 0
    x2: int = 0
    y2: int = 0
    assigned_attendee_id: Optional[int] = None
    assigned_attendee_name: Optional[str] = None
    assigned_employee_id: Optional[str] = None
    current_status: str = "empty"

    @property
    def bbox(self) -> BBox:
        return BBox(int(self.x1), int(self.y1), int(self.x2), int(self.y2))

    def contains_point(self, x: float, y: float) -> bool:
        return self.bbox.contains_point(x, y)

    def calculate_intersection_ratio(self, x1: float, y1: float, x2: float, y2: float) -> float:
        return self.bbox.calculate_intersection_ratio(x1, y1, x2, y2)
