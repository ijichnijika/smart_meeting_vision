"""
顶部导航栏与系统几何标微标组件。
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.config import APP_NAME, APP_SUBTITLE
from app.src.ui.theme import ThemeColors
from app.src.utils.calculate_utils import current_time_str


class BrandLogoWidget(QWidget):
    """系统几何标识微标（矢量绘制智能光圈）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(ThemeColors.PRIMARY_ACCENT)))
        painter.drawRoundedRect(self.rect(), 8, 8)

        cx, cy = self.rect().center().x(), self.rect().center().y()
        lens_pen = QPen(QColor("#FFFFFF"), 1.8)
        painter.setPen(lens_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), 7.0, 7.0)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QPointF(cx, cy), 2.5, 2.5)


class TopNavWidget(QFrame):
    """顶部全局导航栏组件。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topNav")
        self.setFixedHeight(54)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(14)

        layout.addWidget(BrandLogoWidget())

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title_col.setAlignment(Qt.AlignVCenter)

        lbl_title = QLabel(APP_NAME)
        lbl_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {ThemeColors.TEXT_PRIMARY}; letter-spacing: 0.2px;")
        title_col.addWidget(lbl_title)

        lbl_sub = QLabel(APP_SUBTITLE)
        lbl_sub.setStyleSheet(f"font-size: 10px; color: {ThemeColors.TEXT_MUTED};")
        title_col.addWidget(lbl_sub)
        layout.addLayout(title_col)

        layout.addSpacing(16)

        self.venue_pill = QLabel("第一报告厅 · 自由在席感知")
        self.venue_pill.setStyleSheet(f"""
            background-color: {ThemeColors.PANEL_MUTED};
            color: {ThemeColors.TEXT_SECONDARY};
            border: 1px solid {ThemeColors.BORDER_LIGHT};
            border-radius: 12px;
            padding: 3px 10px;
            font-size: 11px;
            font-weight: 500;
        """)
        layout.addWidget(self.venue_pill)

        layout.addStretch()

        self.pill_status = QLabel("自研行为感知引擎 (best.pt) · 实时分析中")
        self.pill_status.setStyleSheet(f"""
            background-color: {ThemeColors.SUCCESS_BG};
            color: {ThemeColors.SUCCESS_TEXT};
            border: 1px solid {ThemeColors.SUCCESS_BORDER};
            border-radius: 12px;
            padding: 4px 14px;
            font-size: 11px;
            font-weight: 600;
        """)
        layout.addWidget(self.pill_status)

        layout.addStretch()

        self.lbl_clock = QLabel(current_time_str("%Y-%m-%d  %H:%M:%S"))
        self.lbl_clock.setStyleSheet(f"""
            color: {ThemeColors.TEXT_SECONDARY};
            font-family: 'SF Pro Text', 'Menlo', monospace;
            font-size: 12px;
            font-weight: 500;
        """)
        layout.addWidget(self.lbl_clock)

    def update_clock(self, text: str):
        """刷新时钟显示文本。"""
        self.lbl_clock.setText(text)
