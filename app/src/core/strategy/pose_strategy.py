"""
基于人体骨骼手腕关键点欧氏距离的设备交互研判策略。
"""

from __future__ import annotations

import math
from typing import Any, List, Optional, Tuple

from app.src.core.strategy.base import InteractionStrategy


class PoseWristDistanceStrategy(InteractionStrategy):
    """通过双手手腕关键点与手机中心的欧氏距离判断是否真实手持手机。"""

    def __init__(self, wrist_dist_threshold: float = 80.0, scale_factor: float = 2.5):
        self.wrist_dist_threshold = wrist_dist_threshold
        self.scale_factor = scale_factor

    def is_holding_phone(
        self,
        person_bbox: Tuple[int, int, int, int],
        matched_phones: List[Tuple[Any, float, float]],
        pose_keypoints: Optional[Any] = None,
    ) -> bool:
        if not matched_phones:
            return False

        if pose_keypoints is None or not hasattr(pose_keypoints, "xy"):
            return True

        px1, py1, px2, py2 = person_bbox
        kp_xy = pose_keypoints.xy.cpu().numpy() if hasattr(pose_keypoints.xy, "cpu") else pose_keypoints.xy
        kp_conf = None
        if hasattr(pose_keypoints, "conf") and pose_keypoints.conf is not None:
            kp_conf = pose_keypoints.conf.cpu().numpy() if hasattr(pose_keypoints.conf, "cpu") else pose_keypoints.conf

        for p_idx in range(len(kp_xy)):
            # COCO 关键点 9: left_wrist, 10: right_wrist
            for wrist_idx in (9, 10):
                wx, wy = kp_xy[p_idx][wrist_idx]
                if px1 <= wx <= px2 and py1 <= wy <= py2:
                    conf_ok = True
                    if kp_conf is not None and len(kp_conf) > p_idx:
                        conf_ok = float(kp_conf[p_idx][wrist_idx]) > 0.2

                    if conf_ok:
                        for ph_xy, ph_cx, ph_cy in matched_phones:
                            dist = math.hypot(wx - ph_cx, wy - ph_cy)
                            phone_scale = max(ph_xy[2] - ph_xy[0], ph_xy[3] - ph_xy[1])
                            dynamic_threshold = max(self.wrist_dist_threshold, phone_scale * self.scale_factor)
                            if dist <= dynamic_threshold:
                                return True
        return False
