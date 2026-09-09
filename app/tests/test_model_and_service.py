import os
import numpy as np
from app.src.model import Attendee, MeetingInfo, DetectionBox, BehaviorType
from app.src.service import VisionService
from app.config import DEFAULT_DEMO_VIDEO

os.environ["QT_QPA_PLATFORM"] = "offscreen"


def test_enums():
    using_dev = BehaviorType.from_code("using_device")
    assert using_dev is not None
    assert using_dev.label == "低头玩手机"
    assert using_dev.is_distracted is True

    sleep = BehaviorType.from_code("sleep")
    assert sleep is not None
    assert sleep.label == "闭眼打瞌睡"
    assert sleep.is_distracted is True

    turn_head = BehaviorType.from_code("turn_head")
    assert turn_head is not None
    assert turn_head.label == "侧向交流"
    assert turn_head.is_distracted is False


def test_model_creation():
    attendee = Attendee(
        id="EMP001",
        name="夏一帆",
        department="研发一部",
        role="组长",
        status="present",
        track_id="#1"
    )
    assert attendee.name == "夏一帆"
    assert attendee.status == "present"
    assert attendee.track_id == "#1"
    assert attendee.distraction_count == 0

    meeting = MeetingInfo(title="测试会议")
    assert meeting.total_expected == 12
    assert meeting.status == "active"

    det = DetectionBox(
        x1=100.0, y1=200.0, x2=300.0, y2=400.0,
        confidence=0.88, class_id=0, class_name="person",
        track_id=1, behavior_label="look_forward"
    )
    assert det.track_id == 1
    assert not det.is_distracted


def test_vision_service_pipeline():
    worker = VisionService(video_source=str(DEFAULT_DEMO_VIDEO), enable_yolo=False)
    assert worker.video_source == str(DEFAULT_DEMO_VIDEO)
    assert not worker.is_running

    ret, frame = worker.read_raw_frame()
    assert ret is True
    assert isinstance(frame, np.ndarray)
    assert frame.shape[2] == 3

    q_img = worker.convert_cv_to_qimage(frame)
    assert q_img is not None
    assert q_img.width() > 0
    assert q_img.height() > 0
