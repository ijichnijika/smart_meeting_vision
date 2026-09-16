"""
MeetingController 与 MeetingSessionStore 单元测试。
"""

from pathlib import Path
import pytest
from PySide6.QtCore import QCoreApplication

from app.src.controller import MeetingController
from app.src.state import MeetingSessionStore
from app.src.model import Attendee, DistractionAlert, MeetingInfo, SeatZone


@pytest.fixture(scope="module")
def qapp():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


def test_meeting_session_store_signals(qapp):
    store = MeetingSessionStore()
    received_attendees = []
    store.attendees_changed.connect(lambda atts: received_attendees.append(atts))

    test_attendees = [
        Attendee(id="E1", name="张三", department="研发", status="present"),
        Attendee(id="E2", name="李四", department="设计", status="present"),
    ]
    store.set_attendees(test_attendees)
    assert len(received_attendees) == 1
    assert len(store.attendees) == 2
    assert store.stats.total_expected == 2
    assert store.stats.current_present == 2

    # 更新在席状态触发自动重算
    store.update_attendee_status("E1", "absent")
    assert store.stats.current_present == 1
    assert store.stats.current_absent == 1
    assert store.stats.attendance_rate == 50.0

    # 累加分心
    store.bind_tracking_id("E2", "#2")
    store.increment_distraction("#2")
    e2 = next(a for a in store.attendees if a.id == "E2")
    assert e2.distraction_count == 1


def test_meeting_controller_workflow(tmp_path: Path, qapp):
    db_file = tmp_path / "test_ctrl.db"
    controller = MeetingController(db_path=db_file)
    controller.initialize()

    assert controller.store.meeting is not None
    assert len(controller.store.attendees) > 0

    # 测试离席告警驱动
    first_att = controller.store.attendees[0]
    alert = DistractionAlert(
        id="ALT-1",
        track_id="#1",
        attendee_name=first_att.name,
        event_type="leaving_seat",
        event_label="离席告警",
        timestamp="10:00:00",
    )
    matched = controller.handle_leaving_seat_alert(alert)
    assert matched is True
    updated = next(a for a in controller.store.attendees if a.id == first_att.id)
    assert updated.status == "absent"

    # 测试新增工位
    new_zone = SeatZone(
        meeting_id=controller.store.meeting.id,
        seat_index=1,
        x1=10, y1=10, x2=50, y2=50,
    )
    saved = controller.add_seat_zone(new_zone)
    assert saved.id is not None
    assert len(controller.store.seat_zones) == 1
