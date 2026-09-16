"""
会议信息管理与编辑弹窗组件。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import DB_PATH
from app.src.model.models import MeetingInfo
from app.src.service.db_service import (
    delete_meeting,
    get_active_meeting,
    get_all_meetings,
    save_meeting,
)
from app.src.ui.theme import ThemeColors


class MeetingEditDialog(QDialog):
    """会议创建与编辑对话框。"""

    def __init__(self, meeting: Optional[MeetingInfo] = None, db_path: Path = DB_PATH, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.is_create = meeting is None or getattr(meeting, "id", 0) == 0

        if self.is_create:
            now = datetime.now()
            start_str = now.strftime("%Y-%m-%d %H:00:00")
            end_str = (now + timedelta(hours=2)).strftime("%Y-%m-%d %H:00:00")
            self.meeting = MeetingInfo(
                id=0,
                title="",
                department="研发中心",
                host_name="",
                start_time=start_str,
                end_time=end_str,
                expected_count=0,
                status="in_progress",
                room="第一报告厅",
            )
        else:
            self.meeting = meeting

        self.setWindowTitle("新建会议" if self.is_create else "编辑会议信息")
        self.setFixedWidth(520)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)

        header_col = QVBoxLayout()
        header_col.setSpacing(3)

        title_text = "新建会议档案" if self.is_create else "编辑会议基本信息"
        header_lbl = QLabel(title_text)
        header_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {ThemeColors.TEXT_PRIMARY};")
        header_col.addWidget(header_lbl)

        sub_lbl = QLabel("配置会场主题、主办部门、主持人与预定起止时间等参数")
        sub_lbl.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        header_col.addWidget(sub_lbl)
        layout.addLayout(header_col)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {ThemeColors.BORDER_LIGHT}; border: none;")
        layout.addWidget(sep)

        form_card = QFrame()
        form_card.setObjectName("formCard")
        form_card.setStyleSheet(f"""
            QFrame#formCard {{
                background-color: {ThemeColors.WINDOW_BG};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
            }}
            QLineEdit, QComboBox {{
                background-color: #FFFFFF;
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 12px;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1px solid {ThemeColors.PRIMARY_ACCENT};
            }}
        """)
        card_layout = QVBoxLayout(form_card)
        card_layout.setContentsMargins(14, 14, 14, 14)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(0, 0, 0, 0)

        self.input_title = QLineEdit(self.meeting.title)
        self.input_title.setFixedHeight(32)
        self.input_title.setPlaceholderText("请输入会议主题名称 (必填)")
        form_layout.addRow(self._create_label("会议主题:"), self.input_title)

        self.input_dept = QLineEdit(self.meeting.department)
        self.input_dept.setFixedHeight(32)
        self.input_dept.setPlaceholderText("例如: 研发中心")
        form_layout.addRow(self._create_label("主办部门:"), self.input_dept)

        self.input_host = QLineEdit(self.meeting.host_name)
        self.input_host.setFixedHeight(32)
        self.input_host.setPlaceholderText("例如: 夏一帆")
        form_layout.addRow(self._create_label("主持人:"), self.input_host)

        self.input_room = QLineEdit(getattr(self.meeting, "room", "第一报告厅"))
        self.input_room.setFixedHeight(32)
        self.input_room.setPlaceholderText("例如: 第一报告厅")
        form_layout.addRow(self._create_label("会议场地:"), self.input_room)

        self.input_start = QLineEdit(str(self.meeting.start_time))
        self.input_start.setFixedHeight(32)
        self.input_start.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        form_layout.addRow(self._create_label("开始时间:"), self.input_start)

        self.input_end = QLineEdit(str(self.meeting.end_time))
        self.input_end.setFixedHeight(32)
        self.input_end.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        form_layout.addRow(self._create_label("结束时间:"), self.input_end)

        self.input_count = QLineEdit(str(self.meeting.expected_count))
        self.input_count.setFixedHeight(32)
        self.input_count.setPlaceholderText("预计参会总人数")
        form_layout.addRow(self._create_label("预期人数:"), self.input_count)

        self.combo_status = QComboBox()
        self.combo_status.setFixedHeight(32)
        self.combo_status.addItem("进行中 (in_progress)", "in_progress")
        self.combo_status.addItem("已排期 (scheduled)", "scheduled")
        self.combo_status.addItem("已归档 (completed)", "completed")
        self.combo_status.addItem("实时活跃 (active)", "active")

        current_val = self.meeting.status
        for i in range(self.combo_status.count()):
            if self.combo_status.itemData(i) == current_val:
                self.combo_status.setCurrentIndex(i)
                break
        form_layout.addRow(self._create_label("会议状态:"), self.combo_status)

        card_layout.addLayout(form_layout)
        layout.addWidget(form_card)

        self.lbl_tip = QLabel()
        self.lbl_tip.setStyleSheet(f"font-size: 11px; color: {ThemeColors.DANGER_TEXT};")
        self.lbl_tip.hide()
        layout.addWidget(self.lbl_tip)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setProperty("class", "btn-secondary")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFixedWidth(80)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        save_btn_text = "创建会议" if self.is_create else "保存配置"
        self.btn_save = QPushButton(save_btn_text)
        self.btn_save.setObjectName("btnPrimary")
        self.btn_save.setProperty("class", "btn-primary")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setFixedWidth(90)
        self.btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def _create_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"""
            QLabel {{
                font-weight: 600;
                font-size: 12px;
                color: {ThemeColors.TEXT_SECONDARY};
                background: transparent;
                border: none;
            }}
        """)
        return lbl

    def _on_save(self):
        """保存会议属性变更至内存与数据库。"""
        title = self.input_title.text().strip()
        if not title:
            self.lbl_tip.setText("提示: 会议主题名称不能为空")
            self.lbl_tip.show()
            self.input_title.setFocus()
            return

        dept = self.input_dept.text().strip() or self.meeting.department
        host = self.input_host.text().strip() or self.meeting.host_name
        room = self.input_room.text().strip() or getattr(self.meeting, "room", "第一报告厅")
        start = self.input_start.text().strip() or self.meeting.start_time
        end = self.input_end.text().strip() or self.meeting.end_time

        try:
            count = int(self.input_count.text().strip())
        except ValueError:
            count = self.meeting.expected_count

        status_val = self.combo_status.currentData() or self.meeting.status

        self.meeting.title = title
        self.meeting.department = dept
        self.meeting.host_name = host
        self.meeting.room = room
        self.meeting.start_time = start
        self.meeting.end_time = end
        self.meeting.expected_count = count
        self.meeting.status = status_val

        self.meeting = save_meeting(self.meeting, self.db_path)
        self.accept()


class MeetingManagerDialog(QDialog):
    """会议管理中心。"""

    meeting_switched = Signal(object)
    meeting_updated = Signal(object)

    def __init__(self, current_meeting_id: int, db_path: Path = DB_PATH, parent=None):
        super().__init__(parent)
        self.current_meeting_id = int(current_meeting_id)
        self.db_path = db_path
        self.all_meetings: List[MeetingInfo] = []

        self.setWindowTitle("会议管理中心")
        self.resize(920, 520)
        self.setMinimumWidth(880)
        self._setup_ui()
        self.load_meetings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_title = QLabel("会议管理中心")
        lbl_title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {ThemeColors.TEXT_PRIMARY};")
        title_col.addWidget(lbl_title)

        lbl_desc = QLabel("支持会议维护、会场切换与关联人员名单管理")
        lbl_desc.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        title_col.addWidget(lbl_desc)
        top_bar.addLayout(title_col)

        top_bar.addStretch()

        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {ThemeColors.TEXT_SECONDARY};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.SURFACE_HOVER};
                border-color: {ThemeColors.PRIMARY_ACCENT};
                color: {ThemeColors.PRIMARY_ACCENT};
            }}
        """)
        self.btn_refresh.clicked.connect(self.load_meetings)
        top_bar.addWidget(self.btn_refresh)

        self.btn_create = QPushButton("+ 新建会议")
        self.btn_create.setCursor(Qt.PointingHandCursor)
        self.btn_create.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 5px 14px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.PRIMARY_HOVER};
            }}
        """)
        self.btn_create.clicked.connect(self._on_create_meeting)
        top_bar.addWidget(self.btn_create)

        layout.addLayout(top_bar)

        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入会议主题、主办部门或主持人过滤搜索...")
        self.search_input.setFixedHeight(30)
        self.search_input.textChanged.connect(self._filter_table)
        filter_bar.addWidget(self.search_input, stretch=1)

        self.lbl_count = QLabel("共 0 场会议")
        self.lbl_count.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED}; font-weight: 500;")
        filter_bar.addWidget(self.lbl_count)

        layout.addLayout(filter_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "会议主题",
            "主办部门",
            "主持人",
            "预定起止时间",
            "应到人数",
            "状态",
            "操作",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(7, 220)

        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #FFFFFF;
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                gridline-color: {ThemeColors.BORDER_LIGHT};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: {ThemeColors.WINDOW_BG};
                color: {ThemeColors.TEXT_SECONDARY};
                font-weight: 600;
                font-size: 11px;
                border: none;
                border-bottom: 1px solid {ThemeColors.BORDER_LIGHT};
                padding: 6px 8px;
            }}
            QTableWidget::item {{
                padding: 6px 8px;
                border-bottom: 1px solid {ThemeColors.BORDER_LIGHT};
            }}
            QTableWidget::item:selected {{
                background-color: {ThemeColors.PRIMARY_LIGHT};
                color: {ThemeColors.PRIMARY};
            }}
        """)
        layout.addWidget(self.table, stretch=1)

        bottom_bar = QHBoxLayout()
        hint_lbl = QLabel("提示：点击【设为当前】可即时切换主屏幕分析会场；点击【删除】将级联移除相关考勤记录。")
        hint_lbl.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_PLACEHOLDER};")
        bottom_bar.addWidget(hint_lbl)
        bottom_bar.addStretch()

        self.btn_close = QPushButton("关闭")
        self.btn_close.setProperty("class", "btn-secondary")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setFixedWidth(80)
        self.btn_close.clicked.connect(self.accept)
        bottom_bar.addWidget(self.btn_close)

        layout.addLayout(bottom_bar)

    def load_meetings(self):
        """从 SQLite 数据库载入所有会议列表。"""
        self.all_meetings = get_all_meetings(self.db_path)
        self._populate_table(self.all_meetings)

    def _populate_table(self, meetings: List[MeetingInfo]):
        """渲染会议列表至表格。"""
        self.table.setRowCount(len(meetings))
        self.lbl_count.setText(f"共 {len(meetings)} 场会议")

        for row_idx, m in enumerate(meetings):
            item_id = QTableWidgetItem(str(m.id))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 0, item_id)

            item_title = QTableWidgetItem(m.title)
            if int(m.id) == self.current_meeting_id:
                item_title.setText(f"★ {m.title}")
            self.table.setItem(row_idx, 1, item_title)

            self.table.setItem(row_idx, 2, QTableWidgetItem(m.department))
            self.table.setItem(row_idx, 3, QTableWidgetItem(m.host_name))

            start_str = str(m.start_time).split()[-1][:5] if m.start_time else ""
            end_str = str(m.end_time).split()[-1][:5] if m.end_time else ""
            time_display = f"{start_str} ~ {end_str}" if start_str else str(m.start_time)
            item_time = QTableWidgetItem(time_display)
            item_time.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 4, item_time)

            item_count = QTableWidgetItem(f"{m.expected_count} 人")
            item_count.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 5, item_count)

            status_text = "进行中" if m.status in ("in_progress", "active") else ("已排期" if m.status == "scheduled" else "已归档")
            item_status = QTableWidgetItem(status_text)
            item_status.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 6, item_status)

            actions_widget = QWidget()
            actions_widget.setStyleSheet("background: transparent;")
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(6, 4, 6, 4)
            actions_layout.setSpacing(6)
            actions_layout.setAlignment(Qt.AlignCenter)

            is_active = (int(m.id) == self.current_meeting_id)
            btn_switch = QPushButton("当前会场" if is_active else "设为当前")
            btn_switch.setCursor(Qt.PointingHandCursor if not is_active else Qt.ArrowCursor)
            btn_switch.setEnabled(not is_active)
            btn_switch.setFixedSize(68, 26)
            btn_switch.setStyleSheet(f"""
                QPushButton {{
                    background-color: {"#E2E8F0" if is_active else "#EFF6FF"};
                    color: {"#64748B" if is_active else ThemeColors.PRIMARY};
                    border: 1px solid {"#CBD5E1" if is_active else ThemeColors.PRIMARY_BORDER};
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 0px;
                }}
                QPushButton:hover:enabled {{
                    background-color: #DBEAFE;
                }}
            """)
            btn_switch.clicked.connect(lambda _, meeting=m: self._on_switch_meeting(meeting))
            actions_layout.addWidget(btn_switch)

            btn_edit = QPushButton("编辑")
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setFixedSize(46, 26)
            btn_edit.setStyleSheet(f"""
                QPushButton {{
                    background-color: #FFFFFF;
                    color: {ThemeColors.TEXT_SECONDARY};
                    border: 1px solid {ThemeColors.BORDER_LIGHT};
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {ThemeColors.SURFACE_HOVER};
                    border-color: {ThemeColors.PRIMARY_ACCENT};
                    color: {ThemeColors.PRIMARY_ACCENT};
                }}
            """)
            btn_edit.clicked.connect(lambda _, meeting=m: self._on_edit_meeting(meeting))
            actions_layout.addWidget(btn_edit)

            btn_del = QPushButton("删除")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setFixedSize(46, 26)
            btn_del.setStyleSheet(f"""
                QPushButton {{
                    background-color: #FFFFFF;
                    color: {ThemeColors.DANGER_TEXT};
                    border: 1px solid {ThemeColors.BORDER_LIGHT};
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: #FEF2F2;
                    border-color: #FCA5A5;
                }}
            """)
            btn_del.clicked.connect(lambda _, meeting=m: self._on_delete_meeting(meeting))
            actions_layout.addWidget(btn_del)

            self.table.setCellWidget(row_idx, 7, actions_widget)

    def _filter_table(self, query: str):
        """根据关键词实时过滤表格行。"""
        q = query.strip().lower()
        if not q:
            for r in range(self.table.rowCount()):
                self.table.setRowHidden(r, False)
            self.lbl_count.setText(f"共 {len(self.all_meetings)} 场会议")
            return

        visible_count = 0
        for r in range(self.table.rowCount()):
            match = False
            for col in (1, 2, 3):
                item = self.table.item(r, col)
                if item and q in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(r, not match)
            if match:
                visible_count += 1

        self.lbl_count.setText(f"匹配 {visible_count} / {len(self.all_meetings)} 场会议")

    def _on_create_meeting(self):
        """新建会议。"""
        dialog = MeetingEditDialog(meeting=None, db_path=self.db_path, parent=self)
        if dialog.exec():
            new_meeting = dialog.meeting
            self.load_meetings()
            self._on_switch_meeting(new_meeting)

    def _on_edit_meeting(self, meeting: MeetingInfo):
        """编辑会议。"""
        dialog = MeetingEditDialog(meeting=meeting, db_path=self.db_path, parent=self)
        if dialog.exec():
            self.load_meetings()
            if int(meeting.id) == self.current_meeting_id:
                self.meeting_updated.emit(meeting)

    def _on_delete_meeting(self, meeting: MeetingInfo):
        """删除会议并级联清理考勤数据。"""
        reply = QMessageBox.question(
            self,
            "确认删除会议",
            f"确定要删除会议【{meeting.title}】(ID: {meeting.id}) 吗？\n\n注意：删除后该会议关联的参会名单与考勤记录将被级联彻底清理。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        delete_meeting(int(meeting.id), self.db_path)
        self.load_meetings()

        if int(meeting.id) == self.current_meeting_id:
            active_m = get_active_meeting(self.db_path)
            self.current_meeting_id = int(active_m.id)
            self.meeting_switched.emit(active_m)
            self._populate_table(self.all_meetings)

    def _on_switch_meeting(self, meeting: MeetingInfo):
        """将指定会议设为当前主屏幕活跃会场。"""
        self.current_meeting_id = int(meeting.id)
        self._populate_table(self.all_meetings)
        self.meeting_switched.emit(meeting)


