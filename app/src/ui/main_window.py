"""
会议签到与出勤分析系统主窗口。
"""

from __future__ import annotations

from typing import List
import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from app.config import (
    APP_NAME,
    APP_SUBTITLE,
    DATA_DIR,
    DEFAULT_DEMO_VIDEO,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from app.src.common.logger import get_logger
from app.src.controller import MeetingController
from app.src.model import AttendanceStats, Attendee, DistractionAlert, MeetingInfo, SeatZone
from app.src.service import VisionService
from app.src.state import MeetingSessionStore
from app.src.ui.components.attendee_panel import AttendeePanel
from app.src.ui.components.control_bar import ControlBar
from app.src.ui.components.db_dialog import DatabaseViewerDialog
from app.src.ui.components.meeting_dialog import MeetingEditDialog, MeetingManagerDialog
from app.src.ui.components.seat_dialog import SeatZoneDialog
from app.src.ui.components.stats_panel import StatsPanel
from app.src.ui.components.top_nav import TopNavWidget
from app.src.ui.components.video_widget import VideoWidget
from app.src.ui.theme import PURE_WHITE_STYLESHEET
from app.src.utils.calculate_utils import current_time_str

logger = get_logger("main_window")


class MainWindow(QMainWindow):
    """主窗口视图：负责控件排版、Qt 信号分发与控制器交互。"""

    def __init__(self, enable_yolo: bool = True, auto_start: bool = False, parent=None):
        super().__init__(parent)
        self.enable_yolo = enable_yolo
        self.auto_start = auto_start

        self.store = MeetingSessionStore(parent=self)
        self.controller = MeetingController(store=self.store, parent=self)
        self.controller.initialize()

        self._setup_window_properties()
        self._setup_ui()
        self._setup_vision_service()
        self._bind_events()
        self._subscribe_store()
        self._start_clock_timer()

        # 初始视图渲染
        self.attendee_panel.update_meeting_info(self.store.meeting)
        self.attendee_panel.set_attendees(self.store.attendees)
        self.video_widget.set_seat_zones(self.store.seat_zones)
        self.vision_service.set_seat_zones(self.store.seat_zones)
        self.stats_panel.update_stats(self.store.stats)

        if not self.auto_start:
            self.control_bar.set_play_state(False)
            ret, first_frame = self.vision_service.read_raw_frame()
            if ret and first_frame is not None:
                q_img = self.vision_service.convert_cv_to_qimage(first_frame)
                self.video_widget.update_frame(q_img, [], 0.0)
            self.statusBar().showMessage("系统就绪，请选择输入源或点击【播放】开始分析", 5000)

    @property
    def meeting(self) -> MeetingInfo:
        return self.store.meeting

    @property
    def attendees(self) -> List[Attendee]:
        return self.store.attendees

    @property
    def seat_zones(self) -> List[SeatZone]:
        return self.store.seat_zones

    @property
    def _current_stats(self) -> AttendanceStats:
        return self.store.stats

    def _setup_window_properties(self):
        self.setWindowTitle(f"{APP_NAME} {APP_SUBTITLE}")
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.setStyleSheet(PURE_WHITE_STYLESHEET)

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.top_nav = TopNavWidget()
        root_layout.addWidget(self.top_nav)

        content_frame = QWidget()
        content_frame.setObjectName("contentFrame")
        content_layout = QHBoxLayout(content_frame)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(12)

        self.attendee_panel = AttendeePanel()
        content_layout.addWidget(self.attendee_panel)

        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(10)

        self.video_widget = VideoWidget()
        center_layout.addWidget(self.video_widget, stretch=1)

        self.control_bar = ControlBar()
        center_layout.addWidget(self.control_bar)
        content_layout.addWidget(center_container, stretch=1)

        self.stats_panel = StatsPanel()
        content_layout.addWidget(self.stats_panel)

        root_layout.addWidget(content_frame, stretch=1)

    def _setup_vision_service(self):
        self.vision_service = VisionService(
            video_source=str(DEFAULT_DEMO_VIDEO),
            enable_yolo=self.enable_yolo,
            expected_count=self.meeting.expected_count if self.meeting else 12,
            parent=self,
        )
        self.vision_service.frame_ready.connect(self._on_frame_ready)
        self.vision_service.done_signal.connect(lambda f, c: self.stats_panel.update_category_counts(c))
        self.vision_service.stats_updated.connect(self._on_stats_updated)
        self.vision_service.alert_triggered.connect(self._on_alert_triggered)
        if self.auto_start:
            self.vision_service.start()

    def _on_stats_updated(self, stats: AttendanceStats):
        self.store.set_stats(stats)

    def _subscribe_store(self):
        self.store.meeting_changed.connect(self.attendee_panel.update_meeting_info)
        self.store.attendees_changed.connect(self.attendee_panel.set_attendees)
        self.store.seat_zones_changed.connect(self.video_widget.set_seat_zones)
        self.store.seat_zones_changed.connect(self.vision_service.set_seat_zones)
        self.store.stats_changed.connect(self.stats_panel.update_stats)

    def _bind_events(self):
        self.control_bar.play_toggled.connect(self._on_play_toggled)
        self.control_bar.restart_clicked.connect(self._on_restart_clicked)
        self.control_bar.source_changed.connect(self._on_source_changed)
        self.control_bar.snapshot_requested.connect(self._on_snapshot_requested)
        self.control_bar.record_toggled.connect(self._on_record_toggled)
        self.control_bar.seat_zones_requested.connect(self._on_open_seat_manager)

        self.video_widget.seat_zone_drawn.connect(self._on_seat_zone_drawn)
        self.vision_service.seat_zones_updated.connect(self.controller.sync_seat_zones)

        self.attendee_panel.bind_requested.connect(self._on_bind_requested)
        self.attendee_panel.manage_meetings_requested.connect(self._on_open_meeting_manager)
        self.attendee_panel.edit_meeting_requested.connect(self._on_open_meeting_manager)
        self.attendee_panel.import_csv_requested.connect(self._on_import_csv)
        self.stats_panel.export_report_requested.connect(self._on_export_report)
        self.top_nav.db_viewer_requested.connect(lambda: DatabaseViewerDialog(parent=self).exec())
        self.top_nav.meeting_manager_requested.connect(self._on_open_meeting_manager)
        self.top_nav.seat_zones_requested.connect(self._on_open_seat_manager)

    def _start_clock_timer(self):
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(lambda: self.top_nav.update_clock(current_time_str("%Y-%m-%d  %H:%M:%S")))
        self.clock_timer.start(1000)

    def _on_play_toggled(self, is_playing: bool):
        if is_playing:
            if not self.vision_service.isRunning():
                self.vision_service.is_paused = False
                self.vision_service.start()
            else:
                self.vision_service.resume()
        else:
            self.vision_service.pause()

    def _on_frame_ready(self, q_image, detections, fps):
        track_to_name = {a.track_id: a.name for a in self.attendees if a.track_id}
        for det in detections:
            if det.track_id is not None and f"#{det.track_id}" in track_to_name:
                det.bound_attendee_name = track_to_name[f"#{det.track_id}"]
        self.video_widget.update_frame(q_image, detections, fps)

    def _on_alert_triggered(self, alert: DistractionAlert):
        self.stats_panel.add_alert(alert)
        if alert.event_type == "leaving_seat":
            matched = self.controller.handle_leaving_seat_alert(alert)
            msg = f"【离席告警】{alert.attendee_name} 已连续 3 秒不在工位" if matched else f"【离席告警】{alert.attendee_name}（未绑定人员）连续 3 秒无人"
            self.statusBar().showMessage(msg, 5000)
        elif alert.track_id:
            self.controller.handle_distraction_alert(alert)

    def _on_restart_clicked(self):
        if not self.vision_service.isRunning():
            self.vision_service.is_paused = False
            self.vision_service.start()
        else:
            self.vision_service.change_source(self.vision_service.video_source)
            self.vision_service.resume()
        self.control_bar.set_play_state(True)

    def _on_source_changed(self, new_source):
        if not self.vision_service.isRunning():
            self.vision_service.video_source = new_source
            self.vision_service.is_paused = False
            self.vision_service.start()
        else:
            self.vision_service.change_source(new_source)
            self.vision_service.resume()
        self.control_bar.set_play_state(True)

    def _on_record_toggled(self, is_recording: bool):
        if is_recording:
            path = self.vision_service.start_recording()
            self.statusBar().showMessage(f"已启动录制: {path}", 4000)
        else:
            path = self.vision_service.stop_recording()
            if path:
                QMessageBox.information(self, "录制完成", f"带标注视频已保存至:\n{path}")

    def _on_snapshot_requested(self):
        snap_path = self.vision_service.take_snapshot()
        if snap_path:
            QMessageBox.information(self, "抓拍完成", f"当前画面已保存至:\n{snap_path}")

    def _on_bind_requested(self, attendee_id: str):
        att = next((a for a in self.attendees if a.id == attendee_id), None)
        if not att:
            return
        text, ok = QInputDialog.getText(
            self, "挂载目标标识",
            f"请输入要关联至【{att.name} ({att.department})】的 TrackingID:\n(例如: #1, #2)",
            text=att.track_id or "#1",
        )
        if ok and text.strip():
            self.controller.bind_tracking_id(attendee_id, text)

    def _on_open_meeting_manager(self):
        dialog = MeetingManagerDialog(current_meeting_id=self.meeting.id, parent=self)
        dialog.meeting_switched.connect(self._on_meeting_switched)
        dialog.meeting_updated.connect(lambda m: self.store.set_meeting(m))
        dialog.exec()

    def _on_meeting_switched(self, new_meeting: MeetingInfo):
        self.controller.switch_meeting(new_meeting)
        self.vision_service.expected_count = new_meeting.expected_count
        self.statusBar().showMessage(f"当前会议已切换为: {new_meeting.title}", 4000)

    def _on_import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择参会人员名单 CSV 文件", str(DATA_DIR), "CSV 名单文件 (*.csv);;所有文件 (*)")
        if not file_path:
            return
        try:
            added, dups, dup_list = self.controller.import_roster_csv(file_path)
            QMessageBox.information(self, "名单导入完成", self.controller.format_import_summary(added, dups, dup_list))
            self.statusBar().showMessage(f"已成功导入 {added} 名参会人员，拦截 {dups} 名重复人员", 4000)
        except Exception as e:
            logger.error(f"导入名单失败: {e}", exc_info=True)
            QMessageBox.critical(self, "导入失败", f"CSV 名单解析异常：\n{e}")

    def _on_open_seat_manager(self):
        dialog = SeatZoneDialog(meeting_id=self.meeting.id, attendees=self.attendees, seat_zones=self.seat_zones, parent=self)
        dialog.draw_new_requested.connect(lambda: self.video_widget.set_drawing_seat_mode(True))
        dialog.auto_generate_requested.connect(self._on_auto_generate_seats)
        dialog.zones_updated.connect(self.controller.sync_seat_zones)
        dialog.exec()

    def _on_seat_zone_drawn(self, x1: int, y1: int, x2: int, y2: int):
        saved = self.controller.prompt_and_create_seat_zone(x1, y1, x2, y2, parent_widget=self)
        if saved:
            self.statusBar().showMessage(f"工位 #{saved.seat_index} 划定成功并已保存入库", 4000)

    def _on_auto_generate_seats(self):
        cur_dets = self.video_widget.detections
        if not cur_dets:
            QMessageBox.information(self, "智能生成工位", "当前视频画面中未检出人员目标，请确保视频正在播放。")
            return
        w = self.video_widget.current_frame.width() if self.video_widget.current_frame else 1920
        h = self.video_widget.current_frame.height() if self.video_widget.current_frame else 1080
        saved = self.controller.auto_generate_seats(cur_dets, w, h)
        if saved:
            QMessageBox.information(self, "工位生成完成", f"已自动生成并保存 {len(saved)} 个工位区域！")
            self.statusBar().showMessage(f"已自动划定 {len(saved)} 个工位区域并保存入库", 4000)
        else:
            QMessageBox.information(self, "智能生成工位", "未找到适合划定工位的人员目标。")

    def _on_export_report(self):
        try:
            path = self.controller.export_report()
            QMessageBox.information(self, "报表导出成功", f"考勤分析表已成功生成：\n{path}")
        except Exception as e:
            logger.error(f"导出失败: {e}", exc_info=True)
            QMessageBox.warning(self, "导出失败", f"生成报表发生异常: {e}")

    def cleanup(self):
        if hasattr(self, "clock_timer") and self.clock_timer.isActive():
            self.clock_timer.stop()
        if hasattr(self, "vision_service"):
            self.vision_service.stop()

    def closeEvent(self, event):
        self.cleanup()
        event.accept()
