"""
工位区域划定与时序离席防抖检测测试套件。
"""

import os
from pathlib import Path
import numpy as np
import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QImage, QColor

from app.src.core.drawer import render_seat_leave_snapshot, render_seat_zones
from app.src.core.seat_tracker import SeatZoneTracker
from app.src.model import Attendee, DetectionBox, SeatZone
from app.resource.db import init_database
from app.src.service.db_service import (
    clear_seat_zones,
    delete_seat_zone,
    get_attendees,
    get_seat_zones,
    save_seat_zone,
    save_seat_zones,
    update_attendee_attendance_status,
    update_seat_zone_status,
)

os.environ["QT_QPA_PLATFORM"] = "offscreen"


def test_seat_zone_model_geometry():
    """测试 SeatZone 数据模型的包含判定与重叠率计算"""
    zone = SeatZone(
        id=1,
        meeting_id=1,
        seat_index=1,
        x1=100,
        y1=100,
        x2=300,
        y2=400,
        assigned_attendee_name="夏一帆",
    )
    assert zone.seat_index == 1
    assert zone.contains_point(200, 250) is True
    assert zone.contains_point(50, 50) is False

    # 包含重叠计算
    overlap_ratio = zone.calculate_intersection_ratio(100, 100, 300, 400)
    assert pytest.approx(overlap_ratio, 0.01) == 1.0

    # 部分重叠
    partial_ratio = zone.calculate_intersection_ratio(200, 100, 400, 400)
    assert 0.45 < partial_ratio < 0.55

    # 无重叠
    no_ratio = zone.calculate_intersection_ratio(400, 500, 600, 700)
    assert no_ratio == 0.0


def test_seat_zone_db_crud_lifecycle(tmp_path: Path):
    """测试工位持久化层完整生命周期管理"""
    db_file = tmp_path / "test_seat.db"
    init_database(db_file)

    # 1. 初始工位为空
    initial_zones = get_seat_zones(1, db_file)
    assert len(initial_zones) == 0

    # 2. 单个保存工位并关联工号
    zone1 = SeatZone(
        meeting_id=1,
        seat_index=1,
        x1=80,
        y1=120,
        x2=260,
        y2=380,
        assigned_employee_id="EMP001",
        current_status="occupied",
    )
    saved = save_seat_zone(zone1, db_file)
    assert saved.id is not None
    assert saved.id > 0

    # 3. 查询并验证姓名自动关联
    loaded = get_seat_zones(1, db_file)
    assert len(loaded) == 1
    assert loaded[0].seat_index == 1
    assert loaded[0].assigned_attendee_name == "夏一帆"
    assert loaded[0].current_status == "occupied"

    # 4. 更新工位状态
    update_seat_zone_status(saved.id, "absent", db_file)
    reloaded = get_seat_zones(1, db_file)
    assert reloaded[0].current_status == "absent"

    # 5. 同步更新参会人出勤考勤状态
    update_attendee_attendance_status(1, "EMP001", "absent", db_file)
    attendees = get_attendees(1, db_file)
    emp1 = next(a for a in attendees if a.id == "EMP001")
    assert emp1.status == "absent"

    # 6. 批量保存与替换工位
    batch_zones = [
        SeatZone(meeting_id=1, seat_index=1, x1=50, y1=50, x2=150, y2=150, assigned_employee_id="EMP001"),
        SeatZone(meeting_id=1, seat_index=2, x1=200, y1=50, x2=300, y2=150, assigned_employee_id="EMP002"),
    ]
    batch_saved = save_seat_zones(1, batch_zones, db_file)
    assert len(batch_saved) == 2
    assert batch_saved[0].assigned_attendee_name == "夏一帆"
    assert batch_saved[1].assigned_attendee_name == "张文远"

    # 7. 单条删除与全部清空
    assert delete_seat_zone(batch_saved[0].id, db_file) is True
    assert len(get_seat_zones(1, db_file)) == 1

    assert clear_seat_zones(1, db_file) is True
    assert len(get_seat_zones(1, db_file)) == 0


