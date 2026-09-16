"""
顶部导航栏与系统几何标微标组件。
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import APP_NAME, APP_SUBTITLE
from app.src.ui.theme import ThemeColors
from app.src.utils.calculate_utils import current_time_str


class BrandLogoWidget(QWidget):
    """系统几何标识微标"""

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

    db_viewer_requested = Signal()
    meeting_manager_requested = Signal()
    seat_zones_requested = Signal()

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

        self.pill_status = QLabel("行为感知分析 (best.pt) · 实时监控中")
        self.pill_status.setStyleSheet(f"""
            background-color: {ThemeColors.SUCCESS_BG};
            color: {ThemeColors.SUCCESS_TEXT};
            border: 1px solid {ThemeColors.SUCCESS_BORDER};
            border-radius: 12px;
            padding: 4px 12px;
            font-size: 11px;
            font-weight: 600;
        """)
        layout.addWidget(self.pill_status)

        self.btn_seat_zones = QPushButton("工位管理")
        self.btn_seat_zones.setCursor(Qt.PointingHandCursor)
        self.btn_seat_zones.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {ThemeColors.TEXT_SECONDARY};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.SURFACE_HOVER};
                border-color: {ThemeColors.PRIMARY_ACCENT};
                color: {ThemeColors.PRIMARY_ACCENT};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.SURFACE_ACTIVE};
            }}
        """)
        self.btn_seat_zones.clicked.connect(lambda: self.seat_zones_requested.emit())
        layout.addWidget(self.btn_seat_zones)

        self.btn_meetings = QPushButton("会议管理")
        self.btn_meetings.setCursor(Qt.PointingHandCursor)
        self.btn_meetings.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {ThemeColors.TEXT_SECONDARY};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.SURFACE_HOVER};
                border-color: {ThemeColors.PRIMARY_ACCENT};
                color: {ThemeColors.PRIMARY_ACCENT};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.SURFACE_ACTIVE};
            }}
        """)
        self.btn_meetings.clicked.connect(lambda: self.meeting_manager_requested.emit())
        layout.addWidget(self.btn_meetings)

        self.btn_db = QPushButton("数据库查看")
        self.btn_db.setCursor(Qt.PointingHandCursor)
        self.btn_db.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {ThemeColors.TEXT_SECONDARY};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.SURFACE_HOVER};
                border-color: {ThemeColors.PRIMARY_ACCENT};
                color: {ThemeColors.PRIMARY_ACCENT};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.SURFACE_ACTIVE};
            }}
        """)
        self.btn_db.clicked.connect(lambda: self.db_viewer_requested.emit())
        layout.addWidget(self.btn_db)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedHeight(18)
        sep.setStyleSheet(f"background-color: {ThemeColors.BORDER_LIGHT}; width: 1px; border: none;")
        layout.addWidget(sep)

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
