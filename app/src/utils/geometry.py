"""
几何坐标裁剪与空间计算工具。
"""

from __future__ import annotations

from typing import Optional, Tuple, Union

from app.src.model import BBox


def clamp_bbox(
    x1: Union[int, float, BBox],
    y1: Optional[Union[int, float]] = None,
    x2: Optional[Union[int, float]] = None,
    y2: Optional[Union[int, float]] = None,
    width: int = 1920,
    height: int = 1080,
) -> Tuple[int, int, int, int]:
    """裁剪限制边界框坐标在图像有效宽高范围内。支持 BBox 值对象或分离坐标输入。"""
    if isinstance(x1, BBox):
        b = x1
        w = int(y1) if y1 is not None else width
        h = int(x2) if x2 is not None else height
        return (
            max(0, min(w - 1, int(b.x1))),
            max(0, min(h - 1, int(b.y1))),
            max(0, min(w - 1, int(b.x2))),
            max(0, min(h - 1, int(b.y2))),
        )
    c_x1 = max(0, min(width - 1, int(x1)))
    c_y1 = max(0, min(height - 1, int(y1 if y1 is not None else 0)))
    c_x2 = max(0, min(width - 1, int(x2 if x2 is not None else 0)))
    c_y2 = max(0, min(height - 1, int(y2 if y2 is not None else 0)))
    return c_x1, c_y1, c_x2, c_y2
