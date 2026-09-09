"""
视频采集与目标检测追踪处理线程。
"""

from __future__ import annotations

import os
import time
from typing import List, Optional, Tuple, Union
import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from enum import IntEnum

from app.src.common.logger import get_logger
from app.config import (
    DEFAULT_YOLO_WEIGHTS,
    BEHAVIOR_WEIGHTS,
    CONF_THRESHOLD,
    IOU_THRESHOLD,
    TARGET_FPS,
)
from app.src.model import (
    AttendanceStats,
    BehaviorType,
    DetectionBox,
    DistractionAlert,
)

logger = get_logger("vision_service")


class _CocoClassId(IntEnum):
    PERSON = 0
    CELL_PHONE = 67


class VisionService(QThread):
    frame_ready = Signal(QImage, list, float)
    stats_updated = Signal(object)
    alert_triggered = Signal(object)
    source_status = Signal(bool, str)

    def __init__(self, video_source: Union[str, int] = 0, enable_yolo: bool = True, parent=None):
        super().__init__(parent)
        # macOS 默认子线程栈空间为 512KB，OpenBLAS 执行矩阵运算易发生栈溢出，此处扩容至 16MB
        self.setStackSize(16 * 1024 * 1024)
        self.video_source = video_source
        self.enable_yolo = enable_yolo
        self.is_running = False
        self.is_paused = False
        self._cap: Optional[cv2.VideoCapture] = None
        self._yolo_model = None
        self._behavior_model = None
        self._frame_count = 0
        self._last_detections: List[DetectionBox] = []
        self._alert_cooldowns = {}
        self._last_stats_t = 0.0

        if self.enable_yolo:
            self._init_yolo()

    def _init_yolo(self):
        """初始化目标检测与行为识别模型。"""
        try:
            from ultralytics import YOLO

            if os.path.exists(DEFAULT_YOLO_WEIGHTS):
                self._yolo_model = YOLO(str(DEFAULT_YOLO_WEIGHTS))
            else:
                self._yolo_model = YOLO("yolov8n.pt")

            if os.path.exists(BEHAVIOR_WEIGHTS) and str(BEHAVIOR_WEIGHTS) != str(DEFAULT_YOLO_WEIGHTS):
                self._behavior_model = YOLO(str(BEHAVIOR_WEIGHTS))
            else:
                self._behavior_model = None
        except Exception as e:
            logger.warning(f"YOLO 模型初始化异常，降级为直通模式: {e}")
            self._yolo_model = None
            self._behavior_model = None

    def read_raw_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """读取单帧原始 OpenCV 图像。"""
        if self._cap is None or not self._cap.isOpened():
            self._open_capture()

        if self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()
            if not ret and isinstance(self.video_source, str):
                # 视频播放至结尾时重置帧索引以实现循环回放
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self._cap.read()
            return ret, frame
        return False, None

    def _open_capture(self) -> bool:
        """打开视频采集设备或本地视频文件。"""
        if self._cap is not None:
            self._cap.release()

        try:
            if isinstance(self.video_source, str) and self.video_source.isdigit():
                self._cap = cv2.VideoCapture(int(self.video_source))
            else:
                self._cap = cv2.VideoCapture(self.video_source)

            is_opened = self._cap.isOpened()
            self.source_status.emit(is_opened, f"数据源: {self.video_source}")
            return is_opened
        except Exception as e:
            logger.error(f"打开视频源失败: {e}")
            self.source_status.emit(False, f"打开失败: {e}")
            return False

    @staticmethod
    def convert_cv_to_qimage(frame: np.ndarray) -> QImage:
        """将 OpenCV BGR 图像转换为 QImage。"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        # 使用 copy 确保 QImage 持有独立的像素缓冲区，避免底层 OpenCV 内存覆写
        return QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()

    def run(self):
        """主执行循环。"""
        self.is_running = True
        if not self._open_capture():
            self.is_running = False
            return

        frame_duration = 1.0 / TARGET_FPS
        prev_time = time.time()
        fps_smooth = float(TARGET_FPS)

        while self.is_running:
            if self.is_paused:
                self.msleep(50)
                continue

            start_t = time.time()
            ret, frame = self.read_raw_frame()

            if not ret or frame is None:
                self.msleep(30)
                continue

            detections = self._process_frame(frame)
            q_image = self.convert_cv_to_qimage(frame)

            curr_t = time.time()
            dt = curr_t - prev_time
            prev_time = curr_t
            if dt > 0:
                fps_smooth = 0.9 * fps_smooth + 0.1 * (1.0 / dt)

            self.frame_ready.emit(q_image, detections, fps_smooth)

            elapsed = time.time() - start_t
            sleep_time = frame_duration - elapsed
            if sleep_time > 0.002:
                time.sleep(sleep_time)

        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def _process_frame(self, frame: np.ndarray) -> List[DetectionBox]:
        """执行目标检测、追踪与行为识别。"""
        if self._yolo_model is None or not self.enable_yolo:
            return []

        # 每两帧执行一次推理，其余帧复用上一帧结果以平滑帧率并降低负载
        self._frame_count += 1
        if self._frame_count % 2 != 0 and self._last_detections:
            return self._last_detections

        is_behavior_model = (
            hasattr(self._yolo_model, "names") and
            isinstance(self._yolo_model.names, dict) and
            "using_device" in self._yolo_model.names.values()
        )

        detections: List[DetectionBox] = []
        try:
            track_kwargs = {
                "persist": True,
                "tracker": "bytetrack.yaml",
                "conf": CONF_THRESHOLD,
                "iou": IOU_THRESHOLD,
                "verbose": False
            }
            if not is_behavior_model:
                track_kwargs["classes"] = [int(_CocoClassId.PERSON), int(_CocoClassId.CELL_PHONE)]

            results = self._yolo_model.track(frame, **track_kwargs)

            behavior_boxes = []
            if self._behavior_model is not None:
                b_res = self._behavior_model.predict(frame, conf=0.08, verbose=False)
                if b_res and len(b_res) > 0 and b_res[0].boxes is not None:
                    behavior_boxes = b_res[0].boxes

            if results and len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                person_boxes = []
                phone_boxes = []
                for idx, box in enumerate(boxes):
                    cls_id = int(box.cls[0].cpu().numpy())
                    if cls_id == _CocoClassId.CELL_PHONE:
                        phone_boxes.append(box.xyxy[0].cpu().numpy())
                    else:
                        person_boxes.append((idx, box))

                for idx, box in person_boxes:
                    xyxy = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    cls_id = int(box.cls[0].cpu().numpy())
                    raw_name = self._yolo_model.names.get(cls_id, str(cls_id))

                    track_id = int(box.id[0].cpu().numpy()) if box.id is not None else (idx + 1)
                    px1, py1, px2, py2 = float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])

                    behavior = BehaviorType.LOOK_FORWARD

                    has_phone = any(
                        (px1 <= (ph[0] + ph[2]) / 2 <= px2) and (py1 <= (ph[1] + ph[3]) / 2 <= py2)
                        for ph in phone_boxes
                    )
                    if has_phone:
                        behavior = BehaviorType.CELL_PHONE
                    elif behavior_boxes:
                        for b_box in behavior_boxes:
                            b_xy = b_box.xyxy[0].cpu().numpy()
                            bcx, bcy = (b_xy[0] + b_xy[2]) / 2.0, (b_xy[1] + b_xy[3]) / 2.0
                            if px1 <= bcx <= px2 and py1 <= bcy <= py2:
                                b_cls = int(b_box.cls[0].cpu().numpy())
                                b_name = self._behavior_model.names.get(b_cls, str(b_cls))
                                matched = BehaviorType.from_code(b_name)
                                if matched:
                                    behavior = matched
                                    if matched.is_distracted:
                                        break

                    if is_behavior_model:
                        matched = BehaviorType.from_code(raw_name)
                        if matched:
                            behavior = matched

                    det = DetectionBox(
                        x1=px1,
                        y1=py1,
                        x2=px2,
                        y2=py2,
                        confidence=conf,
                        class_id=cls_id,
                        class_name=raw_name,
                        track_id=track_id,
                        behavior_label=behavior.label,
                        is_distracted=behavior.is_distracted
                    )
                    detections.append(det)

                    if behavior.is_distracted:
                        self._trigger_alert_if_needed(track_id, behavior.label)
        except Exception as e:
            logger.error(f"视觉推理帧处理异常: {e}", exc_info=True)

        if detections:
            person_count = sum(1 for d in detections if d.class_id != _CocoClassId.CELL_PHONE)
            self._update_stats_if_needed(person_count)

        self._last_detections = detections
        return detections

    def _trigger_alert_if_needed(self, track_id: int, label_text: str):
        """触发分心行为告警，单目标在 6 秒内去重。"""
        now = time.time()
        if track_id not in self._alert_cooldowns or now - self._alert_cooldowns[track_id] > 6.0:
            self._alert_cooldowns[track_id] = now
            alert = DistractionAlert(
                id=f"ALT-{int(now * 1000)}",
                track_id=f"#{track_id}",
                attendee_name=f"参会人 #{track_id}",
                event_type="distraction",
                event_label=label_text,
                timestamp=time.strftime("%H:%M:%S"),
                duration_seconds=3
            )
            self.alert_triggered.emit(alert)

    def _update_stats_if_needed(self, present_count: int):
        """更新出勤统计数据，最小间隔 1 秒。"""
        now = time.time()
        if now - self._last_stats_t > 1.0:
            self._last_stats_t = now
            total = 12
            cur_pres = min(total, max(1, present_count))
            cur_abs = max(0, total - cur_pres)
            rate = round(cur_pres / total * 100.0, 1)
            self.stats_updated.emit(AttendanceStats(
                total_expected=total,
                current_present=cur_pres,
                current_absent=cur_abs,
                attendance_rate=rate
            ))

    def pause(self):
        """暂停播放。"""
        self.is_paused = True

    def resume(self):
        """恢复播放。"""
        self.is_paused = False

    def toggle_play(self) -> bool:
        """切换播放与暂停状态，返回切换后是否处于播放状态。"""
        self.is_paused = not self.is_paused
        return not self.is_paused

    def stop(self):
        """停止线程并等待资源释放。"""
        self.is_running = False
        self.is_paused = False
        self.quit()
        if self.isRunning():
            self.wait(3000)

    def change_source(self, new_source: Union[str, int]):
        self.video_source = new_source
        self._open_capture()
