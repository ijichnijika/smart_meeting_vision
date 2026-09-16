"""
视觉推理与目标追踪引擎，负责 YOLOv8 模型推理、ByteTrack 追踪与行为空间几何推断。
"""

from __future__ import annotations

import math
import os
from collections import Counter
from enum import IntEnum
from typing import List, Optional, Tuple, Union
import numpy as np

from app.config import (
    BEHAVIOR_WEIGHTS,
    CONF_THRESHOLD,
    DEFAULT_YOLO_WEIGHTS,
    IOU_THRESHOLD,
    POSE_WEIGHTS,
)
from app.src.common.logger import get_logger
from app.src.core.strategy import BBoxOverlapStrategy, PoseWristDistanceStrategy
from app.src.model import BehaviorType, DetectionBox
from app.src.utils.geometry import clamp_bbox

logger = get_logger("vision_detector")


class _CocoClassId(IntEnum):
    PERSON = 0
    CELL_PHONE = 67


class VisionDetector:
    """封装 YOLOv8 与行为检测模型，输出标准化 DetectionBox 实体与统计频次。"""

    def __init__(self, enable_yolo: bool = True):
        self.enable_yolo = enable_yolo
        self._yolo_model = None
        self._behavior_model = None
        self._pose_model = None
        self._pose_strategy = PoseWristDistanceStrategy()
        self._fallback_strategy = BBoxOverlapStrategy()
        if self.enable_yolo:
            self._init_models()

    def _init_models(self):
        """初始化目标检测与行为识别模型，在权重缺失时优雅降级。"""
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

            if os.path.exists(POSE_WEIGHTS):
                self._pose_model = YOLO(str(POSE_WEIGHTS))
            else:
                self._pose_model = None
        except Exception as e:
            logger.warning(f"YOLO 模型初始化异常，降级为直通模式: {e}")
            self._yolo_model = None
            self._behavior_model = None
            self._pose_model = None

    @property
    def is_ready(self) -> bool:
        return self._yolo_model is not None

    def detect(self, frame: np.ndarray) -> Tuple[List[DetectionBox], Counter]:
        """对单帧图像执行目标检测、ByteTrack 追踪及多模态行为几何空间融合推断。"""
        if self._yolo_model is None or not self.enable_yolo:
            return [], Counter()

        counter = Counter()
        detections: List[DetectionBox] = []

        is_behavior_model = (
            hasattr(self._yolo_model, "names") and
            isinstance(self._yolo_model.names, dict) and
            "using_device" in self._yolo_model.names.values()
        )

        try:
            track_kwargs = {
                "persist": True,
                "tracker": "bytetrack.yaml",
                "conf": CONF_THRESHOLD,
                "iou": IOU_THRESHOLD,
                "verbose": False,
                "imgsz": 480,
            }
            if not is_behavior_model:
                track_kwargs["classes"] = [int(_CocoClassId.PERSON), int(_CocoClassId.CELL_PHONE)]

            results = self._yolo_model.track(frame, **track_kwargs)

            # 提取自训行为模型预测框 (best.pt)
            behavior_boxes = []
            if self._behavior_model is not None:
                b_res = self._behavior_model.predict(frame, conf=0.15, verbose=False, imgsz=480)
                if b_res and len(b_res) > 0 and b_res[0].boxes is not None:
                    behavior_boxes = b_res[0].boxes

            if results and len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                h, w = frame.shape[:2]

                person_boxes = []
                phone_boxes = []

                for idx, box in enumerate(boxes):
                    cls_id = int(box.cls[0].cpu().numpy())
                    if cls_id == _CocoClassId.CELL_PHONE:
                        phone_boxes.append(box)
                    else:
                        person_boxes.append((idx, box))

                # 按需惰性触发姿态模型：仅当检出手机时才启动姿态推理复核
                pose_keypoints = None
                if self._pose_model is not None and len(phone_boxes) > 0:
                    p_res = self._pose_model.predict(frame, conf=0.20, verbose=False, imgsz=480)
                    if p_res and len(p_res) > 0 and getattr(p_res[0], "keypoints", None) is not None:
                        pose_keypoints = p_res[0].keypoints

                for idx, box in person_boxes:
                    xyxy = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    cls_id = int(box.cls[0].cpu().numpy())
                    raw_name = self._yolo_model.names.get(cls_id, str(cls_id)) if hasattr(self._yolo_model, "names") else str(cls_id)
                    track_id = int(box.id[0].cpu().numpy()) if box.id is not None else (idx + 1)
                    px1, py1, px2, py2 = clamp_bbox(xyxy[0], xyxy[1], xyxy[2], xyxy[3], w, h)

                    # 1. 优先从自训行为模型中匹配该人员中心区域的最佳行为分类
                    best_behavior_code = "look_forward"
                    best_behavior_conf = 0.0
                    if behavior_boxes:
                        for b_box in behavior_boxes:
                            b_xy = b_box.xyxy[0].cpu().numpy()
                            bcx, bcy = (b_xy[0] + b_xy[2]) / 2.0, (b_xy[1] + b_xy[3]) / 2.0
                            if px1 <= bcx <= px2 and py1 <= bcy <= py2:
                                b_cls = int(b_box.cls[0].cpu().numpy())
                                b_name = self._behavior_model.names.get(b_cls, str(b_cls))
                                b_conf = float(b_box.conf[0].cpu().numpy())
                                if b_conf > best_behavior_conf:
                                    best_behavior_conf = b_conf
                                    best_behavior_code = b_name

                    # 2. 检查人员包围盒内是否存在手机
                    matched_phones = []
                    for ph in phone_boxes:
                        ph_xy = ph.xyxy[0].cpu().numpy()
                        ph_cx = (ph_xy[0] + ph_xy[2]) / 2.0
                        ph_cy = (ph_xy[1] + ph_xy[3]) / 2.0
                        if px1 <= ph_cx <= px2 and py1 <= ph_cy <= py2:
                            matched_phones.append((ph_xy, ph_cx, ph_cy))

                    # 委托策略执行设备交互研判
                    strategy = self._pose_strategy if pose_keypoints is not None else self._fallback_strategy
                    is_holding = strategy.is_holding_phone((px1, py1, px2, py2), matched_phones, pose_keypoints)

                    if is_holding:
                        behavior_code = "using_device"
                        is_distracted = True
                    elif best_behavior_code == "using_device" and pose_keypoints is not None:
                        behavior_code = "look_forward"
                        is_distracted = False
                    else:
                        behavior_code = best_behavior_code
                        is_distracted = BehaviorType.is_distracted_code(behavior_code)

                    if is_behavior_model:
                        behavior_code = raw_name
                        is_distracted = BehaviorType.is_distracted_code(behavior_code)

                    counter[behavior_code] += 1
                    b_type = BehaviorType.from_code(behavior_code)
                    label_text = b_type.label if b_type else behavior_code

                    detections.append(DetectionBox(
                        x1=float(px1),
                        y1=float(py1),
                        x2=float(px2),
                        y2=float(py2),
                        confidence=conf,
                        class_id=cls_id,
                        class_name=behavior_code,
                        track_id=track_id,
                        behavior_label=label_text,
                        is_distracted=is_distracted,
                    ))

                for ph in phone_boxes:
                    counter["cell phone"] += 1
                    ph_xyxy = ph.xyxy[0].cpu().numpy()
                    ph_conf = float(ph.conf[0].cpu().numpy())
                    x1, y1, x2, y2 = clamp_bbox(ph_xyxy[0], ph_xyxy[1], ph_xyxy[2], ph_xyxy[3], w, h)
                    detections.append(DetectionBox(
                        x1=float(x1),
                        y1=float(y1),
                        x2=float(x2),
                        y2=float(y2),
                        confidence=ph_conf,
                        class_id=int(_CocoClassId.CELL_PHONE),
                        class_name="cell phone",
                        track_id=None,
                        behavior_label="cell phone",
                        is_distracted=False,
                    ))

        except Exception as e:
            logger.error(f"视觉推理帧处理异常: {e}", exc_info=True)

        return detections, counter
