import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"


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
