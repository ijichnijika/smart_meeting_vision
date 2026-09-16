"""
全局通用基础设施包。
"""

from app.src.common.exceptions import (
    MeetingVisionError,
    VideoSourceError,
    ModelLoadError,
    AttendeeNotFoundError,
    TrackingBindingError,
    ReportExportError,
)
from app.src.common.logger import get_logger

__all__ = [
    "MeetingVisionError",
    "VideoSourceError",
    "ModelLoadError",
    "AttendeeNotFoundError",
    "TrackingBindingError",
    "ReportExportError",
    "get_logger",
]
