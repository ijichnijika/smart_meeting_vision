"""
基于空间包围盒中心点包含关系的设备交互降级研判策略。
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

from app.src.core.strategy.base import InteractionStrategy


class BBoxOverlapStrategy(InteractionStrategy):
    """当无可用骨骼姿态数据时，依据手机中心落在人体框内直接判定。"""

    def is_holding_phone(
        self,
        person_bbox: Tuple[int, int, int, int],
        matched_phones: List[Tuple[Any, float, float]],
        pose_keypoints: Optional[Any] = None,
    ) -> bool:
        return len(matched_phones) > 0
