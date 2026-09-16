"""
工位区域划定与配置管理对话框。
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import DB_PATH
from app.src.model import Attendee, SeatZone
from app.src.service.db_service import clear_seat_zones, delete_seat_zone, save_seat_zones
from app.src.ui.theme import ThemeColors


class SeatZoneDialog(QDialog):
    """工位区域划定与管理中心弹窗。"""

    draw_new_requested = Signal()
    auto_generate_requested = Signal()
    zones_updated = Signal(list)

    def __init__(
        self,
        meeting_id: int,
        attendees: List[Attendee],
        seat_zones: List[SeatZone],
        db_path: Path = DB_PATH,
        parent=None,
    ):
        super().__init__(parent)
        self.meeting_id = int(meeting_id)
        self.attendees = list(attendees)
        self.seat_zones = [
            SeatZone(
                id=z.id,
                meeting_id=z.meeting_id,
                seat_index=z.seat_index,
                x1=z.x1,
                y1=z.y1,
                x2=z.x2,
                y2=z.y2,
                assigned_attendee_id=z.assigned_attendee_id,
                assigned_attendee_name=z.assigned_attendee_name,
                assigned_employee_id=z.assigned_employee_id,
                current_status=z.current_status,
            )
            for z in seat_zones
        ]
        self.db_path = db_path

        self.setWindowTitle("工位区域划定与配置管理")
        self.resize(780, 480)
        self._setup_ui()
        self._load_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # 顶栏标题
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_title = QLabel("工位区域划定与管理")
        lbl_title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {ThemeColors.TEXT_PRIMARY};")
        title_col.addWidget(lbl_title)

        lbl_desc = QLabel("划定物理工位几何范围并指派就座人员，实时进行在席与离席防抖检测")
        lbl_desc.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        title_col.addWidget(lbl_desc)
        top_bar.addLayout(title_col)

        top_bar.addStretch()

        self.btn_draw = QPushButton("＋ 画面框选新工位")
        self.btn_draw.setProperty("class", "btn-primary")
        self.btn_draw.setCursor(Qt.PointingHandCursor)
        self.btn_draw.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY_ACCENT};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #1D4ED8;
            }}
        """)
        self.btn_draw.clicked.connect(self._on_draw_clicked)
        top_bar.addWidget(self.btn_draw)

        self.btn_auto = QPushButton("智能识别生成工位")
        self.btn_auto.setCursor(Qt.PointingHandCursor)
        self.btn_auto.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {ThemeColors.TEXT_PRIMARY};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {ThemeColors.PRIMARY_ACCENT};
                color: {ThemeColors.PRIMARY_ACCENT};
            }}
        """)
        self.btn_auto.clicked.connect(self._on_auto_clicked)
        top_bar.addWidget(self.btn_auto)

        layout.addLayout(top_bar)

        # 工位表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["工位编号", "几何坐标 (X1, Y1, X2, Y2)", "绑定参会人员", "当前在席状态", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # 底栏操作按钮
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        self.lbl_summary = QLabel()
        self.lbl_summary.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px;")
        bottom_bar.addWidget(self.lbl_summary)

        bottom_bar.addStretch()

        btn_clear = QPushButton("清空所有工位")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setStyleSheet(f"""
            QPushButton {{
                background-color: #FEE2E2;
                color: #DC2626;
                border: 1px solid #FCA5A5;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #FECACA;
            }}
        """)
        btn_clear.clicked.connect(self._on_clear_clicked)
        bottom_bar.addWidget(btn_clear)

        btn_save = QPushButton("保存工位配置")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY_ACCENT};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #1D4ED8;
            }}
        """)
        btn_save.clicked.connect(self._on_save_clicked)
        bottom_bar.addWidget(btn_save)

        btn_close = QPushButton("关闭")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {ThemeColors.TEXT_MUTED};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
            }}
        """)
        btn_close.clicked.connect(self.accept)
        bottom_bar.addWidget(btn_close)

        layout.addLayout(bottom_bar)

    def _load_table(self):
        """刷新工位列表数据展示。"""
        self.table.setRowCount(0)
        self.seat_zones.sort(key=lambda z: z.seat_index)
        self.table.setRowCount(len(self.seat_zones))

        for row_idx, zone in enumerate(self.seat_zones):
            # 1. 工位编号
            item_idx = QTableWidgetItem(f"工位 #{zone.seat_index}")
            item_idx.setTextAlignment(Qt.AlignCenter)
            item_idx.setFlags(item_idx.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 0, item_idx)

            # 2. 几何坐标
            coord_str = f"[{zone.x1}, {zone.y1}] → [{zone.x2}, {zone.y2}]  ({zone.x2 - zone.x1} × {zone.y2 - zone.y1})"
            item_coord = QTableWidgetItem(coord_str)
            item_coord.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            item_coord.setFlags(item_coord.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 1, item_coord)

            # 3. 绑定参会人选择下拉框
            combo_att = QComboBox()
            combo_att.addItem("未绑定人员", "")
            selected_idx = 0
            for idx, a in enumerate(self.attendees):
                combo_att.addItem(f"{a.name} ({a.department})", a.id)
                if (zone.assigned_employee_id and zone.assigned_employee_id == a.id) or (
                    zone.assigned_attendee_name and zone.assigned_attendee_name == a.name
                ):
                    selected_idx = idx + 1
            combo_att.setCurrentIndex(selected_idx)
            combo_att.currentIndexChanged.connect(
                lambda c_idx, z=zone, cb=combo_att: self._on_attendee_changed(z, cb)
            )
            self.table.setCellWidget(row_idx, 2, combo_att)

            # 4. 当前状态
            if zone.current_status == "occupied":
                status_text = "在席"
                status_color = "#10B981"
            elif zone.current_status == "absent":
                status_text = "离席告警"
                status_color = "#EF4444"
            else:
                status_text = "空置"
                status_color = "#64748B"

            item_status = QTableWidgetItem(status_text)
            item_status.setTextAlignment(Qt.AlignCenter)
            item_status.setForeground(Qt.GlobalColor(Qt.white) if False else Qt.black)
            item_status.setFlags(item_status.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 3, item_status)

            # 5. 操作按钮
            btn_del = QPushButton("删除")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet("""
                QPushButton {
                    color: #EF4444;
                    background: transparent;
                    border: none;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 2px 8px;
                }
                QPushButton:hover {
                    background-color: #FEE2E2;
                    border-radius: 4px;
                }
            """)
            btn_del.clicked.connect(lambda _, z=zone: self._on_delete_zone(z))
            self.table.setCellWidget(row_idx, 4, btn_del)

        self.lbl_summary.setText(f"当前共划定 {len(self.seat_zones)} 个工位区域")

    def _on_attendee_changed(self, zone: SeatZone, combo: QComboBox):
        """处理工位人员关联绑定变更。"""
        att_id = combo.currentData()
        if not att_id:
            zone.assigned_attendee_id = None
            zone.assigned_attendee_name = None
            zone.assigned_employee_id = None
        else:
            att = next((a for a in self.attendees if a.id == att_id), None)
            if att:
                zone.assigned_employee_id = att.id
                zone.assigned_attendee_name = att.name

    def _on_delete_zone(self, zone: SeatZone):
        """删除指定工位。"""
        if zone in self.seat_zones:
            self.seat_zones.remove(zone)
            if zone.id:
                delete_seat_zone(int(zone.id), self.db_path)
            # 重新编号
            for idx, z in enumerate(self.seat_zones):
                z.seat_index = idx + 1
            self._load_table()
            self.zones_updated.emit(self.seat_zones)

    def _on_clear_clicked(self):
        """清空当前会议的所有工位。"""
        reply = QMessageBox.question(
            self,
            "确认清空工位",
            "确定要清空当前会议的所有已划定工位吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.seat_zones.clear()
            clear_seat_zones(self.meeting_id, self.db_path)
            self._load_table()
            self.zones_updated.emit(self.seat_zones)

    def _on_draw_clicked(self):
        """触发在主画面中框选新工位。"""
        self.draw_new_requested.emit()
        self.accept()

    def _on_auto_clicked(self):
        """触发根据画面就座人员自动生成工位。"""
        self.auto_generate_requested.emit()
        self.accept()

    def _on_save_clicked(self):
        """持久化保存工位配置至 SQLite。"""
        saved = save_seat_zones(self.meeting_id, self.seat_zones, self.db_path)
        self.seat_zones = saved
        self._load_table()
        self.zones_updated.emit(self.seat_zones)
        QMessageBox.information(self, "保存成功", f"已成功保存 {len(self.seat_zones)} 个工位区域配置！")
