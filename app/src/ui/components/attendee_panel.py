"""
参会人员管理与实名挂载面板。
"""

from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.src.model import AttendanceStatus, Attendee
from app.src.ui.theme import ThemeColors


class AvatarWidget(QWidget):
    """文字首字母头像组件。"""

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.char = name[0] if name else "?"
        idx = abs(hash(name)) % len(ThemeColors.AVATAR_PALETTE)
        self.bg_color_hex, self.text_color_hex = ThemeColors.AVATAR_PALETTE[idx]
        self.setFixedSize(32, 32)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.bg_color_hex)))
        painter.drawRoundedRect(self.rect(), 8, 8)

        painter.setPen(QColor(self.text_color_hex))
        font = QFont("PingFang SC", 11, QFont.DemiBold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, self.char)


class AttendeeCard(QFrame):
    """参会人员信息卡片条目。"""

    clicked = Signal(object)
    bind_clicked = Signal(str)

    def __init__(self, attendee: Attendee, parent=None):
        super().__init__(parent)
        self.attendee = attendee
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("attendeeCard")
        self.setStyleSheet(f"""
            QFrame#attendeeCard {{
                background-color: {ThemeColors.PANEL_BG};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
            }}
            QFrame#attendeeCard:hover {{
                background-color: {ThemeColors.SURFACE_HOVER};
                border-color: {ThemeColors.BORDER_MUTED};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        self.avatar = AvatarWidget(self.attendee.name)
        layout.addWidget(self.avatar)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        info_col.setContentsMargins(0, 0, 0, 0)

        row_name = QHBoxLayout()
        row_name.setSpacing(6)
        lbl_name = QLabel(self.attendee.name)
        lbl_name.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {ThemeColors.TEXT_PRIMARY};")
        row_name.addWidget(lbl_name)

        self.lbl_status = QLabel()
        self._update_status_badge()
        row_name.addWidget(self.lbl_status)

        if self.attendee.distraction_count > 0:
            lbl_dist = QLabel(f"分心 {self.attendee.distraction_count} 次")
            lbl_dist.setStyleSheet(f"""
                color: {ThemeColors.WARNING_TEXT};
                background-color: {ThemeColors.WARNING_BG};
                border: 1px solid {ThemeColors.WARNING_BORDER};
                border-radius: 4px;
                padding: 0px 4px;
                font-size: 9px;
                font-weight: 600;
            """)
            row_name.addWidget(lbl_dist)

        row_name.addStretch()
        info_col.addLayout(row_name)

        lbl_meta = QLabel(f"{self.attendee.department} · {self.attendee.role}")
        lbl_meta.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        info_col.addWidget(lbl_meta)

        layout.addLayout(info_col, stretch=1)

        self.btn_bind = QPushButton()
        self.btn_bind.setCursor(Qt.PointingHandCursor)
        self._update_bind_button()
        self.btn_bind.clicked.connect(lambda: self.bind_clicked.emit(self.attendee.id))
        layout.addWidget(self.btn_bind)

    def _update_status_badge(self):
        """更新在席或离席状态徽标。"""
        is_present = (self.attendee.status == AttendanceStatus.PRESENT.value)
        text = "在席" if is_present else "离席"
        color = ThemeColors.SUCCESS_TEXT if is_present else ThemeColors.DANGER_TEXT
        bg = ThemeColors.SUCCESS_BG if is_present else ThemeColors.DANGER_BG
        border = ThemeColors.SUCCESS_BORDER if is_present else ThemeColors.DANGER_BORDER

        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"""
            color: {color};
            background-color: {bg};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 1px 6px;
            font-size: 10px;
            font-weight: 600;
        """)

    def _update_bind_button(self):
        """更新关联状态或已绑定的追踪标识。"""
        if self.attendee.track_id:
            self.btn_bind.setText(self.attendee.track_id)
            self.btn_bind.setToolTip("已关联目标编号，点击可重新设定")
            self.btn_bind.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeColors.PRIMARY_LIGHT};
                    color: {ThemeColors.PRIMARY};
                    border: 1px solid {ThemeColors.PRIMARY_BORDER};
                    border-radius: 5px;
                    font-weight: 600;
                    font-size: 11px;
                    padding: 3px 8px;
                }}
                QPushButton:hover {{
                    background-color: #DBEAFE;
                    border-color: #93C5FD;
                }}
            """)
        else:
            self.btn_bind.setText("+ 关联")
            self.btn_bind.setToolTip("关联监控画面中的目标跟踪编号")
            self.btn_bind.setStyleSheet(f"""
                QPushButton {{
                    background-color: #FFFFFF;
                    color: {ThemeColors.TEXT_MUTED};
                    border: 1px dashed {ThemeColors.BORDER_MUTED};
                    border-radius: 5px;
                    font-size: 11px;
                    padding: 3px 6px;
                }}
                QPushButton:hover {{
                    background-color: {ThemeColors.SURFACE_HOVER};
                    color: {ThemeColors.PRIMARY_ACCENT};
                    border-style: solid;
                    border-color: {ThemeColors.PRIMARY_ACCENT};
                }}
            """)

    def mousePressEvent(self, event):
        self.clicked.emit(self.attendee)
        super().mousePressEvent(event)


