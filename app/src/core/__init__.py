"""
视觉核心与多媒体基础设施包。
"""

from app.src.core.capture import VideoCaptureStream
from app.src.core.detector import VisionDetector
from app.src.core.drawer import (
    draw_cached_detections,
    draw_detections,
    render_box_with_label,
    render_detections,
    render_evidence_snapshot,
    render_seat_leave_snapshot,
    render_seat_zones,
    render_summary_bar,
)
from app.src.utils.geometry import clamp_bbox
from app.src.core.recorder import SnapshotManager, VideoRecorder
from app.src.core.seat_tracker import SeatZoneTracker

__all__ = [
    "VideoCaptureStream",
    "VisionDetector",
    "VideoRecorder",
    "SnapshotManager",
    "SeatZoneTracker",
    "clamp_bbox",
    "draw_detections",
    "render_detections",
    "render_evidence_snapshot",
    "render_seat_leave_snapshot",
    "render_seat_zones",
    "render_box_with_label",
    "render_summary_bar",
    "draw_cached_detections",
]
