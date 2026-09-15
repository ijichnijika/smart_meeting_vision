from enum import Enum
from typing import List, Optional
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QPainter, QPen, QColor, QPixmap
from PySide6.QtWidgets import QLabel


class Status(Enum):
    DRAW_BEGIN = 1
    DRAW_MOVE = 2
    DRAW_DONE = 3


class DrawShape(Enum):
    LEFT_BORDER = 0
    RIGHT_BORDER = 1


class ZImageLabel(QLabel):
    borderDrew = Signal(bool, list)
    clearBorder = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.status: Optional[Status] = None
        self.shape = DrawShape.LEFT_BORDER

        self._pixmap: Optional[QPixmap] = None
        self._pic: Optional[QPixmap] = None

        self._x_begin = 0
        self._y_begin = 0
        self._mx = 0
        self._my = 0

        self.left_border_img: Optional[List[List[int]]] = None
        self.right_border_img: Optional[List[List[int]]] = None

        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def setPixmapT(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self._update_scaled_pixmap()
        self.update()

    def setShape(self, shape: DrawShape):
        self.shape = shape

    def setLeftBorder(self, coords: Optional[List[List[int]]]):
        self.left_border_img = coords
        self.update()

    def setRightBorder(self, coords: Optional[List[List[int]]]):
        self.right_border_img = coords
        self.update()

    def getLeftBorder(self) -> Optional[List[List[int]]]:
        return self.left_border_img

    def getRightBorder(self) -> Optional[List[List[int]]]:
        return self.right_border_img

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self):
        if self._pixmap is not None and not self._pixmap.isNull():
            self._pic = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            super().setPixmap(self._pic)

    def _get_draw_offsets(self):
        if self._pic is None or self._pic.isNull():
            return 0, 0, self.width(), self.height()
        ox = (self.width() - self._pic.width()) // 2
        oy = (self.height() - self._pic.height()) // 2
        return ox, oy, self._pic.width(), self._pic.height()

    def _widget_to_image(self, wx: int, wy: int) -> QPoint:
        if self._pixmap is None or self._pic is None or self._pixmap.isNull() or self._pic.isNull():
            return QPoint(wx, wy)

        ox, oy, dw, dh = self._get_draw_offsets()
        clamped_x = max(ox, min(wx, ox + dw))
        clamped_y = max(oy, min(wy, oy + dh))

        ratio_x = self._pixmap.width() / float(dw) if dw > 0 else 1.0
        ratio_y = self._pixmap.height() / float(dh) if dh > 0 else 1.0

        ix = int((clamped_x - ox) * ratio_x)
        iy = int((clamped_y - oy) * ratio_y)
        return QPoint(ix, iy)

    def _image_to_widget(self, ix: int, iy: int) -> QPoint:
        if self._pixmap is None or self._pic is None or self._pixmap.isNull() or self._pic.isNull():
            return QPoint(ix, iy)

        ox, oy, dw, dh = self._get_draw_offsets()
        ratio_x = float(dw) / self._pixmap.width() if self._pixmap.width() > 0 else 1.0
        ratio_y = float(dh) / self._pixmap.height() if self._pixmap.height() > 0 else 1.0

        wx = int(ox + ix * ratio_x)
        wy = int(oy + iy * ratio_y)
        return QPoint(wx, wy)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._pixmap is not None:
            self.status = Status.DRAW_BEGIN
            self._x_begin = event.pos().x()
            self._y_begin = event.pos().y()
            self._mx = self._x_begin
            self._my = self._y_begin
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.status in (Status.DRAW_BEGIN, Status.DRAW_MOVE):
            self.status = Status.DRAW_MOVE
            self._mx = event.pos().x()
            self._my = event.pos().y()
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.status in (Status.DRAW_BEGIN, Status.DRAW_MOVE):
            self.status = Status.DRAW_DONE
            p_start = self._widget_to_image(self._x_begin, self._y_begin)
            p_end = self._widget_to_image(event.pos().x(), event.pos().y())

            coords = [[p_start.x(), p_start.y()], [p_end.x(), p_end.y()]]
            if self.shape == DrawShape.LEFT_BORDER:
                self.left_border_img = coords
                self.borderDrew.emit(True, coords)
            else:
                self.right_border_img = coords
                self.borderDrew.emit(False, coords)
            self.update()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.status = None
        self.left_border_img = None
        self.right_border_img = None
        self.clearBorder.emit()
        self.update()
        super().mouseDoubleClickEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._pixmap is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.left_border_img and len(self.left_border_img) == 2:
            pen_left = QPen(QColor(0, 255, 0), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen_left)
            p1 = self._image_to_widget(self.left_border_img[0][0], self.left_border_img[0][1])
            p2 = self._image_to_widget(self.left_border_img[1][0], self.left_border_img[1][1])
            painter.drawLine(p1, p2)

        if self.right_border_img and len(self.right_border_img) == 2:
            pen_right = QPen(QColor(255, 0, 0), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen_right)
            p1 = self._image_to_widget(self.right_border_img[0][0], self.right_border_img[0][1])
            p2 = self._image_to_widget(self.right_border_img[1][0], self.right_border_img[1][1])
            painter.drawLine(p1, p2)

        if self.status == Status.DRAW_MOVE:
            active_color = QColor(0, 200, 255) if self.shape == DrawShape.LEFT_BORDER else QColor(255, 140, 0)
            pen_live = QPen(active_color, 2, Qt.PenStyle.DashLine)
            painter.setPen(pen_live)
            painter.drawLine(self._x_begin, self._y_begin, self._mx, self._my)

        painter.end()
