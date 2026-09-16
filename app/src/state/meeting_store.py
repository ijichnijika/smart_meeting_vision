"""
会议业务会话集中状态存储器
"""

from __future__ import annotations

from typing import List, Optional
from PySide6.QtCore import QObject, Signal

from app.src.model import AttendanceStats, AttendanceStatus, Attendee, MeetingInfo, SeatZone


class MeetingSessionStore(QObject):
    """集中响应式状态仓库，负责持有当前会话的核心数据并向订阅者广播变更。"""

    meeting_changed = Signal(object)
    attendees_changed = Signal(list)
    seat_zones_changed = Signal(list)
    stats_changed = Signal(object)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._meeting: Optional[MeetingInfo] = None
        self._attendees: List[Attendee] = []
        self._seat_zones: List[SeatZone] = []
        self._stats: AttendanceStats = AttendanceStats()

    @property
    def meeting(self) -> Optional[MeetingInfo]:
        return self._meeting

    @property
    def attendees(self) -> List[Attendee]:
        return list(self._attendees)

    @property
    def seat_zones(self) -> List[SeatZone]:
        return list(self._seat_zones)

    @property
    def stats(self) -> AttendanceStats:
        return self._stats

    def set_meeting(self, meeting: MeetingInfo) -> None:
        self._meeting = meeting
        self.meeting_changed.emit(meeting)

    def set_attendees(self, attendees: List[Attendee]) -> None:
        self._attendees = list(attendees)
        self._recalculate_stats()
        self.attendees_changed.emit(self._attendees)

    def set_seat_zones(self, zones: List[SeatZone]) -> None:
        self._seat_zones = list(zones)
        self.seat_zones_changed.emit(self._seat_zones)

    def set_stats(self, stats: AttendanceStats) -> None:
        self._stats = stats
        self.stats_changed.emit(self._stats)

    def update_attendee_status(self, attendee_id: str, status: str) -> bool:
        """更新参会人在席状态并自动重新计算出勤统计。"""
        matched = False
        for a in self._attendees:
            if a.id == attendee_id or a.name == attendee_id:
                a.status = status
                matched = True
                break

        if matched:
            self._recalculate_stats()
            self.attendees_changed.emit(self._attendees)
        return matched

    def increment_distraction(self, track_id_or_clean: str) -> bool:
        """根据 TrackingID 累加分心计数值。"""
        tid_clean = track_id_or_clean.lstrip("#")
        matched = False
        for a in self._attendees:
            if a.track_id and (a.track_id == track_id_or_clean or a.track_id.lstrip("#") == tid_clean):
                a.distraction_count += 1
                matched = True
                break

        if matched:
            self.attendees_changed.emit(self._attendees)
        return matched

    def bind_tracking_id(self, attendee_id: str, track_id: str) -> bool:
        """绑定参会人与临时目标追踪编号。"""
        for a in self._attendees:
            if a.id == attendee_id:
                a.track_id = track_id
                self.attendees_changed.emit(self._attendees)
                return True
        return False

    def add_seat_zone(self, zone: SeatZone) -> None:
        """新增单个工位区域。"""
        self._seat_zones.append(zone)
        self.seat_zones_changed.emit(self._seat_zones)

    def _recalculate_stats(self) -> None:
        """依据当前参会人员名单重新计算考勤统计指标。"""
        total = len(self._attendees)
        present = sum(1 for a in self._attendees if a.status == AttendanceStatus.PRESENT.value)
        absent = total - present
        rate = round(present / total * 100.0, 1) if total > 0 else 0.0

        self._stats = AttendanceStats(
            total_expected=total,
            current_present=present,
            current_absent=absent,
            distraction_total=self._stats.distraction_total,
            attendance_rate=rate,
            category_counts=self._stats.category_counts,
        )
        self.stats_changed.emit(self._stats)
