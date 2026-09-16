"""
会议业务协调控制器 (MeetingController)。
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple, Union
from PySide6.QtCore import QObject

from app.config import DB_PATH, INITIAL_ATTENDEES
from app.resource.db import init_database
from app.src.common.logger import get_logger
from app.src.state.meeting_store import MeetingSessionStore
from app.src.core.seat_tracker import SeatZoneTracker
from app.src.dao.attendee_dao import AttendeeDao
from app.src.dao.meeting_dao import MeetingDao
from app.src.dao.seat_zone_dao import SeatZoneDao
from app.src.model import AttendanceStatus, Attendee, DetectionBox, DistractionAlert, MeetingInfo, SeatZone
from app.src.service.csv_importer import CsvAttendeeImporter
from app.src.service.export_service import AttendanceReportService

logger = get_logger("meeting_controller")


class MeetingController(QObject):
    """协调持久层数据访问与应用状态流转的中枢控制器。"""

    def __init__(self, store: Optional[MeetingSessionStore] = None, db_path: Path = DB_PATH, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.db_path = db_path
        self.store = store or MeetingSessionStore(parent=self)
        self.meeting_dao = MeetingDao(self.db_path)
        self.attendee_dao = AttendeeDao(self.db_path)
        self.seat_zone_dao = SeatZoneDao(self.db_path)
        self.csv_importer = CsvAttendeeImporter(self.db_path)

    def initialize(self) -> None:
        """初始化数据库与当前活跃会话状态。"""
        init_database(self.db_path)
        meeting = self.meeting_dao.get_active()
        attendees = self.attendee_dao.get_by_meeting_id(meeting.id)
        if not attendees:
            attendees = [Attendee(**data) for data in INITIAL_ATTENDEES]
        seat_zones = self.seat_zone_dao.get_by_meeting_id(meeting.id)

        self.store.set_meeting(meeting)
        self.store.set_attendees(attendees)
        self.store.set_seat_zones(seat_zones)

    def switch_meeting(self, new_meeting: MeetingInfo) -> None:
        """切换当前活动会议并重载关联人员与工位。"""
        self.store.set_meeting(new_meeting)
        attendees = self.attendee_dao.get_by_meeting_id(new_meeting.id)
        self.store.set_attendees(attendees)
        seat_zones = self.seat_zone_dao.get_by_meeting_id(new_meeting.id)
        self.store.set_seat_zones(seat_zones)
        logger.info(f"会议已切换至 ID: {new_meeting.id} ({new_meeting.title})")

    def handle_leaving_seat_alert(self, alert: DistractionAlert) -> bool:
        """处理工位离席告警，更新数据库并在状态仓库中标记离席。"""
        target_name = alert.attendee_name
        meeting = self.store.meeting
        if not meeting:
            return False

        matched = False
        for a in self.store.attendees:
            if a.name == target_name:
                self.attendee_dao.update_attendance_status(meeting.id, a.id, AttendanceStatus.ABSENT.value)
                self.store.update_attendee_status(a.id, AttendanceStatus.ABSENT.value)
                matched = True
                break
        return matched

    def handle_distraction_alert(self, alert: DistractionAlert) -> None:
        """处理分心告警，累加目标分心计数值。"""
        if alert.track_id:
            self.store.increment_distraction(alert.track_id)

    def bind_tracking_id(self, attendee_id: str, track_id: str) -> None:
        """绑定人员与目标追踪编号。"""
        tid = track_id.strip()
        if not tid.startswith("#"):
            tid = f"#{tid}"
        self.store.bind_tracking_id(attendee_id, tid)

    def import_roster_csv(self, file_path: Union[str, Path]) -> Tuple[int, int, List[str]]:
        """批量导入参会人员名单并刷新会话状态。"""
        meeting = self.store.meeting
        if not meeting:
            raise ValueError("当前无有效活跃会议")

        added, dups, dup_list = self.csv_importer.import_csv(meeting.id, file_path)
        fresh_attendees = self.attendee_dao.get_by_meeting_id(meeting.id)
        self.store.set_attendees(fresh_attendees)
        fresh_meeting = self.meeting_dao.get_by_id(meeting.id)
        if fresh_meeting:
            self.store.set_meeting(fresh_meeting)
        return added, dups, dup_list

    def add_seat_zone(self, zone: SeatZone) -> SeatZone:
        """持久化并注册新工位区域。"""
        saved = self.seat_zone_dao.save(zone)
        self.store.add_seat_zone(saved)
        return saved

    def auto_generate_seats(
        self,
        detections: List[DetectionBox],
        frame_width: int,
        frame_height: int,
    ) -> List[SeatZone]:
        """根据画面检测人员自动排布工位并批量持久化。"""
        meeting = self.store.meeting
        if not meeting:
            return []

        generated = SeatZoneTracker.auto_generate_zones(
            detections, self.store.attendees, frame_width, frame_height, meeting_id=meeting.id
        )
        if not generated:
            return []

        saved = self.seat_zone_dao.save_all(meeting.id, generated)
        self.store.set_seat_zones(saved)
        return saved

    def sync_seat_zones(self, zones: List[SeatZone]) -> None:
        """同步最新工位列表。"""
        self.store.set_seat_zones(zones)

    def prompt_and_create_seat_zone(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        parent_widget=None,
    ) -> Optional[SeatZone]:
        """弹出工位绑定对话框并完成工位注册持久化。"""
        from PySide6.QtWidgets import QInputDialog

        meeting = self.store.meeting
        if not meeting:
            return None

        next_idx = len(self.store.seat_zones) + 1
        items = ["暂不指派人员"] + [f"{a.name} ({a.department})" for a in self.store.attendees]
        item, ok = QInputDialog.getItem(
            parent_widget,
            "工位人员绑定",
            f"已划定工位 #{next_idx} 几何范围，请选择就座参会人员:",
            items,
            0,
            False,
        )
        if not ok:
            return None

        new_zone = SeatZone(
            meeting_id=meeting.id,
            seat_index=next_idx,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            current_status="empty",
        )
        if item != "暂不指派人员":
            att_name = item.split(" (")[0]
            matched = next((a for a in self.store.attendees if a.name == att_name), None)
            if matched:
                new_zone.assigned_employee_id = matched.id
                new_zone.assigned_attendee_name = matched.name

        return self.add_seat_zone(new_zone)

    def format_import_summary(self, added: int, dups: int, dup_list: List[str]) -> str:
        """格式化 CSV 导入完成摘要信息。"""
        msg = f"名单批量解析入库完成！\n\n• 成功导入新参会人：{added} 人\n• 拦截跳过重复工号：{dups} 人"
        if dup_list:
            preview = ", ".join(dup_list[:5])
            if len(dup_list) > 5:
                preview += f" 等共 {len(dup_list)} 人"
            msg += f"\n  (重复工号: {preview})"
        return msg

    def export_report(self) -> Path:
        """导出当前出勤明细至 Excel。"""
        return AttendanceReportService.export_to_excel(self.store.attendees)
