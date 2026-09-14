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


def test_draw_detections_and_counting():
    """测试 draw_detections 在图像上原生绘制矩形框、防乱码英文字符及 Counter 统计准确性"""
    import torch
    from app.src.service.vision_service import draw_detections

    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    class MockBoxes:
        xyxy = torch.tensor([
            [50, 60, 150, 200],
            [200, 100, 300, 250],
            [320, 150, 360, 210]
        ], dtype=torch.float32)
        cls = torch.tensor([0, 0, 67], dtype=torch.float32)
        conf = torch.tensor([0.91, 0.85, 0.76], dtype=torch.float32)
        id = torch.tensor([1.0, 2.0, 3.0], dtype=torch.float32)

        def __len__(self):
            return len(self.xyxy)

    names = {0: "person", 67: "cell phone"}
    counter, detections = draw_detections(frame, MockBoxes(), names)

    assert counter["person"] == 2
    assert counter["cell phone"] == 1
    assert len(detections) == 3

    assert detections[0].class_name == "person"
    assert detections[0].track_id == 1
    assert not detections[0].is_distracted

    assert detections[2].class_name == "cell phone"
    assert detections[2].is_distracted is False

    # 验证图像矩阵已被 OpenCV 原地写入边界框与文字信息
    assert frame.sum() > 0


def test_video_recording_and_snapshot_lifecycle(tmp_path):
    """测试工作线程录制视频与画面快照的完整生命周期"""
    worker = VisionService(video_source=str(DEFAULT_DEMO_VIDEO), enable_yolo=False)
    ret, frame = worker.read_raw_frame()
    assert ret is True and frame is not None
    worker._last_raw_frame = frame.copy()

    # 测试快照功能
    snap_file = str(tmp_path / "test_snap.jpg")
    saved_snap = worker.take_snapshot(snap_file)
    assert saved_snap == snap_file
    assert os.path.exists(snap_file)
    assert os.path.getsize(snap_file) > 0

    # 测试录制控制生命周期
    record_file = str(tmp_path / "test_record.mp4")
    worker.start_recording(record_file)
    assert worker.is_recording is True

    # 模拟写入 3 帧
    for _ in range(3):
        worker._write_recording_frame(frame)

    stopped_path = worker.stop_recording()
    assert worker.is_recording is False
    assert stopped_path == record_file
    assert os.path.exists(record_file)
    assert os.path.getsize(record_file) > 0


def test_stats_with_category_counts():
    """测试 AttendanceStats 能够携带分类统计字典并通过信号发射"""
    worker = VisionService(video_source=str(DEFAULT_DEMO_VIDEO), enable_yolo=False)
    received_stats = []
    worker.stats_updated.connect(lambda s: received_stats.append(s))

    worker._update_stats_if_needed(present_count=8, distraction_count=2, counts_dict={"person": 8, "cell phone": 2})

    assert len(received_stats) == 1
    stats = received_stats[0]
    assert stats.current_present == 8
    assert stats.distraction_total == 2
    assert stats.category_counts == {"person": 8, "cell phone": 2}
