"""
视频采集与视觉推理服务编排层（Facade门面类），负责协调流采集、目标检测、画面标注与媒体管道。
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple, Union
import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from app.config import SNAPSHOTS_DIR, TARGET_FPS
from app.src.common.logger import get_logger
from app.src.core import (
    SeatZoneTracker,
    SnapshotManager,
    VideoCaptureStream,
    VideoRecorder,
    VisionDetector,
    draw_detections,
    render_detections,
    render_evidence_snapshot,
)
from app.src.model import AttendanceStats, DetectionBox, DistractionAlert, SeatZone

logger = get_logger("vision_service")

# 向后兼容导出
__all__ = ["VisionService", "draw_detections"]


class VisionService(QThread):
    """视觉服务管道调度门面，串联采集流、推理引擎、标注渲染与录制。"""

    frame_ready = Signal(QImage, list, float)
    done_signal = Signal(np.ndarray, dict)
    frame_processed = done_signal
    stats_updated = Signal(object)
    alert_triggered = Signal(object)
    seat_zones_updated = Signal(list)
    source_status = Signal(bool, str)
    recording_status = Signal(bool, str)

    def __init__(self, video_source: Union[str, int] = 0, enable_yolo: bool = True, expected_count: int = 12, alert_cooldown_seconds: float = 6.0, parent=None):
        super().__init__(parent)
        self.setStackSize(16 * 1024 * 1024)
        self.video_source = video_source
        self.enable_yolo = enable_yolo
        self.is_running = False
        self.is_paused = False
        self.expected_count = expected_count
        self.alert_cooldown_seconds = alert_cooldown_seconds

        self._capture = VideoCaptureStream(video_source=self.video_source)
        self._detector = VisionDetector(enable_yolo=self.enable_yolo)
        self._recorder = VideoRecorder(fps=float(TARGET_FPS))

        self._frame_count = 0
        self._last_detections: List[DetectionBox] = []
        self._last_counts: dict = {}
        self._last_raw_frame: Optional[np.ndarray] = None
        self._alert_cooldowns = {}
        self._last_stats_t = 0.0

        self._infer_lock = threading.Lock()
        self._is_inferring = False
        self._infer_pool = ThreadPoolExecutor(max_workers=1)

        self._seat_tracker = SeatZoneTracker(debounce_frames=15, recovery_frames=1, absent_seconds=3.0)
        self._seat_lock = threading.Lock()

        self._pending_source: Optional[Union[str, int]] = None
        self._source_lock = threading.Lock()

    def set_seat_zones(self, zones: List[SeatZone]):
        """设置当前视频流对应的工位列表。"""
        with self._seat_lock:
            self._seat_tracker.set_zones(zones)

    def get_seat_zones(self) -> List[SeatZone]:
        """获取当前跟踪器维护的工位列表及最新状态。"""
        with self._seat_lock:
            return self._seat_tracker.get_zones()

    @property
    def is_recording(self) -> bool:
        return self._recorder.is_recording

    def read_raw_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """读取单帧原始 OpenCV 图像。"""
        return self._capture.read()

    @staticmethod
    def convert_cv_to_qimage(frame: np.ndarray) -> QImage:
        """将 OpenCV BGR 图像转换为 QImage（深拷贝防止内存覆写）。"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        return QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()

    def run(self):
        """主管道调度执行循环。"""
        self.is_running = True
        if not self._capture.open():
            self.source_status.emit(False, f"数据源无法打开: {self.video_source}")
            self.is_running = False
            return
        self.source_status.emit(True, f"数据源: {self.video_source}")

        native_fps = self._capture.get_fps()
        frame_duration = 1.0 / max(10.0, min(60.0, native_fps))
        prev_time = time.time()
        fps_smooth = float(native_fps)

        while self.is_running:
            with self._source_lock:
                if self._pending_source is not None:
                    pending = self._pending_source
                    self._pending_source = None
                    if self._capture.change_source(pending):
                        self.source_status.emit(True, f"数据源: {pending}")
                        native_fps = self._capture.get_fps()
                        frame_duration = 1.0 / max(10.0, min(60.0, native_fps))
                    else:
                        self.source_status.emit(False, f"数据源无法打开: {pending}")

            if self.is_paused:
                self.msleep(50)
                continue

            start_t = time.time()
            ret, frame = self.read_raw_frame()

            if not ret or frame is None:
                self.msleep(30)
                continue

            self._last_raw_frame = frame.copy()

            # 异步非阻塞调度后台 AI 推理（保障前台 30 FPS 丝滑播放，解决切片卡顿）
            if self.enable_yolo and self._detector.is_ready:
                with self._infer_lock:
                    can_infer = not self._is_inferring
                if can_infer:
                    with self._infer_lock:
                        self._is_inferring = True
                    self._infer_pool.submit(self._async_infer_worker, frame.copy())

            # 获取当前最新的目标检测与行为状态快照
            with self._infer_lock:
                cur_dets = list(self._last_detections)
                cur_counts = dict(self._last_counts)

            # 仅在录制视频时在副本上绘制离线标注，避免污染前台 UI 矢量渲染
            if self.is_recording:
                record_frame = frame.copy()
                render_detections(record_frame, cur_dets, cur_counts)
                self._recorder.write(record_frame)

            q_image = self.convert_cv_to_qimage(frame)

            curr_t = time.time()
            dt = curr_t - prev_time
            prev_time = curr_t
            if dt > 0:
                fps_smooth = 0.9 * fps_smooth + 0.1 * (1.0 / dt)

            self.frame_ready.emit(q_image, cur_dets, fps_smooth)

            elapsed = time.time() - start_t
            sleep_time = frame_duration - elapsed
            if sleep_time > 0.001:
                time.sleep(sleep_time)

        if self.is_recording:
            self.stop_recording()

        self._capture.release()

    def _async_infer_worker(self, frame: np.ndarray):
        """后台独立工作线程：执行行为感知与姿态复核。"""
        try:
            detections, counter = self._detector.detect(frame)
            counts_dict = dict(counter)

            for det in detections:
                if det.is_distracted and det.class_name != "cell phone":
                    self._trigger_alert_if_needed(det.track_id or 1, det.behavior_label or "分心告警", det)

            person_count = counts_dict.get("person", 0)
            if person_count == 0:
                person_count = sum(c for k, c in counts_dict.items() if k != "cell phone")

            distraction_count = sum(1 for d in detections if d.is_distracted and d.class_name != "cell phone")
            self._update_stats_if_needed(person_count, distraction_count, counts_dict)

            # 更新工位时序状态机与离席防抖推断
            with self._seat_lock:
                if self._seat_tracker.zones:
                    updated_zones, leave_alerts, has_changed = self._seat_tracker.update(frame, detections)
                    for l_alert in leave_alerts:
                        if frame is not None and l_alert.snapshot_path is None:
                            try:
                                zone_match = next(
                                    (z for z in updated_zones if f"#{z.seat_index}" == l_alert.track_id), None
                                )
                                if zone_match:
                                    from app.src.core.drawer import render_seat_leave_snapshot
                                    evidence_img = render_seat_leave_snapshot(
                                        frame, zone_match, time.strftime("%Y-%m-%d %H:%M:%S")
                                    )
                                    snap_file = SNAPSHOTS_DIR / f"leave_seat_{zone_match.seat_index}_{int(time.time() * 1000)}.jpg"
                                    cv2.imwrite(str(snap_file), evidence_img)
                                    l_alert.snapshot_path = str(snap_file)
                            except Exception as e:
                                logger.error(f"保存离席证据快照失败: {e}", exc_info=True)
                        self.alert_triggered.emit(l_alert)
                    if has_changed:
                        self.seat_zones_updated.emit(list(updated_zones))

            with self._infer_lock:
                self._last_detections = detections
                self._last_counts = counts_dict
            self.done_signal.emit(frame, counts_dict)
        except Exception as e:
            logger.error(f"异步视觉推理异常: {e}", exc_info=True)
        finally:
            with self._infer_lock:
                self._is_inferring = False

    def _process_frame_with_counts(self, frame: np.ndarray) -> Tuple[List[DetectionBox], dict]:
        """同步推理兼容接口（供单元测试或离线单步调用）。"""
        if not self.enable_yolo or not self._detector.is_ready:
            return [], {}
        detections, counter = self._detector.detect(frame)
        counts_dict = dict(counter)
        render_detections(frame, detections, counts_dict)

        with self._seat_lock:
            if self._seat_tracker.zones:
                updated_zones, leave_alerts, has_changed = self._seat_tracker.update(frame, detections)
                for l_alert in leave_alerts:
                    self.alert_triggered.emit(l_alert)
                if has_changed:
                    self.seat_zones_updated.emit(list(updated_zones))

        with self._infer_lock:
            self._last_detections = detections
            self._last_counts = counts_dict
        return detections, counts_dict

    def _trigger_alert_if_needed(self, track_id: int, label_text: str, det: Optional[DetectionBox] = None):
        """触发分心行为告警，单目标在 6 秒内去重。"""
        now = time.time()
        if track_id not in self._alert_cooldowns or now - self._alert_cooldowns[track_id] > self.alert_cooldown_seconds:
            self._alert_cooldowns[track_id] = now
            ts_readable = time.strftime("%Y-%m-%d %H:%M:%S")

            snapshot_path = None
            if self._last_raw_frame is not None and det is not None:
                evidence_img = render_evidence_snapshot(self._last_raw_frame, det, ts_readable)
                snap_file = SNAPSHOTS_DIR / f"alert_{track_id}_{int(now * 1000)}.jpg"
                cv2.imwrite(str(snap_file), evidence_img)
                snapshot_path = str(snap_file)

            alert = DistractionAlert(
                id=f"ALT-{int(now * 1000)}",
                track_id=f"#{track_id}",
                attendee_name=f"参会人 #{track_id}",
                event_type="distraction",
                event_label=label_text,
                timestamp=time.strftime("%H:%M:%S"),
                duration_seconds=3,
                snapshot_path=snapshot_path,
            )
            self.alert_triggered.emit(alert)

    def _update_stats_if_needed(self, present_count: int, distraction_count: int = 0, counts_dict: Optional[dict] = None):
        """更新出勤统计数据，最小时间间隔 0.8 秒。"""
        now = time.time()
        if now - self._last_stats_t > 0.8:
            self._last_stats_t = now
            total = self.expected_count
            cur_pres = min(total, max(1, present_count)) if present_count > 0 else 0
            cur_abs = max(0, total - cur_pres)
            rate = round(cur_pres / total * 100.0, 1) if total > 0 else 0.0
            self.stats_updated.emit(AttendanceStats(
                total_expected=total,
                current_present=cur_pres,
                current_absent=cur_abs,
                distraction_total=distraction_count,
                attendance_rate=rate,
                category_counts=counts_dict,
            ))

    def start_recording(self, save_path: Optional[str] = None) -> str:
        """启动带标注视频录制。"""
        path = self._recorder.start(save_path)
        self.recording_status.emit(True, path)
        return path

    def _write_recording_frame(self, frame: np.ndarray):
        """将帧写入录像管道。"""
        self._recorder.write(frame)

    def stop_recording(self) -> Optional[str]:
        """停止录制并释放资源。"""
        path = self._recorder.stop()
        self.recording_status.emit(False, path or "")
        return path

    def toggle_recording(self, save_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """切换录制与停止状态。"""
        is_rec, path = self._recorder.toggle(save_path)
        self.recording_status.emit(is_rec, path or "")
        return is_rec, path

    def take_snapshot(self, save_path: Optional[str] = None) -> Optional[str]:
        """将当前带算法标注的高清帧保存为图像。"""
        return SnapshotManager.save_snapshot(self._last_raw_frame, save_path)

    def pause(self):
        """暂停播放。"""
        self.is_paused = True

    def resume(self):
        """恢复播放。"""
        self.is_paused = False

    def toggle_play(self) -> bool:
        """切换播放与暂停状态。"""
        self.is_paused = not self.is_paused
        return not self.is_paused

    def stop(self):
        """停止线程并等待资源安全退出。"""
        self.is_running = False
        self.is_paused = False
        self._infer_pool.shutdown(wait=False)
        if self.is_recording:
            self.stop_recording()
        self.quit()
        if self.isRunning():
            self.wait(3000)

    def change_source(self, new_source: Union[str, int]):
        """切换视频流数据源。"""
        self.video_source = new_source
        if self.isRunning():
            with self._source_lock:
                self._pending_source = new_source
        else:
            self._capture.change_source(new_source)
