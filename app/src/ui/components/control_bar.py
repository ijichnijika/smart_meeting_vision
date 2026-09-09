"""
视频回放与输入源控制条。
"""

import os
from pathlib import Path
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from app.config import DEFAULT_DEMO_VIDEO, DEMO_VIDEOS_DIR
from app.src.ui.theme import ThemeColors


class ControlBar(QFrame):
    """视频回放与输入源控制条组件。"""

    play_toggled = Signal(bool)
    restart_clicked = Signal()
    source_changed = Signal(object)
    snapshot_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_playing = True
        self.setObjectName("controlBar")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        self.btn_play = QPushButton("暂停")
        self.btn_play.setObjectName("btnPrimary")
        self.btn_play.setProperty("class", "btn-primary")
        self.btn_play.setFixedWidth(78)
        self.btn_play.clicked.connect(self._toggle_play)
        layout.addWidget(self.btn_play)

        self.btn_restart = QPushButton("重播")
        self.btn_restart.setProperty("class", "btn-secondary")
        self.btn_restart.setFixedWidth(64)
        self.btn_restart.clicked.connect(lambda: self.restart_clicked.emit())
        layout.addWidget(self.btn_restart)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"background-color: {ThemeColors.BORDER_LIGHT}; width: 1px;")
        layout.addWidget(sep)

        lbl_source = QLabel("输入源:")
        lbl_source.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px; font-weight: 500;")
        layout.addWidget(lbl_source)

        self.combo_source = QComboBox()
        self.combo_source.setMinimumWidth(260)
        self._populate_video_sources()
        self.combo_source.currentIndexChanged.connect(self._on_source_index_changed)
        layout.addWidget(self.combo_source)

        layout.addStretch()

        self.btn_snapshot = QPushButton("画面抓拍")
        self.btn_snapshot.setProperty("class", "btn-secondary")
        self.btn_snapshot.clicked.connect(lambda: self.snapshot_requested.emit())
        layout.addWidget(self.btn_snapshot)

    def _populate_video_sources(self):
        """填充预设演示视频与系统输入源。"""
        if DEFAULT_DEMO_VIDEO.exists():
            self.combo_source.addItem("全景会议流 (推荐演示)", str(DEFAULT_DEMO_VIDEO))

        extra_demos = [
            ("会场监控切片 01", "meeting_surveillance_long_1.mp4"),
            ("企业研讨会切片", "meeting_media_company_clip_14_20.mp4"),
            ("行为分析样本集", "meeting_distraction_demo.mp4"),
        ]
        for label, fname in extra_demos:
            path = DEMO_VIDEOS_DIR / fname
            if path.exists() and path != DEFAULT_DEMO_VIDEO:
                self.combo_source.addItem(label, str(path))

        self.combo_source.addItem("本地摄像头 (设备 0)", 0)
        self.combo_source.addItem("打开本地视频文件...", "BROWSE_FILE")

    def _toggle_play(self):
        """切换播放与暂停状态。"""
        self.set_play_state(not self.is_playing)
        self.play_toggled.emit(self.is_playing)

    def set_play_state(self, is_playing: bool):
        """更新播放按钮状态显示。"""
        self.is_playing = is_playing
        self.btn_play.setText("暂停" if is_playing else "播放")

    def _on_source_index_changed(self, index: int):
        """响应视频源下拉选择变更。"""
        data = self.combo_source.itemData(index)
        if data != "BROWSE_FILE":
            if data is not None:
                self.source_changed.emit(data)
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择本地会议视频", str(DEMO_VIDEOS_DIR), "视频文件 (*.mp4 *.avi *.mov *.mkv)"
        )
        if not file_path or not os.path.exists(file_path):
            self.combo_source.setCurrentIndex(0)
            return

        name = Path(file_path).name
        self.combo_source.insertItem(0, f"本地: {name}", file_path)
        self.combo_source.setCurrentIndex(0)
        self.source_changed.emit(file_path)
