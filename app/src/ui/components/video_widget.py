"""
视频渲染与交互画布组件。
"""

from typing import List, Optional, Tuple
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

from app.src.model import DetectionBox
from app.src.ui.theme import ThemeColors


class VideoWidget(QWidget):
    """视频图像渲染与目标拾取交互组件。"""

    tracking_id_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_frame: Optional[QImage] = None
        self.detections: List[DetectionBox] = []
        self.current_fps: float = 0.0
        self.selected_track_id: Optional[int] = None
        self._render_rect = QRectF()

        self.setMinimumSize(480, 270)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

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

        # 等比例居中缩放
        scale = min(w / img_w, h / img_h)
        draw_w = img_w * scale
        draw_h = img_h * scale
        draw_x = (w - draw_w) / 2.0
        draw_y = (h - draw_h) / 2.0
        self._render_rect = QRectF(draw_x, draw_y, draw_w, draw_h)

        painter.drawImage(self._render_rect, self.current_frame)

        for det in self.detections:
            self._draw_detection_item(painter, det, draw_x, draw_y, scale)

        self._draw_hud(painter)

    def _draw_standby_screen(self, painter: QPainter, rect: QRectF):
        """绘制待机十字光标与等待提示。"""
        cx, cy = rect.center().x(), rect.center().y()

        cross_pen = QPen(QColor(ThemeColors.CANVAS_GRID), 1.5, Qt.SolidLine)
        painter.setPen(cross_pen)
        painter.drawLine(QPointF(cx - 30, cy), QPointF(cx + 30, cy))
        painter.drawLine(QPointF(cx, cy - 30), QPointF(cx, cy + 30))

        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), 18, 18)

        painter.setPen(QColor(ThemeColors.TEXT_MUTED))
        font = QFont("PingFang SC", 12)
        painter.setFont(font)
        text_rect = QRectF(rect.x(), cy + 32, rect.width(), 24)
        painter.drawText(text_rect, Qt.AlignCenter, "等待视频信号接入...")

    def _resolve_det_style(self, det: DetectionBox, is_selected: bool) -> Tuple[QColor, QColor, QColor, str]:
        """计算检测框边框颜色、背景填充色与显示文本。"""
        if det.is_distracted:
            stroke = QColor(ThemeColors.BOX_DISTRACT)
            fill = QColor(220, 38, 38, 28)
            tag_bg = QColor(220, 38, 38, 230)
        elif is_selected:
            stroke = QColor(ThemeColors.BOX_SELECTED)
            fill = QColor(139, 92, 246, 32)
            tag_bg = QColor(139, 92, 246, 230)
        else:
            stroke = QColor(ThemeColors.BOX_PERSON)
            fill = QColor(59, 130, 246, 18)
            tag_bg = QColor(37, 99, 235, 220)

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
        """在画面右上角绘制实时帧率与目标数指示。"""
        hud_text = f"FPS {self.current_fps:.1f}  ·  目标 {len(self.detections)}"
        hud_font = QFont("SF Pro Text", 10, QFont.Medium)
        painter.setFont(hud_font)
        fm = painter.fontMetrics()
        hud_w = fm.horizontalAdvance(hud_text) + 18
        hud_h = fm.height() + 8

        rx = self.width() - hud_w - 12
        ry = 12
        hud_rect = QRectF(rx, ry, hud_w, hud_h)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(15, 23, 42, 200))
        painter.drawRoundedRect(hud_rect, 5, 5)

        painter.setPen(QColor("#F1F5F9"))
        painter.drawText(hud_rect, Qt.AlignCenter, hud_text)

    def mousePressEvent(self, event):
        """响应鼠标点击，拾取光标所在位置的检测目标。"""
        if event.button() != Qt.LeftButton or not self._render_rect.isValid():
            super().mousePressEvent(event)
            return

        if not self.current_frame or self.current_frame.width() <= 0:
            super().mousePressEvent(event)
            return

        click_pos = event.position()
        scale = self._render_rect.width() / self.current_frame.width()
        ox, oy = self._render_rect.x(), self._render_rect.y()

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
