import os
import numpy as np
import pytest

from app.config import DEFAULT_DEMO_VIDEO
from app.src.core.capture import VideoCaptureStream
from app.src.core.detector import VisionDetector
from app.src.core.drawer import (
    draw_cached_detections,
    draw_detections,
    render_box_with_label,
    render_detections,
    render_summary_bar,
)
from app.src.core.recorder import SnapshotManager, VideoRecorder
from app.src.model import Attendee, DetectionBox
from app.src.service.export_service import AttendanceReportService


def test_video_capture_stream():
    """测试 VideoCaptureStream 打开、读取与循环回放能力"""
    stream = VideoCaptureStream(video_source=str(DEFAULT_DEMO_VIDEO))
    assert stream.open() is True
    assert stream.is_opened() is True

    ret, frame = stream.read()
    assert ret is True
    assert frame is not None
    assert frame.shape[0] > 0

    stream.release()
    assert stream.is_opened() is False


def test_video_capture_stream_concurrent_change_source():
    """回归测试：多线程并发读取与切换源不会导致 libavcodec 断言失败或死锁崩溃"""
    import threading
    import time

    stream = VideoCaptureStream(video_source=str(DEFAULT_DEMO_VIDEO))
    assert stream.open() is True

    running = True

    def reader():
        while running:
            ret, frame = stream.read()
            time.sleep(0.001)

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    for _ in range(10):
        time.sleep(0.01)
        stream.change_source(str(DEFAULT_DEMO_VIDEO))

    running = False
    t.join(timeout=1.0)
    stream.release()
    assert stream.is_opened() is False


def test_core_drawer_rendering():
    """测试 drawer 原生帧绘制与摘要横幅"""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    render_box_with_label(frame, 10, 10, 100, 100, "test_box")
    assert frame.sum() > 0

    render_summary_bar(frame, {"person": 3, "cell phone": 1})

    dets = [
        DetectionBox(
            x1=20, y1=20, x2=80, y2=80, confidence=0.9, class_id=0,
            class_name="person", track_id=1, is_distracted=False
        ),
        DetectionBox(
            x1=90, y1=90, x2=120, y2=140, confidence=0.8, class_id=67,
            class_name="cell phone", track_id=None, is_distracted=False
        ),
        DetectionBox(
            x1=150, y1=150, x2=200, y2=200, confidence=0.85, class_id=0,
            class_name="sleep", track_id=2, is_distracted=True
        ),
    ]
    render_detections(frame, dets, {"person": 1, "cell phone": 1, "sleep": 1})
    draw_cached_detections(frame, dets, {"person": 1})


def test_core_recorder_and_snapshot(tmp_path):
    """测试 VideoRecorder 与 SnapshotManager 落盘操作"""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # 快照测试
    snap_target = str(tmp_path / "snap.jpg")
    res_snap = SnapshotManager.save_snapshot(frame, snap_target)
    assert res_snap == snap_target
    assert os.path.exists(snap_target)
    assert os.path.getsize(snap_target) > 0

    # 录制测试
    recorder = VideoRecorder(fps=25.0)
    rec_target = str(tmp_path / "test.mp4")
    started = recorder.start(rec_target)
    assert started == rec_target
    assert recorder.is_recording is True

    recorder.write(frame)
    recorder.write(frame)

    stopped = recorder.stop()
    assert recorder.is_recording is False
    assert stopped == rec_target
    assert os.path.exists(rec_target)
    assert os.path.getsize(rec_target) > 0


def test_vision_detector_fallback():
    """测试 VisionDetector 直通模式与优雅降级"""
    detector = VisionDetector(enable_yolo=False)
    assert detector.is_ready is False

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    dets, counts = detector.detect(frame)
    assert len(dets) == 0
    assert len(counts) == 0


def test_attendance_export_service(tmp_path):
    """测试 AttendanceReportService 导出考勤报表"""
    attendees = [
        Attendee(id="EMP001", name="测试人员", department="技术部", role="工程师", status="present", track_id="#1"),
        Attendee(id="EMP002", name="离席人员", department="市场部", role="主管", status="absent"),
    ]
    export_file = tmp_path / "test_report.xlsx"
    res_path = AttendanceReportService.export_to_excel(attendees, export_file)
    assert res_path == export_file
    assert os.path.exists(str(export_file))
    assert os.path.getsize(str(export_file)) > 0


def test_evidence_snapshot_and_alert_lifecycle(tmp_path, monkeypatch):
    """测试告警自动截取证据帧、时间水印与物理落盘闭环"""
    from app.src.core.drawer import render_evidence_snapshot
    from app.src.service.vision_service import VisionService

    frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
    det = DetectionBox(
        x1=100, y1=100, x2=200, y2=250, confidence=0.88,
        class_id=0, class_name="using_device", track_id=5,
        behavior_label="低头玩手机", is_distracted=True
    )
    watermarked = render_evidence_snapshot(frame, det, "2026-09-14 15:50:00")
    assert watermarked is not None
    assert watermarked.shape == frame.shape
    assert not np.array_equal(frame, watermarked)

    # 测试告警触发时快照自动生成与路径绑定
    monkeypatch.setattr("app.src.service.vision_service.SNAPSHOTS_DIR", tmp_path)
    service = VisionService(video_source=str(DEFAULT_DEMO_VIDEO), enable_yolo=False)
    service._last_raw_frame = frame.copy()

    captured_alerts = []
    service.alert_triggered.connect(lambda a: captured_alerts.append(a))
    service._trigger_alert_if_needed(track_id=5, label_text="低头玩手机", det=det)

    assert len(captured_alerts) == 1
    alert = captured_alerts[0]
    assert alert.track_id == "#5"
    assert alert.snapshot_path is not None
    assert os.path.exists(alert.snapshot_path)
    assert os.path.getsize(alert.snapshot_path) > 0


def test_behavior_enum_distraction():
    """测试 BehaviorType 对分心状态的领域模型内聚判断"""
    from app.src.model.enums import BehaviorType

    assert BehaviorType.is_distracted_code("using_device") is True
    assert BehaviorType.is_distracted_code("sleep") is True
    assert BehaviorType.is_distracted_code("look_forward") is False
    assert BehaviorType.is_distracted_code("cell phone") is False
    assert BehaviorType.is_distracted_code("unknown_code") is False


def test_interaction_strategies():
    """测试设备交互研判策略：精简为纯布尔谓词判断 is_holding_phone(person_bbox, matched_phones, pose_keypoints)。"""
    from app.src.core.strategy import BBoxOverlapStrategy, PoseWristDistanceStrategy

    bbox_strat = BBoxOverlapStrategy()
    assert bbox_strat.is_holding_phone((0, 0, 100, 100), []) is False
    assert bbox_strat.is_holding_phone((0, 0, 100, 100), [([10, 10, 30, 40], 20.0, 25.0)]) is True

    pose_strat = PoseWristDistanceStrategy(wrist_dist_threshold=80.0)
    # 无关键点时回退判定
    assert pose_strat.is_holding_phone((0, 0, 100, 100), [([10, 10, 30, 40], 20.0, 25.0)], None) is True
    assert pose_strat.is_holding_phone((0, 0, 100, 100), [], None) is False

