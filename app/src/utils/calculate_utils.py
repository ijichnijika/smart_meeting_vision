"""
通用时间与数值计算工具函数。
"""

from datetime import datetime
from typing import Union


def format_duration(seconds: int) -> str:
    """将秒数转换为分秒或时分秒时间字符串。"""
    if seconds < 0:
        seconds = 0
    hrs = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def current_time_str(fmt: str = "%H:%M:%S") -> str:
    """获取当前时间格式化字符串"""
    return datetime.now().strftime(fmt)


def clamp(val: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """数值范围边界截断"""
    return max(min_val, min(val, max_val))
