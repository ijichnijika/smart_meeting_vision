"""
行为与设备交互判定抽象策略基类。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple


class InteractionStrategy(ABC):
    """手机使用与人机空间交互研判策略接口。"""

    @abstractmethod
    def is_holding_phone(
        self,
        person_bbox: Tuple[int, int, int, int],
        matched_phones: List[Tuple[Any, float, float]],
        pose_keypoints: Optional[Any] = None,
    ) -> bool:
        """判定目标是否正在手持操作手机。"""
        raise NotImplementedError
