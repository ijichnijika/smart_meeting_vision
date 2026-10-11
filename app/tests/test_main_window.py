import os
from dataclasses import replace
from functools import partial

import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture(autouse=True)
def isolate_window_data(tmp_path, monkeypatch):
    from app.src.controller import MeetingController
    from app.src.service.vision_service import VisionService

    monkeypatch.setattr(
        "app.src.ui.main_window.MeetingController",
        partial(MeetingController, db_path=tmp_path / "meeting.db"),
    )
    monkeypatch.setattr(VisionService, "read_raw_frame", lambda self: (False, None))


def test_main_window_initialization():
    """测试主窗口三栏式装配、子面板完整性与组件连接"""
    from app.src.ui import MainWindow

    window = MainWindow(enable_yolo=False, auto_start=False)
    assert window.windowTitle() == "Smart Meeting Vision 智能会议签到与出勤分析系统"

    # 验证三栏核心组件存在
    assert hasattr(window, "attendee_panel")
    assert hasattr(window, "video_widget")
    assert hasattr(window, "control_bar")
    assert hasattr(window, "stats_panel")

    assert window.attendee_panel.get_total_count() > 0

    from app.src.model import AttendanceStats
    mock_stats = AttendanceStats(total_expected=12, current_present=11, current_absent=1, attendance_rate=91.7)
    window._on_stats_updated(mock_stats)

    assert "11 / 12" in window.stats_panel.lbl_present_val.text()

    window.cleanup()
    window.close()


def test_main_window_seat_zone_and_leaving_alert(monkeypatch):
    """测试主窗口工位管理、离席告警触发及考勤状态与面板联动"""
    from app.src.model import DistractionAlert, DetectionBox
    from app.src.ui import MainWindow

    # 模拟弹窗输入选择夏一帆
    from PySide6.QtWidgets import QInputDialog
    monkeypatch.setattr(QInputDialog, "getItem", lambda *args, **kwargs: ("夏一帆 (研发一部)", True))

    window = MainWindow(enable_yolo=False, auto_start=False)

    # 1. 模拟鼠标框选生成新工位
    window._on_seat_zone_drawn(120, 150, 280, 390)
    assert len(window.seat_zones) > 0
    newest_zone = window.seat_zones[-1]
    assert newest_zone.assigned_attendee_name == "夏一帆"

    # 2. 模拟触发连续 15 帧离席告警
    alert = DistractionAlert(
        id="ALT-LEAVE-999",
        track_id="#1",
        attendee_name="夏一帆",
        event_type="leaving_seat",
        event_label="工位离席告警",
        timestamp="14:05:00",
        duration_seconds=5,
    )
    window._on_alert_triggered(alert)

    # 3. 验证考勤状态已自动降级为离席
    emp1 = next(a for a in window.attendees if a.name == "夏一帆")
    assert emp1.status == "absent"
    assert window._current_stats.current_absent > 0
    assert "连续 5 秒" in window.statusBar().currentMessage()

    window.cleanup()
    window.close()


def test_expected_count_tracks_roster_import_meeting_edit_and_switch(tmp_path):
    from app.src.ui import MainWindow

    window = MainWindow(enable_yolo=False, auto_start=False)
    try:
        initial_count = window.meeting.expected_count
        csv_file = tmp_path / "roster.csv"
        csv_file.write_text("工号,姓名,部门\nNEW001,测试员,研发\n", encoding="utf-8")
        window.controller.import_roster_csv(csv_file)
        assert window.vision_service.expected_count == initial_count + 1

        window.store.set_meeting(replace(window.meeting, expected_count=20))
        assert window.vision_service.expected_count == 20
        window.vision_service._update_stats_if_needed(10)
        assert window.store.stats.attendance_rate == 50.0

        new_meeting = window.controller.meeting_dao.save(
            replace(window.meeting, id=0, title="空会议", expected_count=0)
        )
        window._on_meeting_switched(new_meeting)
        assert window.vision_service.expected_count == 0
    finally:
        window.close()
