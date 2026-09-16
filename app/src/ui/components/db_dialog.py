"""
内嵌 SQLite 数据库查看器弹窗。
对应 D1/D2/D3 数据存储的可视化浏览与核验。
"""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.config import DB_PATH
from app.resource.db import get_connection
from app.src.ui.theme import ThemeColors


class DatabaseViewerDialog(QDialog):
    """内嵌数据表查看与管理对话框。"""

    TABLES = [
        ("meetings", "会议信息表 (meetings)"),
        ("attendees", "参会人员表 (attendees)"),
        ("check_in_records", "考勤签到明细表 (check_in_records)"),
        ("distraction_events", "分心违规事件表 (distraction_events)"),
        ("seat_zones", "工位配置表 (seat_zones)"),
    ]

    def __init__(self, db_path: Path = DB_PATH, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.setWindowTitle("数据库管理中心")
        self.resize(900, 560)
        self._setup_ui()
        self._load_table_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        header_col = QVBoxLayout()
        header_col.setSpacing(2)
        title_lbl = QLabel("数据库管理中心")
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {ThemeColors.TEXT_PRIMARY};")
        header_col.addWidget(title_lbl)

        sub_lbl = QLabel("本地 SQLite 持久化数据查询与核验 · 支持实时检索")
        sub_lbl.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        header_col.addWidget(sub_lbl)
        header_layout.addLayout(header_col)

        header_layout.addStretch()

        db_badge = QLabel(f"数据源: {self.db_path.name}")
        db_badge.setStyleSheet(f"""
            color: {ThemeColors.TEXT_SECONDARY};
            background-color: {ThemeColors.WINDOW_BG};
            border: 1px solid {ThemeColors.BORDER_LIGHT};
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 11px;
            font-family: 'SF Pro Text', 'Menlo', monospace;
        """)
        header_layout.addWidget(db_badge)
        layout.addLayout(header_layout)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {ThemeColors.BORDER_LIGHT}; border: none;")
        layout.addWidget(sep)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        lbl_select = QLabel("数据表:")
        lbl_select.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {ThemeColors.TEXT_SECONDARY};")
        toolbar.addWidget(lbl_select)

        self.combo_tables = QComboBox()
        self.combo_tables.setMinimumWidth(260)
        for tbl_name, tbl_label in self.TABLES:
            self.combo_tables.addItem(tbl_label, tbl_name)
        self.combo_tables.currentIndexChanged.connect(lambda _: self._load_table_data())
        toolbar.addWidget(self.combo_tables)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("过滤当前表格内容...")
        self.search_input.textChanged.connect(self._apply_search_filter)
        toolbar.addWidget(self.search_input, stretch=1)

        self.lbl_count = QLabel("共 0 条记录")
        self.lbl_count.setStyleSheet(f"""
            color: {ThemeColors.TEXT_MUTED};
            background-color: {ThemeColors.WINDOW_BG};
            border: 1px solid {ThemeColors.BORDER_LIGHT};
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 11px;
        """)
        toolbar.addWidget(self.lbl_count)

        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.setProperty("class", "btn-secondary")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setFixedWidth(64)
        self.btn_refresh.clicked.connect(self._load_table_data)
        toolbar.addWidget(self.btn_refresh)

        layout.addLayout(toolbar)

        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.verticalHeader().setDefaultSectionSize(32)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setStyleSheet(f"""
            QTableWidget {{
                background-color: #FFFFFF;
                alternate-background-color: {ThemeColors.WINDOW_BG};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
                gridline-color: {ThemeColors.BORDER_LIGHT};
                selection-background-color: {ThemeColors.PRIMARY_LIGHT};
                selection-color: {ThemeColors.PRIMARY};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: {ThemeColors.PANEL_MUTED};
                color: {ThemeColors.TEXT_PRIMARY};
                font-weight: 600;
                font-size: 12px;
                padding: 8px 10px;
                border: none;
                border-right: 1px solid {ThemeColors.BORDER_LIGHT};
                border-bottom: 1px solid {ThemeColors.BORDER_LIGHT};
            }}
        """)
        layout.addWidget(self.table_widget, stretch=1)

        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        path_text = f"存储路径: {self.db_path}"
        lbl_path = QLabel(path_text)
        lbl_path.setStyleSheet(f"font-size: 10px; color: {ThemeColors.TEXT_PLACEHOLDER}; font-family: 'SF Pro Text', 'Menlo', monospace;")
        bottom_bar.addWidget(lbl_path, stretch=1)

        self.btn_close = QPushButton("关闭")
        self.btn_close.setProperty("class", "btn-secondary")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setFixedWidth(72)
        self.btn_close.clicked.connect(self.accept)
        bottom_bar.addWidget(self.btn_close)

        layout.addLayout(bottom_bar)

    def _load_table_data(self):
        """从 SQLite 中查询当前选中的数据表并填充 UI 表格。"""
        table_name = self.combo_tables.currentData()
        if not table_name or not self.db_path.exists():
            return

        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            col_names = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

        self.table_widget.clear()
        self.table_widget.setColumnCount(len(col_names))
        self.table_widget.setHorizontalHeaderLabels(col_names)
        self.table_widget.setRowCount(len(rows))

        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                text = "" if val is None else str(val)
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table_widget.setItem(r_idx, c_idx, item)

        self.search_input.clear()
        self.lbl_count.setText(f"共 {len(rows)} 条记录")

    def _apply_search_filter(self, query: str):
        """根据输入的关键词动态隐藏不匹配的数据行。"""
        query = query.strip().lower()
        row_count = self.table_widget.rowCount()
        col_count = self.table_widget.columnCount()

        visible_count = 0
        for r in range(row_count):
            if not query:
                self.table_widget.setRowHidden(r, False)
                visible_count += 1
                continue

            row_matched = False
            for c in range(col_count):
                item = self.table_widget.item(r, c)
                if item and query in item.text().lower():
                    row_matched = True
                    break

            self.table_widget.setRowHidden(r, not row_matched)
            if row_matched:
                visible_count += 1

        if query:
            self.lbl_count.setText(f"匹配 {visible_count} / {row_count} 条")
        else:
            self.lbl_count.setText(f"共 {row_count} 条记录")