def test_seat_tracker_debounce_and_leaving_seat_alert(tmp_path: Path):
    """测试连续 15 帧在工位内未检测到目标时严格触发离席防抖判定与告警"""
    tracker = SeatZoneTracker(debounce_frames=15, recovery_frames=3)
    zone = SeatZone(
        id=1,
        meeting_id=1,
        seat_index=1,
        x1=100,
        y1=100,
        x2=200,
        y2=250,
        assigned_attendee_name="夏一帆",
        current_status="empty",
    )
    tracker.set_zones([zone])

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    person_det = DetectionBox(
        x1=110, y1=110, x2=190, y2=240,
        confidence=0.92, class_id=0, class_name="person",
        track_id=1, behavior_label="look_forward",
    )

    # 1. 目标在席：状态应转为 occupied
    zones, alerts, changed = tracker.update(frame, [person_det])
    assert zones[0].current_status == "occupied"
    assert len(alerts) == 0

    # 2. 连续 1 到 14 帧目标消失：处于防抖缓冲期，不应判定离席
    for f_idx in range(14):
        zones, alerts, changed = tracker.update(frame, [])
        assert zones[0].current_status == "occupied"
        assert len(alerts) == 0, f"在第 {f_idx + 1} 帧误触发离席告警"

    # 3. 达到第 15 帧：触发离席判定与告警（快照由上层 VisionService 负责）
    zones, alerts, changed = tracker.update(frame, [])
    assert len(alerts) == 1
    assert alerts[0].event_type == "leaving_seat"
    assert alerts[0].attendee_name == "夏一帆"
    assert alerts[0].snapshot_path is None
    assert zones[0].current_status == "absent"
    assert changed is True

    # 4. 持续无人：不应重复发射告警
    zones, alerts, changed = tracker.update(frame, [])
    assert len(alerts) == 0
    assert zones[0].current_status == "absent"

    # 5. 人员重新归座：前 2 帧防抖缓冲，第 3 帧恢复在席
    zones, alerts, changed = tracker.update(frame, [person_det])
    assert zones[0].current_status == "absent"

    zones, alerts, changed = tracker.update(frame, [person_det])
    assert zones[0].current_status == "absent"

    zones, alerts, changed = tracker.update(frame, [person_det])
    assert zones[0].current_status == "occupied"
    assert changed is True


def test_auto_generate_zones_spatial_layout():
    """测试根据检测目标自动生成工位布局并与参会人员按序配对"""
    dets = [
        DetectionBox(x1=300, y1=100, x2=400, y2=250, confidence=0.9, class_id=0, class_name="person"),
        DetectionBox(x1=100, y1=100, x2=200, y2=250, confidence=0.9, class_id=0, class_name="person"),
        DetectionBox(x1=50, y1=50, x2=80, y2=100, confidence=0.8, class_id=67, class_name="cell phone"),
    ]
    attendees = [
        Attendee(id="EMP001", name="夏一帆", department="研发一部"),
        Attendee(id="EMP002", name="张文远", department="研发一部"),
    ]

    generated = SeatZoneTracker.auto_generate_zones(dets, attendees, frame_width=640, frame_height=480)
    # 手机目标应被排除，生成 2 个工位
    assert len(generated) == 2
    # 左侧目标 (x1=100) 排在第 1，绑定夏一帆
    assert generated[0].seat_index == 1
    assert generated[0].assigned_attendee_name == "夏一帆"
    assert generated[0].x1 < generated[1].x1
    assert generated[1].seat_index == 2
    assert generated[1].assigned_attendee_name == "张文远"


def test_render_seat_leave_and_zone_canvas():
    """测试工位绘制与取证水印图像合成"""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    zone = SeatZone(
        seat_index=1,
        x1=100,
        y1=100,
        x2=250,
        y2=300,
        assigned_attendee_name="夏一帆",
        current_status="absent",
    )

    # 离席快照取证
    snapshot = render_seat_leave_snapshot(frame, zone, "2026-09-15 14:00:00")
    assert snapshot.shape == (480, 640, 3)
    assert snapshot.sum() > 0

    # 原位渲染工位
    render_seat_zones(frame, [zone])
    assert frame.sum() > 0


def test_seat_dialog_interaction(tmp_path: Path):
    """测试工位管理弹窗交互与列表装载"""
    from app.src.ui.components.seat_dialog import SeatZoneDialog

    db_file = tmp_path / "test_dialog.db"
    init_database(db_file)

    attendees = [
        Attendee(id="EMP001", name="夏一帆", department="研发一部"),
        Attendee(id="EMP002", name="张文远", department="研发一部"),
    ]
    zones = [
        SeatZone(
            meeting_id=1,
            seat_index=1,
            x1=100,
            y1=100,
            x2=200,
            y2=200,
            assigned_employee_id="EMP001",
            assigned_attendee_name="夏一帆",
            current_status="occupied",
        )
    ]

    dialog = SeatZoneDialog(meeting_id=1, attendees=attendees, seat_zones=zones, db_path=db_file)
    assert dialog.table.rowCount() == 1

    # 测试修改下拉框人员
    combo = dialog.table.cellWidget(0, 2)
    assert combo is not None
    assert combo.currentIndex() == 1  # 对应夏一帆

    dialog.close()


