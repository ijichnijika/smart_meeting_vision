"""
会议签到与出勤分析系统主窗口。
"""

from datetime import datetime
import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
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
    DEFAULT_DEMO_VIDEO,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    INITIAL_ATTENDEES,
    SNAPSHOTS_DIR,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from app.src.common.logger import get_logger
from app.src.model import AttendanceStats, AttendanceStatus, Attendee, DistractionAlert
from app.src.service import AttendanceReportService, VisionService
from app.src.ui.components.attendee_panel import AttendeePanel
from app.src.ui.components.control_bar import ControlBar
from app.src.ui.components.stats_panel import StatsPanel
from app.src.ui.components.top_nav import TopNavWidget
from app.src.ui.components.video_widget import VideoWidget
from app.src.ui.theme import PURE_WHITE_STYLESHEET
from app.src.utils.calculate_utils import current_time_str

logger = get_logger("main_window")


class MainWindow(QMainWindow):
    """会议出勤视觉分析系统主窗口控制器。"""

    def __init__(self, enable_yolo: bool = True, auto_start: bool = True, parent=None):
        super().__init__(parent)
        self.enable_yolo = enable_yolo
        self.auto_start = auto_start
        self.attendees = [Attendee(**data) for data in INITIAL_ATTENDEES]
        self._current_stats = AttendanceStats(
            total_expected=len(self.attendees),
            current_present=sum(1 for a in self.attendees if a.status == AttendanceStatus.PRESENT.value),
            current_absent=sum(1 for a in self.attendees if a.status != AttendanceStatus.PRESENT.value),
            attendance_rate=round(sum(1 for a in self.attendees if a.status == AttendanceStatus.PRESENT.value) / len(self.attendees) * 100, 1),
        )

        self._setup_window_properties()
        self._setup_ui()
        self._setup_vision_service()
        self._bind_events()
        self._start_clock_timer()

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
        self.attendee_panel.set_attendees(self.attendees)
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
        self.stats_panel.update_stats(self._current_stats)
        content_layout.addWidget(self.stats_panel)

        root_layout.addWidget(content_frame, stretch=1)

    def _setup_vision_service(self):
        source = str(DEFAULT_DEMO_VIDEO)
        self.vision_service = VisionService(
            video_source=source,
            enable_yolo=self.enable_yolo,
            parent=self,
        )
        self.vision_service.frame_ready.connect(self._on_frame_ready)
        self.vision_service.done_signal.connect(self._on_done_signal)
        self.vision_service.stats_updated.connect(self._on_stats_updated)
        self.vision_service.alert_triggered.connect(self._on_alert_triggered)
        if self.auto_start:
            self.vision_service.start()

    def _bind_events(self):
        """绑定组件交互信号与槽。"""
        self.control_bar.play_toggled.connect(self._on_play_toggled)
        self.control_bar.restart_clicked.connect(self._on_restart_clicked)
        self.control_bar.source_changed.connect(self._on_source_changed)
        self.control_bar.snapshot_requested.connect(self._on_snapshot_requested)
        self.control_bar.record_toggled.connect(self._on_record_toggled)

        self.video_widget.tracking_id_selected.connect(self._on_tracking_id_selected)
        self.attendee_panel.bind_requested.connect(self._on_bind_requested)
        self.stats_panel.export_report_requested.connect(self._on_export_report)

    def _start_clock_timer(self):
        """每秒刷新顶栏时钟。"""
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(
            lambda: self.top_nav.update_clock(current_time_str("%Y-%m-%d  %H:%M:%S"))
        )
        self.clock_timer.start(1000)

    def _on_frame_ready(self, q_image, detections, fps):
        """接收视频帧与检测目标，关联参会人实名后更新画布。"""
        track_to_name = {a.track_id: a.name for a in self.attendees if a.track_id}
        for det in detections:
            if det.track_id is None:
                continue
            tid_str = f"#{det.track_id}"
            if tid_str in track_to_name:
                det.bound_attendee_name = track_to_name[tid_str]

        self.video_widget.update_frame(q_image, detections, fps)

    def _on_stats_updated(self, stats: AttendanceStats):
        self._current_stats = stats
        self.stats_panel.update_stats(stats)

    def _on_done_signal(self, frame: np.ndarray, counts: dict):
        self.stats_panel.update_category_counts(counts)

    def _on_alert_triggered(self, alert: DistractionAlert):
        self.stats_panel.add_alert(alert)
        if alert.track_id:
            tid_clean = alert.track_id.lstrip("#")
            for a in self.attendees:
                if a.track_id and (a.track_id == alert.track_id or a.track_id.lstrip("#") == tid_clean):
                    a.distraction_count += 1
                    self.attendee_panel.set_attendees(self.attendees)
                    break

    def _on_play_toggled(self, is_playing: bool):
        if is_playing:
            self.vision_service.resume()
        else:
            self.vision_service.pause()

    def _on_restart_clicked(self):
        self.vision_service.change_source(self.vision_service.video_source)
        self.control_bar.set_play_state(True)

    def _on_source_changed(self, new_source):
        self.vision_service.change_source(new_source)
        self.control_bar.set_play_state(True)

    def _on_record_toggled(self, is_recording: bool):
        """响应录制按钮状态变更。"""
        if is_recording:
            path = self.vision_service.start_recording()
            self.statusBar().showMessage(f"已启动录制: {path}", 4000)
        else:
            path = self.vision_service.stop_recording()
            if path:
                QMessageBox.information(self, "录制完成", f"带标注视频已成功保存至:\n{path}")

    def _on_snapshot_requested(self):
        """保存当前视频帧抓拍快照。"""
        snap_path = self.vision_service.take_snapshot()
        if not snap_path and self.video_widget.current_frame and not self.video_widget.current_frame.isNull():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"manual_snap_{ts}.jpg"
            save_path = SNAPSHOTS_DIR / filename
            self.video_widget.current_frame.save(str(save_path), "JPG")
            snap_path = str(save_path)

        if snap_path:
            QMessageBox.information(self, "抓拍完成", f"当前带算法标注画面已保存至:\n{snap_path}")

    def _on_tracking_id_selected(self, track_id: int):
        logger.info(f"画面选中 TrackingID: #{track_id}")

    def _on_bind_requested(self, attendee_id: str):
        """关联参会人员与目标跟踪标识。"""
        att = next((a for a in self.attendees if a.id == attendee_id), None)
        if not att:
            return

        text, ok = QInputDialog.getText(
            self, "挂载目标标识",
            f"请输入要关联至【{att.name} ({att.department})】的 TrackingID:\n(例如: #1, #2)",
            text=att.track_id or "#1",
        )
        if not ok or not text.strip():
            return

        tid = text.strip()
        if not tid.startswith("#"):
            tid = f"#{tid}"
        att.track_id = tid
        self.attendee_panel.update_attendee_binding(attendee_id, tid)
        logger.info(f"参会人员 {att.name} 挂载至 {tid}")

    def _on_export_report(self):
        """导出考勤分析报表至 Excel 文件。"""
        try:
            export_path = AttendanceReportService.export_to_excel(self.attendees)
            QMessageBox.information(
                self, "报表导出成功",
                f"会议考勤出勤分析表已成功生成：\n{export_path}",
            )
        except Exception as e:
            logger.error(f"导出考勤报表失败: {e}", exc_info=True)
            QMessageBox.warning(self, "导出失败", f"生成报表发生异常: {e}")

    def cleanup(self):
        """释放后台线程与定时器资源。"""
        if hasattr(self, "clock_timer") and self.clock_timer.isActive():
            self.clock_timer.stop()
        if hasattr(self, "vision_service"):
            self.vision_service.stop()

    def closeEvent(self, event):
        """窗口关闭处理。"""
        self.cleanup()
        event.accept()
