"""
出勤分析与实时告警动态流面板。
"""

from typing import List
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.src.model import AttendanceStats, DistractionAlert
from app.src.ui.theme import ThemeColors


class CircularGaugeWidget(QWidget):
    """环形出勤率仪表组件。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.percentage: float = 0.0
        self.setFixedSize(92, 92)

    def set_percentage(self, pct: float):
        self.percentage = max(0.0, min(100.0, pct))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(7, 7, -7, -7)

        pen_bg = QPen(QColor(ThemeColors.BORDER_LIGHT), 6, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, 0, 360 * 16)

        pen_fg = QPen(QColor(ThemeColors.PRIMARY), 6, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_fg)
        span_angle = int(-self.percentage * 3.6 * 16)
        painter.drawArc(rect, 90 * 16, span_angle)

        center_rect = self.rect()
        font_val = QFont("SF Pro Text", 13, QFont.Bold)
        painter.setFont(font_val)
        painter.setPen(QColor(ThemeColors.TEXT_PRIMARY))

        num_rect = center_rect.adjusted(0, -6, 0, -6)
        painter.drawText(num_rect, Qt.AlignCenter, f"{self.percentage:.1f}%")

        font_sub = QFont("PingFang SC", 9, QFont.Normal)
        painter.setFont(font_sub)
        painter.setPen(QColor(ThemeColors.TEXT_MUTED))
        sub_rect = center_rect.adjusted(0, 14, 0, 14)
        painter.drawText(sub_rect, Qt.AlignCenter, "在席率")


class MetricCard(QFrame):
    """单项指标卡片组件。"""

    def __init__(self, title: str, initial_val: str, val_color_hex: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.WINDOW_BG};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)

        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED}; font-weight: 500;")
        layout.addWidget(self.lbl_title)

        self.lbl_val = QLabel(initial_val)
        self.lbl_val.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {val_color_hex};")
        layout.addWidget(self.lbl_val)

    def set_value(self, text: str):
        self.lbl_val.setText(text)


class AlertCardItem(QFrame):
    """告警流水动态卡片组件。"""

    def __init__(self, alert: DistractionAlert, parent=None):
        super().__init__(parent)
        self.alert = alert
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.WINDOW_BG};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-left: 3px solid {ThemeColors.DANGER};
                border-radius: 6px;
            }}
            QFrame:hover {{
                background-color: {ThemeColors.PANEL_MUTED};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        lbl_type = QLabel(self.alert.event_label)
        lbl_type.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {ThemeColors.DANGER_TEXT};")
        top_row.addWidget(lbl_type)

        top_row.addStretch()

        lbl_time = QLabel(self.alert.timestamp)
        lbl_time.setStyleSheet(f"font-size: 10px; color: {ThemeColors.TEXT_MUTED}; font-family: monospace;")
        top_row.addWidget(lbl_time)
        layout.addLayout(top_row)

        desc = f"目标 {self.alert.track_id} {self.alert.attendee_name} · 持续 {self.alert.duration_seconds} 秒"
        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_SECONDARY};")
        layout.addWidget(lbl_desc)


class StatsPanel(QFrame):
    """出勤看板与实时告警面板。"""

    export_report_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.alert_cards: List[AlertCardItem] = []
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedWidth(330)
        self.setObjectName("statsPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        lbl_header = QLabel("出勤感知看板")
        lbl_header.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {ThemeColors.TEXT_PRIMARY};")
        layout.addWidget(lbl_header)

        kpi_card = QFrame()
        kpi_card.setStyleSheet(f"""
            background-color: {ThemeColors.WINDOW_BG};
            border: 1px solid {ThemeColors.BORDER_LIGHT};
            border-radius: 10px;
        """)
        kpi_layout = QHBoxLayout(kpi_card)
        kpi_layout.setContentsMargins(12, 12, 12, 12)
        kpi_layout.setSpacing(10)

        numbers_col = QVBoxLayout()
        numbers_col.setSpacing(3)

        lbl_pres_title = QLabel("当前在席情况")
        lbl_pres_title.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED}; font-weight: 500;")
        numbers_col.addWidget(lbl_pres_title)

        self.lbl_present_val = QLabel("0 / 0")
        self.lbl_present_val.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {ThemeColors.TEXT_PRIMARY};")
        numbers_col.addWidget(self.lbl_present_val)

        self.lbl_rate_val = QLabel("出勤率 0.0%")
        self.lbl_rate_val.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {ThemeColors.SUCCESS_TEXT};")
        numbers_col.addWidget(self.lbl_rate_val)

        kpi_layout.addLayout(numbers_col)
        kpi_layout.addStretch()

        self.gauge_widget = CircularGaugeWidget()
        kpi_layout.addWidget(self.gauge_widget)
        layout.addWidget(kpi_card)

        row_metrics = QHBoxLayout()
        row_metrics.setSpacing(8)

        self.card_present = MetricCard("在席人数", "0 人", ThemeColors.SUCCESS)
        self.card_absent = MetricCard("离席人数", "0 人", ThemeColors.DANGER)
        self.card_distract = MetricCard("分心告警", "0 次", ThemeColors.WARNING)

        row_metrics.addWidget(self.card_present)
        row_metrics.addWidget(self.card_absent)
        row_metrics.addWidget(self.card_distract)
        layout.addLayout(row_metrics)

        lbl_feed_title = QLabel("实时感知流水")
        lbl_feed_title.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ThemeColors.TEXT_PRIMARY};")
        layout.addWidget(lbl_feed_title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.feed_layout = QVBoxLayout(self.scroll_widget)
        self.feed_layout.setContentsMargins(0, 0, 0, 0)
        self.feed_layout.setSpacing(6)

        self.lbl_empty_feed = QLabel("全场秩序良好，暂无分心告警")
        self.lbl_empty_feed.setAlignment(Qt.AlignCenter)
        self.lbl_empty_feed.setStyleSheet(f"color: {ThemeColors.TEXT_PLACEHOLDER}; font-size: 12px; padding: 24px 0;")
        self.feed_layout.addWidget(self.lbl_empty_feed)

        self.feed_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area, stretch=1)

        self.btn_export = QPushButton("导出考勤分析表 (.xlsx)")
        self.btn_export.setObjectName("btnPrimary")
        self.btn_export.setProperty("class", "btn-primary")
        self.btn_export.setFixedHeight(36)
        self.btn_export.clicked.connect(lambda: self.export_report_requested.emit())
        layout.addWidget(self.btn_export)

    def update_stats(self, stats: AttendanceStats):
        """更新出勤率数值与各子项指标。"""
        self.lbl_present_val.setText(f"{stats.current_present} / {stats.total_expected}")
        self.lbl_rate_val.setText(f"出勤率 {stats.attendance_rate:.1f}%")
        self.gauge_widget.set_percentage(stats.attendance_rate)

        self.card_present.set_value(f"{stats.current_present} 人")
        self.card_absent.set_value(f"{stats.current_absent} 人")
        self.card_distract.set_value(f"{stats.distraction_total} 次")

    def add_alert(self, alert: DistractionAlert):
        """向动态流水列表添加告警卡片。"""
        if self.lbl_empty_feed.isVisible():
            self.lbl_empty_feed.hide()

        card = AlertCardItem(alert)
        self.alert_cards.insert(0, card)
        self.feed_layout.insertWidget(0, card)
        card.show()

    def get_alert_count(self) -> int:
        """获取当前告警卡片数量。"""
        return len(self.alert_cards)
