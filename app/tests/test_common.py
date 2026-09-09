"""
通用基础设施包测试 (Common Package Tests)
"""

from app.src.common import (
    MeetingVisionError, VideoSourceError, AttendeeNotFoundError
)
from app.src.common import get_logger
from app.src.utils.calculate_utils import format_duration, current_time_str, clamp


def test_custom_exceptions():
    """测试系统业务异常的继承与错误码"""
    base_err = MeetingVisionError("基础异常")
    assert str(base_err) == "[SYSTEM_ERROR] 基础异常"

    vid_err = VideoSourceError("视频文件不存在")
    assert isinstance(vid_err, MeetingVisionError)
    assert vid_err.code == "VIDEO_SOURCE_ERROR"

    att_err = AttendeeNotFoundError("EMP999")
    assert "EMP999" in str(att_err)
    assert att_err.code == "ATTENDEE_NOT_FOUND"


def test_utils_functions():
    """测试通用工具函数"""
    assert format_duration(0) == "00:00"
    assert format_duration(65) == "01:05"
    assert format_duration(3665) == "01:01:05"

    t_str = current_time_str("%H:%M")
    assert len(t_str) == 5

    assert clamp(5, 0, 10) == 5
    assert clamp(-2, 0, 10) == 0
    assert clamp(15, 0, 10) == 10


def test_logger_creation():
    """测试日志器能够正确创建"""
    logger = get_logger("test_logger")
    assert logger.name == "test_logger"
