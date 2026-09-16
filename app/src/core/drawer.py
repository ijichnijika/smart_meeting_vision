"""
OpenCV 原生帧图像绘制与可视化标注模块。
"""

from __future__ import annotations

from collections import Counter
from typing import List, Optional, Tuple, Union
import cv2
import numpy as np

from app.src.utils.geometry import clamp_bbox
from app.src.model import BehaviorType, DetectionBox, SeatZone


def render_box_with_label(
    frame: np.ndarray,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    label: str,
    box_color: Tuple[int, int, int] = (0, 255, 0),
    text_color: Tuple[int, int, int] = (0, 0, 255),
    font_scale: float = 0.6,
    thickness: int = 2,
):
    """在指定坐标绘制目标矩形框并在边缘绘制文本标签。"""
    cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, thickness)
    text_y = y1 - 6 if y1 - 6 > 14 else y1 + 18
    cv2.putText(frame, label, (x1, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, thickness)


def render_summary_bar(frame: np.ndarray, counts: Union[Counter, dict]):
    """在视频帧顶部绘制类别感知频次汇总信息横幅。"""
    if not counts:
        return
    total_num = sum(counts.values())
    summary = f"best.pt ({total_num})  " + "  ".join(f"{n}: {c}" for n, c in counts.items())
    cv2.putText(frame, summary, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.70, (0, 255, 255), 2)


def render_detections(
    frame: np.ndarray,
    detections: List[DetectionBox],
    counts: Optional[Union[Counter, dict]] = None,
    box_color: Tuple[int, int, int] = (0, 255, 0),
    text_color: Tuple[int, int, int] = (0, 0, 255),
):
    """在视频帧上原生绘制结构化 DetectionBox 列表与顶部摘要横幅。"""
    if not detections and not counts:
        return

    h, w = frame.shape[:2]
    for det in detections:
        x1, y1, x2, y2 = clamp_bbox(det.x1, det.y1, det.x2, det.y2, w, h)

        if det.class_name == "cell phone":
            render_box_with_label(frame, x1, y1, x2, y2, "phone", (0, 165, 255), (0, 0, 255), font_scale=0.5, thickness=1)
        else:
            box_col = (0, 0, 255) if det.is_distracted else box_color
            prefix = f"#{det.track_id} " if det.track_id is not None else ""
            label = f"{prefix}{det.class_name} {det.confidence:.2f}"
            render_box_with_label(frame, x1, y1, x2, y2, label, box_col, text_color)

    if counts:
        render_summary_bar(frame, counts)


# 保持向后兼容的别名导出
draw_cached_detections = render_detections


def render_evidence_snapshot(frame: np.ndarray, det: DetectionBox, timestamp_str: str) -> np.ndarray:
    """在帧上绘制违规红框、事件标签及半透明底栏时间水印，生成合规取证图片。"""
    canvas = frame.copy()
    h, w = canvas.shape[:2]
    x1, y1, x2, y2 = clamp_bbox(det.x1, det.y1, det.x2, det.y2, w, h)

    cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 0, 255), 2)
    label = f"ALERT: #{det.track_id or ''} {det.behavior_label or det.class_name} ({det.confidence:.2f})"
    render_box_with_label(canvas, x1, y1, x2, y2, label, (0, 0, 255), (0, 0, 255))

    watermark = f"EVIDENCE {timestamp_str} | TRACK: #{det.track_id or 'N/A'}"
    cv2.rectangle(canvas, (10, h - 35), (w - 10, h - 10), (15, 23, 42), -1)
    cv2.putText(canvas, watermark, (20, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    return canvas


def render_seat_leave_snapshot(frame: np.ndarray, zone: SeatZone, timestamp_str: str) -> np.ndarray:
    """在帧上绘制工位离席警示框、人员信息与时间水印，生成离席取证图片。"""
    canvas = frame.copy()
    h, w = canvas.shape[:2]
    x1, y1, x2, y2 = clamp_bbox(zone.x1, zone.y1, zone.x2, zone.y2, w, h)

    cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 0, 255), 2)
    name_str = f" {zone.assigned_attendee_name}" if zone.assigned_attendee_name else ""
    label = f"LEAVING: SEAT #{zone.seat_index}{name_str}"
    render_box_with_label(canvas, x1, y1, x2, y2, label, (0, 0, 255), (0, 0, 255))

    watermark = f"EVIDENCE {timestamp_str} | SEAT #{zone.seat_index} ABSENT | {zone.assigned_attendee_name or 'UNASSIGNED'}"
    cv2.rectangle(canvas, (10, h - 35), (w - 10, h - 10), (15, 23, 42), -1)
    cv2.putText(canvas, watermark, (20, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    return canvas


def render_seat_zones(frame: np.ndarray, zones: List[SeatZone]):
    """在 OpenCV 帧上绘制工位区域与当前在席状态。"""
    h, w = frame.shape[:2]
    for zone in zones:
        x1, y1, x2, y2 = clamp_bbox(zone.x1, zone.y1, zone.x2, zone.y2, w, h)
        if zone.current_status == "occupied":
            color = (0, 200, 0)
            status_text = "OCCUPIED"
        elif zone.current_status == "absent":
            color = (0, 0, 255)
            status_text = "ABSENT"
        else:
            color = (180, 180, 180)
            status_text = "EMPTY"

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        name_str = f" {zone.assigned_attendee_name}" if zone.assigned_attendee_name else ""
        label = f"#{zone.seat_index}{name_str} [{status_text}]"
        render_box_with_label(frame, x1, y1, x2, y2, label, color, color, font_scale=0.5, thickness=1)


def draw_detections(
    frame: np.ndarray,
    boxes,
    names: Union[dict, list],
    box_color: Tuple[int, int, int] = (0, 255, 0),
    text_color: Tuple[int, int, int] = (0, 0, 255),
) -> Tuple[Counter, List[DetectionBox]]:
    """在视频帧上原地绘制目标矩形框与左上角英文字符标注，统计类别频次并在顶部输出概览。"""
    counter = Counter()
    detections: List[DetectionBox] = []

    if boxes is None:
        return counter, detections
    num_boxes = len(boxes) if hasattr(boxes, "__len__") else (len(boxes.xyxy) if hasattr(boxes, "xyxy") else 0)
    if num_boxes == 0:
        return counter, detections

    xyxy = boxes.xyxy.cpu().numpy() if hasattr(boxes.xyxy, "cpu") else np.asarray(boxes.xyxy)
    cls_arr = boxes.cls.cpu().numpy() if hasattr(boxes.cls, "cpu") else np.asarray(boxes.cls)
    conf_arr = boxes.conf.cpu().numpy() if hasattr(boxes.conf, "cpu") else np.asarray(boxes.conf)

    ids_arr = None
    if hasattr(boxes, "id") and boxes.id is not None:
        ids_arr = boxes.id.cpu().numpy() if hasattr(boxes.id, "cpu") else np.asarray(boxes.id)

    h, w = frame.shape[:2]

    for i in range(len(xyxy)):
        x1, y1, x2, y2 = clamp_bbox(xyxy[i][0], xyxy[i][1], xyxy[i][2], xyxy[i][3], w, h)

        cls_id = int(cls_arr[i])
        if isinstance(names, dict):
            name = str(names.get(cls_id, cls_id))
        elif isinstance(names, (list, tuple)) and cls_id < len(names):
            name = str(names[cls_id])
        else:
            name = str(cls_id)

        score = float(conf_arr[i])
        track_id = int(ids_arr[i]) if ids_arr is not None and len(ids_arr) > i and ids_arr[i] is not None else None

        counter[name] += 1

        is_distracted = BehaviorType.is_distracted_code(name)
        behavior = BehaviorType.from_code(name)
        behavior_label = behavior.label if behavior else name

        detections.append(DetectionBox(
            x1=float(x1),
            y1=float(y1),
            x2=float(x2),
            y2=float(y2),
            confidence=score,
            class_id=cls_id,
            class_name=name,
            track_id=track_id,
            behavior_label=behavior_label,
            is_distracted=is_distracted,
        ))

    render_detections(frame, detections, counter, box_color, text_color)
    return counter, detections