def test_video_widget_seat_drawing_mode():
    """测试 VideoWidget 鼠标框选工位模式与几何映射"""
    from app.src.ui.components.video_widget import VideoWidget

    widget = VideoWidget()
    img = QImage(640, 480, QImage.Format_RGB888)
    img.fill(QColor(255, 255, 255))
    widget.update_frame(img, [], fps=30.0)
    widget.resize(640, 480)

    # 开启框选模式
    widget.set_drawing_seat_mode(True)
    assert widget.is_drawing_seat is True
    assert widget.cursor().shape() == Qt.CrossCursor

    captured_coords = []
    widget.seat_zone_drawn.connect(lambda x1, y1, x2, y2: captured_coords.append((x1, y1, x2, y2)))

    # 模拟鼠标拖拽
    class MockMouseEvent:
        def __init__(self, pos, button=Qt.LeftButton):
            self._pos = pos
            self._button = button

        def position(self):
            return self._pos

        def button(self):
            return self._button

    widget.mousePressEvent(MockMouseEvent(QPointF(100, 100)))
    assert widget._is_dragging_rect is True

    widget.mouseMoveEvent(MockMouseEvent(QPointF(250, 300)))
    assert widget._drag_current_pos == QPointF(250, 300)

    widget.mouseReleaseEvent(MockMouseEvent(QPointF(250, 300)))
    assert widget.is_drawing_seat is False
    assert len(captured_coords) == 1
    fx1, fy1, fx2, fy2 = captured_coords[0]
    assert 90 <= fx1 <= 110
    assert 90 <= fy1 <= 110
    assert 240 <= fx2 <= 260
    assert 290 <= fy2 <= 310


def test_bbox_value_object():
    """测试 BBox 几何包围盒属性与方法"""
    from app.src.model import BBox
    from app.src.core.drawer import clamp_bbox

    box = BBox(10, 20, 110, 120)
    assert box.width == 100
    assert box.height == 100
    assert box.center == (60.0, 70.0)
    assert box.contains_point(60, 70) is True
    assert box.contains_point(5, 5) is False

    ratio = box.calculate_intersection_ratio(60, 70, 160, 170)
    assert pytest.approx(ratio, 0.01) == 0.25

    clamped = clamp_bbox(box, width=640, height=480)
    assert clamped == (10, 20, 110, 120)


def test_attendance_stats_calculate():
    """测试 AttendanceStats.calculate 领域聚合计算"""
    from app.src.model import AttendanceStats, Attendee

    attendees = [
        Attendee(id="E1", name="A1", department="D1", status="present"),
        Attendee(id="E2", name="A2", department="D1", status="present"),
        Attendee(id="E3", name="A3", department="D1", status="absent"),
        Attendee(id="E4", name="A4", department="D1", status="absent"),
    ]
    stats = AttendanceStats.calculate(attendees, distraction_total=3)
    assert stats.total_expected == 4
    assert stats.current_present == 2
    assert stats.current_absent == 2
    assert stats.attendance_rate == 50.0
    assert stats.distraction_total == 3


def test_seat_tracker_three_second_absence():
    """测试持续 3 秒不在工位触发离席防抖"""
    import time
    tracker = SeatZoneTracker(debounce_frames=100, recovery_frames=1, absent_seconds=0.1)
    zone = SeatZone(
        id=1,
        meeting_id=1,
        seat_index=1,
        x1=100,
        y1=100,
        x2=200,
        y2=200,
        assigned_attendee_name="测试员",
        current_status="occupied",
    )
    tracker.set_zones([zone])
    frame = np.zeros((300, 300, 3), dtype=np.uint8)

    # 刚离开，不到 0.1 秒，不告警
    zones, alerts, _ = tracker.update(frame, [])
    assert len(alerts) == 0

    # 睡眠满 0.12 秒（满足 absent_seconds 设定）
    time.sleep(0.12)
    zones, alerts, changed = tracker.update(frame, [])
    assert len(alerts) == 1
    assert alerts[0].event_type == "leaving_seat"
    assert zones[0].current_status == "absent"
    assert changed is True

