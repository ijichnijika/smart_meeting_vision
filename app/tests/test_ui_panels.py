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

    # 测试状态筛选药丸 (在席 / 离席 / 未关联)
    panel._on_filter_changed("PRESENT")
    assert panel.get_visible_count() == sum(1 for a in attendees if a.status == "present")

    panel._on_filter_changed("ABSENT")
    assert panel.get_visible_count() == sum(1 for a in attendees if a.status != "present")

    panel._on_filter_changed("UNBOUND")
    assert panel.get_visible_count() == sum(1 for a in attendees if not a.track_id)

    panel._on_filter_changed("ALL")
    assert panel.get_visible_count() == len(attendees)


def test_no_emoji_in_ui():
    """验证界面核心组件文本均无 Emoji 字符"""
    import re
    from app.src.ui.components.attendee_panel import AttendeePanel
    from app.src.ui.components.control_bar import ControlBar
    from app.src.ui.components.stats_panel import StatsPanel

    # 常见 Emoji 字符 Unicode 范围
    emoji_pattern = re.compile(
        r"[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50]",
        flags=re.UNICODE
    )

    bar = ControlBar()
    assert not emoji_pattern.search(bar.btn_play.text())
    assert not emoji_pattern.search(bar.btn_restart.text())
    assert not emoji_pattern.search(bar.btn_snapshot.text())

    att_panel = AttendeePanel()
    assert not emoji_pattern.search(att_panel.search_input.placeholderText())

    stats_panel = StatsPanel()
    assert not emoji_pattern.search(stats_panel.lbl_empty_feed.text())
    assert not emoji_pattern.search(stats_panel.btn_export.text())


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


def test_stats_panel_category_counts(qapp):
    """测试 StatsPanel 类别细分标签渲染与数据更新"""
    from app.src.ui.components.stats_panel import StatsPanel

    panel = StatsPanel()
    assert "暂无数据" in panel.lbl_category_detail.text()

    panel.update_category_counts({"person": 5, "cell phone": 1})
    assert "person: 5" in panel.lbl_category_detail.text()
    assert "cell phone: 1" in panel.lbl_category_detail.text()

    stats = AttendanceStats(
        total_expected=12,
        current_present=5,
        current_absent=7,
        category_counts={"person": 6, "sleep": 1}
    )
    panel.update_stats(stats)
    assert "person: 6" in panel.lbl_category_detail.text()
    assert "sleep: 1" in panel.lbl_category_detail.text()
