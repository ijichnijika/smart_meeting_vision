import os

from app.src.model import Attendee, AttendanceStats, DistractionAlert
from app.config import INITIAL_ATTENDEES

os.environ["QT_QPA_PLATFORM"] = "offscreen"


def test_attendee_panel_populate_and_filter():
    """测试 AttendeePanel 加载参会人员与关键字搜索过滤"""
    from app.src.ui.components.attendee_panel import AttendeePanel

    panel = AttendeePanel()
    attendees = [Attendee(**data) for data in INITIAL_ATTENDEES]
    panel.set_attendees(attendees)

    assert panel.get_total_count() == len(attendees)

    # 测试关键字过滤
    panel.search_input.setText("夏一帆")
    visible_count = panel.get_visible_count()
    assert visible_count == 1

    # 清除过滤
    panel.search_input.setText("")
    assert panel.get_visible_count() == len(attendees)


def test_stats_panel_metrics_and_alerts(qapp):
    """测试 StatsPanel 数据指标更新与告警动态流卡片新增"""
    from app.src.ui.components.stats_panel import StatsPanel

    panel = StatsPanel()
    stats = AttendanceStats(
        total_expected=12,
        current_present=10,
        current_absent=2,
        attendance_rate=83.3
    )
    panel.update_stats(stats)
    assert "10" in panel.lbl_present_val.text()
    assert "83.3%" in panel.lbl_rate_val.text()

    # 测试新增告警卡片
    alert = DistractionAlert(
        id="ALT001",
        track_id="#2",
        attendee_name="张文远",
        event_type="using_device",
        event_label="低头玩手机",
        timestamp="10:30:15",
        duration_seconds=3
    )
    panel.add_alert(alert)
    assert panel.get_alert_count() == 1
