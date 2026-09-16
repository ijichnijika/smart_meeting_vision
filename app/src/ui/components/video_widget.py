"""
视频渲染与交互画布组件。
"""

from typing import List, Optional, Tuple
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

from app.src.model import DetectionBox, SeatZone
from app.src.ui.theme import ThemeColors


class VideoWidget(QWidget):
    """视频图像渲染与目标拾取交互组件。"""

    tracking_id_selected = Signal(int)
    seat_zone_drawn = Signal(int, int, int, int)
    seat_zone_clicked = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_frame: Optional[QImage] = None
        self.detections: List[DetectionBox] = []
        self.seat_zones: List[SeatZone] = []
        self.current_fps: float = 0.0
        self.selected_track_id: Optional[int] = None
        self._render_rect = QRectF()

        self.is_drawing_seat: bool = False
        self._is_dragging_rect: bool = False
        self._drag_start_pos = QPointF()
        self._drag_current_pos = QPointF()

        self.setMinimumSize(480, 270)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

    def set_seat_zones(self, zones: List[SeatZone]):
        """设置当前需要叠加渲染的工位列表。"""
        self.seat_zones = list(zones)
        self.update()

    def set_drawing_seat_mode(self, enabled: bool):
        """开启或关闭鼠标框选工位模式。"""
        self.is_drawing_seat = enabled
        self._is_dragging_rect = False
        if enabled:
            self.setCursor(Qt.CrossCursor)
        else:
            self.unsetCursor()
        self.update()

    def update_frame(self, image: QImage, detections: List[DetectionBox], fps: float = 0.0):
        """更新当前视频帧与检测目标列表。"""
        self.current_frame = image
        self.detections = detections
        self.current_fps = fps
        self.update()

    def set_selected_track_id(self, track_id: Optional[int]):
        """设置当前高亮选中的目标跟踪标识。"""
        self.selected_track_id = track_id
        self.update()

    def paintEvent(self, event):
        """绘制视频图像、待机提示及所有检测目标。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w, h = self.width(), self.height()
        canvas_rect = QRectF(0, 0, w, h)
        painter.fillRect(canvas_rect, QColor(ThemeColors.CANVAS_BG))

        if self.current_frame is None or self.current_frame.isNull():
            self._draw_standby_screen(painter, canvas_rect)
            return

        img_w = self.current_frame.width()
        img_h = self.current_frame.height()
        if img_w <= 0 or img_h <= 0:
            return

        render_rect = self._get_render_rect()
        if not render_rect.isValid() or render_rect.width() <= 0:
            return

        scale = render_rect.width() / img_w
        draw_x, draw_y = render_rect.x(), render_rect.y()

        painter.drawImage(render_rect, self.current_frame)

        for zone in self.seat_zones:
            self._draw_seat_zone_item(painter, zone, draw_x, draw_y, scale)

        for det in self.detections:
            self._draw_detection_item(painter, det, draw_x, draw_y, scale)

        if self.is_drawing_seat and self._is_dragging_rect:
            self._draw_rubber_band(painter, scale)

        self._draw_hud(painter)

    def _draw_standby_screen(self, painter: QPainter, rect: QRectF):
        """绘制待机十字准星与平滑状态指引。"""
        cx, cy = rect.center().x(), rect.center().y()

        cross_pen = QPen(QColor(ThemeColors.CANVAS_GRID), 1.2, Qt.SolidLine)
        painter.setPen(cross_pen)
        painter.drawLine(QPointF(cx - 36, cy), QPointF(cx + 36, cy))
        painter.drawLine(QPointF(cx, cy - 36), QPointF(cx, cy + 36))

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(ThemeColors.CANVAS_GRID), 1.2))
        painter.drawEllipse(QPointF(cx, cy), 20, 20)
        painter.drawEllipse(QPointF(cx, cy), 32, 32)

        painter.setPen(QColor(ThemeColors.TEXT_MUTED))
        font = QFont("PingFang SC", 12, QFont.Medium)
        painter.setFont(font)
        text_rect = QRectF(rect.x(), cy + 44, rect.width(), 24)
        painter.drawText(text_rect, Qt.AlignCenter, "等待视频信号接入...")

    def _resolve_det_style(self, det: DetectionBox, is_selected: bool) -> Tuple[QColor, QColor, QColor, str]:
        """计算检测框边框颜色、背景填充色与显示文本。"""
        if det.is_distracted:
            stroke = QColor(ThemeColors.BOX_DISTRACT)
            fill = QColor(220, 38, 38, 30)
            tag_bg = QColor(220, 38, 38, 235)
        elif is_selected:
            stroke = QColor(ThemeColors.BOX_SELECTED)
            fill = QColor(139, 92, 246, 35)
            tag_bg = QColor(139, 92, 246, 235)
        elif det.class_id == 67:
            stroke = QColor(ThemeColors.WARNING)
            fill = QColor(217, 119, 6, 30)
            tag_bg = QColor(217, 119, 6, 235)
        else:
            stroke = QColor(ThemeColors.BOX_PERSON)
            fill = QColor(59, 130, 246, 20)
            tag_bg = QColor(37, 99, 235, 225)

        track_tag = f"#{det.track_id} " if det.track_id is not None else ""
        name_tag = f"{det.bound_attendee_name} · " if det.bound_attendee_name else ""
        conf_tag = f" {int(det.confidence * 100)}%"

        if det.is_distracted:
            label = f"{track_tag}{name_tag}{det.behavior_label or '分心告警'}"
        elif det.class_id == 67:
            label = f"移动设备{conf_tag}"
        elif det.behavior_label:
            label = f"{track_tag}{name_tag}{det.behavior_label}{conf_tag}"
        else:
            label = f"{track_tag}{name_tag}在席{conf_tag}"

        return stroke, fill, tag_bg, label

    def _draw_detection_item(self, painter: QPainter, det: DetectionBox,
                             ox: float, oy: float, scale: float):
        """绘制单个人员目标框、角点标记与标签。"""
        bx = ox + det.x1 * scale
        by = oy + det.y1 * scale
        bw = (det.x2 - det.x1) * scale
        bh = (det.y2 - det.y1) * scale
        box_rect = QRectF(bx, by, bw, bh)

        is_selected = (det.track_id is not None and det.track_id == self.selected_track_id)
        stroke, fill, tag_bg, label = self._resolve_det_style(det, is_selected)

        pen = QPen(stroke, 1.8 if not is_selected else 2.4)
        painter.setPen(pen)
        painter.setBrush(QBrush(fill))
        painter.drawRoundedRect(box_rect, 4, 4)

        self._draw_corner_accents(painter, box_rect, stroke)
        self._draw_tag_pill(painter, box_rect, tag_bg, label, oy)

    def _draw_corner_accents(self, painter: QPainter, rect: QRectF, color: QColor):
        """在矩形框四角绘制角点标记。"""
        accent_len = min(10.0, rect.width() / 4.0, rect.height() / 4.0)
        accent_pen = QPen(color, 2.5, Qt.SolidLine, Qt.SquareCap)
        painter.setPen(accent_pen)

        x1, y1, x2, y2 = rect.left(), rect.top(), rect.right(), rect.bottom()
        painter.drawLine(QPointF(x1, y1), QPointF(x1 + accent_len, y1))
        painter.drawLine(QPointF(x1, y1), QPointF(x1, y1 + accent_len))
        painter.drawLine(QPointF(x2, y1), QPointF(x2 - accent_len, y1))
        painter.drawLine(QPointF(x2, y1), QPointF(x2, y1 + accent_len))
        painter.drawLine(QPointF(x1, y2), QPointF(x1 + accent_len, y2))
        painter.drawLine(QPointF(x1, y2), QPointF(x1, y2 - accent_len))
        painter.drawLine(QPointF(x2, y2), QPointF(x2 - accent_len, y2))
        painter.drawLine(QPointF(x2, y2), QPointF(x2, y2 - accent_len))

    def _draw_tag_pill(self, painter: QPainter, box: QRectF, bg_color: QColor, text: str, min_y: float):
        """在检测框上方绘制包含类别与属性的信息标签。"""
        tag_font = QFont("PingFang SC", 10, QFont.DemiBold)
        painter.setFont(tag_font)
        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(text) + 12
        text_h = fm.height() + 4

        tag_x = box.left()
        tag_y = max(min_y, box.top() - text_h - 3)
        tag_rect = QRectF(tag_x, tag_y, text_w, text_h)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(tag_rect, 3, 3)

        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(tag_rect, Qt.AlignCenter, text)

    def _draw_hud(self, painter: QPainter):
        """在画面绘制状态指示信息。"""
        live_rect = QRectF(12, 12, 142, 26)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(15, 23, 42, 210))
        painter.drawRoundedRect(live_rect, 13, 13)

        painter.setBrush(QBrush(QColor("#EF4444")))
        painter.drawEllipse(QPointF(24, 25), 4.0, 4.0)

        painter.setPen(QColor("#F1F5F9"))
        painter.setFont(QFont("PingFang SC", 9, QFont.DemiBold))
        painter.drawText(QRectF(34, 12, 112, 26), Qt.AlignVCenter, "实时监控 · 1080P")

        hud_text = f"FPS {self.current_fps:.1f}  ·  目标 {len(self.detections)}"
        hud_font = QFont("SF Pro Text", 9, QFont.Medium)
        painter.setFont(hud_font)
        fm = painter.fontMetrics()
        hud_w = fm.horizontalAdvance(hud_text) + 20
        hud_h = 26

        rx = self.width() - hud_w - 12
        ry = 12
        hud_rect = QRectF(rx, ry, hud_w, hud_h)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(15, 23, 42, 210))
        painter.drawRoundedRect(hud_rect, 13, 13)

        painter.setPen(QColor("#F1F5F9"))
        painter.drawText(hud_rect, Qt.AlignCenter, hud_text)

    def _draw_seat_zone_item(self, painter: QPainter, zone: SeatZone, ox: float, oy: float, scale: float):
        """在视频画面上绘制工位区域虚线框与状态胶囊标签。"""
        zx = ox + zone.x1 * scale
        zy = oy + zone.y1 * scale
        zw = (zone.x2 - zone.x1) * scale
        zh = (zone.y2 - zone.y1) * scale
        zone_rect = QRectF(zx, zy, zw, zh)

        if zone.current_status == "occupied":
            stroke = QColor(16, 185, 129, 210)
            fill = QColor(16, 185, 129, 25)
            tag_bg = QColor(16, 185, 129, 230)
            tag_text = f"工位 #{zone.seat_index} · {zone.assigned_attendee_name or '在席'}"
        elif zone.current_status == "absent":
            stroke = QColor(239, 68, 68, 230)
            fill = QColor(239, 68, 68, 35)
            tag_bg = QColor(239, 68, 68, 230)
            tag_text = f"工位 #{zone.seat_index} · {zone.assigned_attendee_name or ''} (离席)"
        else:
            stroke = QColor(148, 163, 184, 180)
            fill = QColor(148, 163, 184, 15)
            tag_bg = QColor(100, 116, 139, 200)
            tag_text = f"工位 #{zone.seat_index} · 空置"

        pen = QPen(stroke, 1.8, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(QBrush(fill))
        painter.drawRoundedRect(zone_rect, 4, 4)

        self._draw_tag_pill(painter, zone_rect, tag_bg, tag_text, oy)

    def _draw_rubber_band(self, painter: QPainter, scale: float):
        """绘制鼠标框选工位时的实时预览框与尺寸提示。"""
        p1 = self._drag_start_pos
        p2 = self._drag_current_pos
        rx = min(p1.x(), p2.x())
        ry = min(p1.y(), p2.y())
        rw = abs(p1.x() - p2.x())
        rh = abs(p1.y() - p2.y())
        preview_rect = QRectF(rx, ry, rw, rh)

        pen = QPen(QColor("#3B82F6"), 2, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(59, 130, 246, 35)))
        painter.drawRoundedRect(preview_rect, 4, 4)

        tag_text = f"划定工位范围: {int(rw / max(0.01, scale))} × {int(rh / max(0.01, scale))}"
        self._draw_tag_pill(painter, preview_rect, QColor("#2563EB"), tag_text, 0)

    def _get_render_rect(self) -> QRectF:
        """获取视频渲染几何矩形，若未触发绘制则根据尺寸动态推导。"""
        if self._render_rect.isValid():
            return self._render_rect
        if self.current_frame and not self.current_frame.isNull() and self.current_frame.width() > 0:
            w, h = max(1, self.width()), max(1, self.height())
            img_w = self.current_frame.width()
            img_h = self.current_frame.height()
            scale = min(w / img_w, h / img_h)
            draw_w = img_w * scale
            draw_h = img_h * scale
            draw_x = (w - draw_w) / 2.0
            draw_y = (h - draw_h) / 2.0
            self._render_rect = QRectF(draw_x, draw_y, draw_w, draw_h)
            return self._render_rect
        return QRectF()

    def mousePressEvent(self, event):
        """响应鼠标点击事件，处理框选工位与目标拾取。"""
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        if self.is_drawing_seat:
            self._drag_start_pos = event.position()
            self._drag_current_pos = event.position()
            self._is_dragging_rect = True
            self.update()
            return

        render_rect = self._get_render_rect()
        if not render_rect.isValid() or not self.current_frame or self.current_frame.width() <= 0:
            super().mousePressEvent(event)
            return

        click_pos = event.position()
        scale = render_rect.width() / self.current_frame.width()
        ox, oy = render_rect.x(), render_rect.y()

        for zone in self.seat_zones:
            zx = ox + zone.x1 * scale
            zy = oy + zone.y1 * scale
            zw = (zone.x2 - zone.x1) * scale
            zh = (zone.y2 - zone.y1) * scale
            if QRectF(zx, zy, zw, zh).contains(click_pos):
                self.seat_zone_clicked.emit(zone)
                return

        for det in self.detections:
            if det.track_id is None:
                continue
            bx = ox + det.x1 * scale
            by = oy + det.y1 * scale
            bw = (det.x2 - det.x1) * scale
            bh = (det.y2 - det.y1) * scale
            if QRectF(bx, by, bw, bh).contains(click_pos):
                self.set_selected_track_id(det.track_id)
                self.tracking_id_selected.emit(det.track_id)
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """处理鼠标移动，实时更新工位框选预览。"""
        if self.is_drawing_seat and self._is_dragging_rect:
            self._drag_current_pos = event.position()
            self.update()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """处理鼠标释放，完成工位框选并转换物理分辨率坐标。"""
        if self.is_drawing_seat and self._is_dragging_rect:
            self._is_dragging_rect = False
            self._drag_current_pos = event.position()
            render_rect = self._get_render_rect()

            if self.current_frame and self.current_frame.width() > 0 and render_rect.isValid():
                scale = render_rect.width() / self.current_frame.width()
                ox, oy = render_rect.x(), render_rect.y()

                p1 = self._drag_start_pos
                p2 = self._drag_current_pos
                rx = min(p1.x(), p2.x())
                ry = min(p1.y(), p2.y())
                rw = abs(p1.x() - p2.x())
                rh = abs(p1.y() - p2.y())

                fx1 = int(round((rx - ox) / scale))
                fy1 = int(round((ry - oy) / scale))
                fx2 = int(round((rx + rw - ox) / scale))
                fy2 = int(round((ry + rh - oy) / scale))

                img_w = self.current_frame.width()
                img_h = self.current_frame.height()
                fx1 = max(0, min(img_w - 1, fx1))
                fy1 = max(0, min(img_h - 1, fy1))
                fx2 = max(0, min(img_w - 1, fx2))
                fy2 = max(0, min(img_h - 1, fy2))

                if abs(fx2 - fx1) >= 20 and abs(fy2 - fy1) >= 20:
                    self.seat_zone_drawn.emit(min(fx1, fx2), min(fy1, fy2), max(fx1, fx2), max(fy1, fy2))

            self.set_drawing_seat_mode(False)
            self.update()
            return

        super().mouseReleaseEvent(event)