class AttendeePanel(QFrame):
    """参会人员名单展示与检索面板。"""

    attendee_selected = Signal(object)
    bind_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.attendees: List[Attendee] = []
        self.cards: List[AttendeeCard] = []
        self.current_filter: str = "ALL"
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedWidth(290)
        self.setObjectName("attendeePanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        info_box = QFrame()
        info_box.setStyleSheet(f"""
            background-color: {ThemeColors.WINDOW_BG};
            border: 1px solid {ThemeColors.BORDER_LIGHT};
            border-radius: 8px;
            padding: 8px;
        """)
        box_layout = QVBoxLayout(info_box)
        box_layout.setContentsMargins(6, 6, 6, 6)
        box_layout.setSpacing(3)

        lbl_title = QLabel("软件工程项目训练 中期进度评审")
        lbl_title.setStyleSheet(f"font-weight: 700; font-size: 13px; color: {ThemeColors.TEXT_PRIMARY};")
        lbl_title.setWordWrap(True)
        box_layout.addWidget(lbl_title)

        lbl_venue = QLabel("第一报告厅 · 实时感知")
        lbl_venue.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        box_layout.addWidget(lbl_venue)

        layout.addWidget(info_box)

        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(4)

        filters = [
            ("全部", "ALL"),
            ("在席", "PRESENT"),
            ("离席", "ABSENT"),
            ("未关联", "UNBOUND"),
        ]
        for idx, (label, fkey) in enumerate(filters):
            btn = QPushButton(label)
            btn.setProperty("class", "filter-chip")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            if idx == 0:
                btn.setChecked(True)
            self.filter_group.addButton(btn, idx)
            btn.clicked.connect(lambda checked, k=fkey: self._on_filter_changed(k))
            filter_layout.addWidget(btn)

        layout.addLayout(filter_layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索参会人姓名或部门...")
        self.search_input.textChanged.connect(lambda _: self._apply_filters())
        layout.addWidget(self.search_input)

        self.lbl_counts = QLabel("参会人员 (共 0 人 · 0 人在席)")
        self.lbl_counts.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED}; font-weight: 500;")
        layout.addWidget(self.lbl_counts)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.list_layout = QVBoxLayout(self.scroll_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)

        self.lbl_empty = QLabel("未找到匹配的参会人员")
        self.lbl_empty.setAlignment(Qt.AlignCenter)
        self.lbl_empty.setStyleSheet(f"color: {ThemeColors.TEXT_PLACEHOLDER}; font-size: 12px; padding: 24px 0;")
        self.lbl_empty.hide()
        self.list_layout.addWidget(self.lbl_empty)

        self.list_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area, stretch=1)

    def set_attendees(self, attendees: List[Attendee]):
        """加载全量人员列表并构建卡片。"""
        self.attendees = attendees

        for card in self.cards:
            self.list_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()

        for att in attendees:
            card = AttendeeCard(att)
            card.clicked.connect(lambda a=att: self.attendee_selected.emit(a))
            card.bind_clicked.connect(lambda aid: self.bind_requested.emit(aid))
            self.cards.append(card)
            self.list_layout.insertWidget(len(self.cards) - 1, card)

        self._update_counts()
        self._apply_filters()

    def _update_counts(self):
        """更新在席人数统计标签。"""
        total = len(self.attendees)
        present = sum(1 for a in self.attendees if a.status == AttendanceStatus.PRESENT.value)
        self.lbl_counts.setText(f"参会人员 (共 {total} 人 · {present} 人在席)")

    def _on_filter_changed(self, filter_key: str):
        """响应筛选药丸切换。"""
        self.current_filter = filter_key
        self._apply_filters()

    def _apply_filters(self):
        """结合搜索框文本与当前筛选标签综合过滤可见卡片。"""
        query = self.search_input.text().strip().lower()
        matched = 0

        for card in self.cards:
            att = card.attendee
            text_match = (
                not query
                or query in att.name.lower()
                or query in att.department.lower()
            )

            status_match = True
            if self.current_filter == "PRESENT":
                status_match = (att.status == AttendanceStatus.PRESENT.value)
            elif self.current_filter == "ABSENT":
                status_match = (att.status != AttendanceStatus.PRESENT.value)
            elif self.current_filter == "UNBOUND":
                status_match = (not att.track_id)

            is_visible = text_match and status_match
            card.setVisible(is_visible)
            if is_visible:
                matched += 1

        self.lbl_empty.setVisible(matched == 0)

    def _filter_list(self, text: str):
        """按关键字过滤参会人员卡片列表。"""
        self._apply_filters()

    def get_total_count(self) -> int:
        return len(self.cards)

    def get_visible_count(self) -> int:
        return sum(1 for c in self.cards if not c.isHidden())

    def update_attendee_binding(self, attendee_id: str, track_id: str):
        """更新指定人员绑定的目标跟踪标识。"""
        for card in self.cards:
            if card.attendee.id == attendee_id:
                card.attendee.track_id = track_id
                card._update_bind_button()
                break
        self._apply_filters()
