"""
工位几何空间匹配与时序离席防抖跟踪模块。
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple
import numpy as np

from app.src.common.logger import get_logger
from app.src.utils.geometry import clamp_bbox
from app.src.model import Attendee, DetectionBox, DistractionAlert, SeatZone

logger = get_logger("seat_tracker")


class SeatZoneTracker:
    """工位状态机与时序离席防抖检测器。

    负责在每一视频帧中将检测目标与工位区域进行空间重叠计算，
    并在目标连续消失达到防抖阈值时触发离席判定与取证截图。
    """

    def __init__(self, debounce_frames: int = 15, recovery_frames: int = 1, absent_seconds: float = 3.0):
        self.debounce_frames = debounce_frames
        self.recovery_frames = recovery_frames
        self.absent_seconds = absent_seconds
        self.zones: List[SeatZone] = []
        self._zone_states: Dict[str, dict] = {}

    def _get_zone_key(self, zone: SeatZone) -> str:
        if zone.id is not None and zone.id > 0:
            return f"id_{zone.id}"
        return f"idx_{zone.seat_index}"

    def set_zones(self, zones: List[SeatZone]):
        """设置当前监控的工位区域列表，保留已存在工位的时序计数状态。"""
        new_states = {}
        for z in zones:
            key = self._get_zone_key(z)
            if key in self._zone_states:
                new_states[key] = self._zone_states[key]
                new_states[key]["zone"] = z
            else:
                new_states[key] = {
                    "zone": z,
                    "empty_count": 0,
                    "occupied_count": 0,
                    "absent_start_time": None,
                    "status": z.current_status,
                    "alerted": False,
                }
        self.zones = zones
        self._zone_states = new_states

    def get_zones(self) -> List[SeatZone]:
        """返回当前所有工位区域副本。"""
        return list(self.zones)

    def update(
        self,
        frame: Optional[np.ndarray],
        detections: List[DetectionBox],
    ) -> Tuple[List[SeatZone], List[DistractionAlert], bool]:
        """按帧更新工位状态，执行空间重叠计算与离席防抖状态机流转。

        返回: (最新工位列表, 本帧触发的离席告警列表, 是否发生状态变更)
        """
        if not self.zones:
            return [], [], False

        now = time.time()
        person_boxes = [d for d in detections if d.class_name != "cell phone"]
        alerts: List[DistractionAlert] = []
        has_changed = False

        for zone in self.zones:
            key = self._get_zone_key(zone)
            state = self._zone_states.get(key)
            if state is None:
                state = {
                    "zone": zone,
                    "empty_count": 0,
                    "occupied_count": 0,
                    "absent_start_time": None,
                    "status": zone.current_status,
                    "alerted": False,
                }
                self._zone_states[key] = state

            is_occupied_now = False
            for det in person_boxes:
                cx, cy = det.bbox.center
                if zone.contains_point(cx, cy):
                    is_occupied_now = True
                    break
                if zone.calculate_intersection_ratio(det.x1, det.y1, det.x2, det.y2) >= 0.25:
                    is_occupied_now = True
                    break

            if is_occupied_now:
                state["empty_count"] = 0
                state["absent_start_time"] = None
                state["occupied_count"] += 1
                if zone.current_status != "occupied":
                    if state["occupied_count"] >= self.recovery_frames or zone.current_status == "empty":
                        zone.current_status = "occupied"
                        state["status"] = "occupied"
                        state["alerted"] = False
                        has_changed = True
            else:
                state["occupied_count"] = 0
                state["empty_count"] += 1
                if state["absent_start_time"] is None:
                    state["absent_start_time"] = now

                duration_away = now - state["absent_start_time"]
                is_debounced_absent = (
                    state["empty_count"] >= self.debounce_frames
                    or duration_away >= self.absent_seconds
                )

                if is_debounced_absent:
                    if zone.current_status != "absent":
                        zone.current_status = "absent"
                        state["status"] = "absent"
                        has_changed = True

                    if not state["alerted"]:
                        state["alerted"] = True
                        att_name = zone.assigned_attendee_name or f"工位 #{zone.seat_index}"
                        alert = DistractionAlert(
                            id=f"ALT-LEAVE-{int(now * 1000)}",
                            track_id=f"#{zone.seat_index}",
                            attendee_name=att_name,
                            event_type="leaving_seat",
                            event_label="工位离席告警",
                            timestamp=time.strftime("%H:%M:%S"),
                            duration_seconds=3,
                            snapshot_path=None,
                        )
                        alerts.append(alert)

        return self.zones, alerts, has_changed

    @staticmethod
    def auto_generate_zones(
        detections: List[DetectionBox],
        attendees: List[Attendee],
        frame_width: int,
        frame_height: int,
        meeting_id: int = 1,
    ) -> List[SeatZone]:
        """根据当前画面的检测人员目标自动生成工位布局并与参会人员按序绑定。"""
        persons = [d for d in detections if d.class_name != "cell phone"]
        if not persons:
            return []

        # 按在席画面从左至右、从上至下的空间顺序排列
        sorted_persons = sorted(persons, key=lambda p: (round(p.y1 / 60.0), p.x1))

        generated: List[SeatZone] = []
        for idx, p in enumerate(sorted_persons):
            w_box = p.x2 - p.x1
            h_box = p.y2 - p.y1
            # 适度外扩包围盒作为固定物理工位空间
            pad_x = w_box * 0.12
            pad_y = h_box * 0.10

            x1, y1, x2, y2 = clamp_bbox(
                p.x1 - pad_x,
                p.y1 - pad_y,
                p.x2 + pad_x,
                p.y2 + pad_y,
                frame_width,
                frame_height,
            )

            att = attendees[idx] if idx < len(attendees) else None
            assigned_id = None
            assigned_name = None
            assigned_emp = None
            if att:
                assigned_name = att.name
                assigned_emp = att.id

            generated.append(
                SeatZone(
                    id=None,
                    meeting_id=meeting_id,
                    seat_index=idx + 1,
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    assigned_attendee_id=assigned_id,
                    assigned_attendee_name=assigned_name,
                    assigned_employee_id=assigned_emp,
                    current_status="occupied",
                )
            )

        return generated
