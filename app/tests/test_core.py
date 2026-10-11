import os
import cv2
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


def test_snapshot_cooldown_and_rate_limiting(tmp_path, monkeypatch):
    """测试自动截图频率控制：单目标冷却锁、全局时间间隔限制与快照开关。"""
    from app.src.service.vision_service import VisionService

    monkeypatch.setattr("app.src.service.vision_service.SNAPSHOTS_DIR", tmp_path)
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 100
    det = DetectionBox(
        x1=50, y1=50, x2=150, y2=200, confidence=0.9,
        class_id=0, class_name="using_device", track_id=1,
        behavior_label="低头玩手机", is_distracted=True
    )

    # 1. 冷却期内同一 track_id 抑制重复告警与截图
    service = VisionService(alert_cooldown_seconds=10.0, min_snapshot_interval=1.0, enable_yolo=False)
    service._last_raw_frame = frame.copy()

    alerts = []
    service.alert_triggered.connect(lambda a: alerts.append(a))
    service._trigger_alert_if_needed(track_id=1, label_text="低头玩手机", det=det)
    assert len(alerts) == 1
    assert alerts[0].snapshot_path is not None

    # 立即再次触发同一目标，应被冷却锁拦截
    service._trigger_alert_if_needed(track_id=1, label_text="低头玩手机", det=det)
    assert len(alerts) == 1

    # 2. 全局最小截图间隔限制：另一目标立即触发，告警发出但截图被限频保护
    det2 = DetectionBox(
        x1=200, y1=50, x2=300, y2=200, confidence=0.88,
        class_id=0, class_name="sleep", track_id=2,
        behavior_label="闭眼打瞌睡", is_distracted=True
    )
    service._trigger_alert_if_needed(track_id=2, label_text="闭眼打瞌睡", det=det2)
    assert len(alerts) == 2
    # 在 1 秒全局限频内，不应重复写入截图文件
    assert alerts[1].snapshot_path is None

    # 3. 关闭自动截图功能
    service_no_snap = VisionService(enable_auto_snapshot=False, enable_yolo=False)
    service_no_snap._last_raw_frame = frame.copy()
    alerts_no_snap = []
    service_no_snap.alert_triggered.connect(lambda a: alerts_no_snap.append(a))
    service_no_snap._trigger_alert_if_needed(track_id=3, label_text="低头玩手机", det=det)
    assert len(alerts_no_snap) == 1
    assert alerts_no_snap[0].snapshot_path is None


@pytest.mark.parametrize("failure", [False, cv2.error("write failed"), OSError("disk full")])
def test_snapshot_write_failure(tmp_path, monkeypatch, failure):
    def fail_write(*args):
        if isinstance(failure, Exception):
            raise failure
        return failure

    monkeypatch.setattr("app.src.core.recorder.cv2.imwrite", fail_write)
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    assert SnapshotManager.save_snapshot(frame, str(tmp_path / "failed.jpg")) is None


def test_alert_uses_inference_frame_and_preserves_cooldown_on_write_failure(tmp_path, monkeypatch):
    from app.src.service.vision_service import VisionService

    monkeypatch.setattr("app.src.service.vision_service.SNAPSHOTS_DIR", tmp_path)
    service = VisionService(enable_yolo=False, distraction_confirm_frames=1)
    inference_frame = np.full((100, 100, 3), 50, dtype=np.uint8)
    service._last_raw_frame = np.full_like(inference_frame, 200)
    det = DetectionBox(10, 10, 50, 50, 0.9, 0, "sleep", track_id=1, is_distracted=True)
    monkeypatch.setattr(service._detector, "detect", lambda frame: ([det], {"sleep": 1}))
    rendered_frames = []

    def render(frame, *args):
        rendered_frames.append(frame.copy())
        return frame.copy()

    monkeypatch.setattr("app.src.service.vision_service.render_evidence_snapshot", render)
    write_results = iter([False, True])
    monkeypatch.setattr("app.src.core.recorder.cv2.imwrite", lambda *args: next(write_results))
    alerts = []
    service.alert_triggered.connect(alerts.append)
    try:
        service._async_infer_worker(inference_frame)
        assert len(alerts) == 1
        assert alerts[0].snapshot_path is None
        assert service._last_snapshot_time == 0
        np.testing.assert_array_equal(rendered_frames[0], inference_frame)

        det.track_id = 2
        service._async_infer_worker(inference_frame)
        assert len(alerts) == 2
        assert alerts[1].snapshot_path is not None
        assert service._last_snapshot_time > 0
    finally:
        service.stop()


def test_seat_alert_write_failure_does_not_consume_snapshot_cooldown(tmp_path, monkeypatch):
    from app.src.model import SeatZone
    from app.src.service.vision_service import VisionService

    monkeypatch.setattr("app.src.service.vision_service.SNAPSHOTS_DIR", tmp_path)
    monkeypatch.setattr("app.src.core.recorder.cv2.imwrite", lambda *args: False)
    service = VisionService(enable_yolo=False)
    service._seat_tracker.debounce_frames = 1
    service.set_seat_zones([SeatZone(id=1, x2=50, y2=50, current_status="occupied")])
    monkeypatch.setattr(service._detector, "detect", lambda frame: ([], {}))
    alerts = []
    service.alert_triggered.connect(alerts.append)
    try:
        service._async_infer_worker(np.zeros((100, 100, 3), dtype=np.uint8))
        assert len(alerts) == 1
        assert alerts[0].snapshot_path is None
        assert service._last_snapshot_time == 0
        assert service._seat_leave_cooldowns == {}
    finally:
        service.stop()
