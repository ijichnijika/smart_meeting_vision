import os
import time
import ast
import yaml
import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QFileDialog,
    QMessageBox,
    QGroupBox,
)

from zimage_label import ZImageLabel, DrawShape


class MyMonitorSetupDialog(QDialog):
    def __init__(self, beltID: int, cfgfile: str = './conf/config.yaml', parent=None):
        super().__init__(parent)
        self.beltID = beltID
        self.beltID_str = f'belt_{beltID}'
        self.cfgfile = cfgfile
        self.cfg = {}
        self.snapshot_file = None
        self.pixmap = None

        self.setWindowTitle(f'系统配置 - 皮带 {self.beltID}')
        self.resize(1000, 680)

        self._init_ui()
        self._load_config()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()
        self.label_snapshot = ZImageLabel(self)
        self.label_snapshot.setMinimumSize(640, 480)
        self.label_snapshot.setStyleSheet('border: 1px solid #444; background-color: #111;')
        left_layout.addWidget(self.label_snapshot, 1)

        tool_layout = QHBoxLayout()
        self.radioButton_left = QRadioButton('绘制左边界', self)
        self.radioButton_right = QRadioButton('绘制右边界', self)
        self.radioButton_left.setChecked(True)

        self.btn_group = QButtonGroup(self)
        self.btn_group.addButton(self.radioButton_left)
        self.btn_group.addButton(self.radioButton_right)

        self.pushButton_clear = QPushButton('清除边界', self)
        self.pushButton_snapshot = QPushButton('抓取快照', self)
        self.pushButton_opensnapshot = QPushButton('打开快照', self)

        tool_layout.addWidget(self.radioButton_left)
        tool_layout.addWidget(self.radioButton_right)
        tool_layout.addWidget(self.pushButton_clear)
        tool_layout.addWidget(self.pushButton_snapshot)
        tool_layout.addWidget(self.pushButton_opensnapshot)
        tool_layout.addStretch()
        left_layout.addLayout(tool_layout)

        main_layout.addLayout(left_layout, 7)

        right_box = QGroupBox('参数配置', self)
        form_layout = QFormLayout(right_box)

        self.lineEdit_url = QLineEdit(self)
        self.lineEdit_leftborder = QLineEdit(self)
        self.lineEdit_rightborder = QLineEdit(self)
        self.lineEdit_beltwidth = QLineEdit(self)
        self.lineEdit_angle = QLineEdit(self)
        self.lineEdit_dist = QLineEdit(self)

        form_layout.addRow(QLabel('视频源/RTSP:'), self.lineEdit_url)
        form_layout.addRow(QLabel('左边界坐标:'), self.lineEdit_leftborder)
        form_layout.addRow(QLabel('右边界坐标:'), self.lineEdit_rightborder)
        form_layout.addRow(QLabel('皮带宽度(mm):'), self.lineEdit_beltwidth)
        form_layout.addRow(QLabel('角度告警阈值(°):'), self.lineEdit_angle)
        form_layout.addRow(QLabel('距离告警阈值(mm):'), self.lineEdit_dist)

        btn_box = QHBoxLayout()
        self.pushButton_save = QPushButton('保存配置', self)
        self.pushButton_cancel = QPushButton('取消', self)
        btn_box.addWidget(self.pushButton_save)
        btn_box.addWidget(self.pushButton_cancel)

        right_panel = QVBoxLayout()
        right_panel.addWidget(right_box)
        right_panel.addStretch()
        right_panel.addLayout(btn_box)

        main_layout.addLayout(right_panel, 3)

        self.radioButton_left.toggled.connect(self.setShape)
        self.radioButton_right.toggled.connect(self.setShape)
        self.label_snapshot.borderDrew.connect(self.borderDrew)
        self.label_snapshot.clearBorder.connect(self.clearBorder)
        self.pushButton_clear.clicked.connect(self.clearBorder)
        self.pushButton_snapshot.clicked.connect(self.getSnapshot)
        self.pushButton_opensnapshot.clicked.connect(self.openSnapshot)
        self.pushButton_save.clicked.connect(self.saveConfig)
        self.pushButton_cancel.clicked.connect(self.reject)

    def _load_config(self):
        if not os.path.exists(self.cfgfile):
            return

        with open(self.cfgfile, 'r', encoding='utf-8') as f:
            self.cfg = yaml.safe_load(f) or {}

        belt_data = self.cfg.get(self.beltID_str, {})
        if not belt_data:
            return

        self.lineEdit_url.setText(str(belt_data.get('url', '')))
        self.lineEdit_beltwidth.setText(str(belt_data.get('belt_width', 180)))
        self.lineEdit_angle.setText(str(belt_data.get('angle_alarm', 5.0)))
        self.lineEdit_dist.setText(str(belt_data.get('dist_alarm', 5.0)))

        border_l = belt_data.get('border_left')
        border_r = belt_data.get('border_right')

        if border_l:
            self.lineEdit_leftborder.setText(str(border_l))
            self.label_snapshot.setLeftBorder(border_l)

        if border_r:
            self.lineEdit_rightborder.setText(str(border_r))
            self.label_snapshot.setRightBorder(border_r)

        snapshot_path = belt_data.get('snapshot')
        if snapshot_path and os.path.exists(snapshot_path):
            self.snapshot_file = snapshot_path
            self.pixmap = QPixmap(snapshot_path)
            if not self.pixmap.isNull():
                self.label_snapshot.setPixmapT(self.pixmap)

    def setShape(self):
        if self.radioButton_left.isChecked():
            self.label_snapshot.setShape(DrawShape.LEFT_BORDER)
        elif self.radioButton_right.isChecked():
            self.label_snapshot.setShape(DrawShape.RIGHT_BORDER)

    def borderDrew(self, leftorright: bool, coord: list):
        if leftorright:
            self.lineEdit_leftborder.setText(str(coord))
        else:
            self.lineEdit_rightborder.setText(str(coord))

    def clearBorder(self):
        self.lineEdit_leftborder.setText('')
        self.lineEdit_rightborder.setText('')
        self.label_snapshot.setLeftBorder(None)
        self.label_snapshot.setRightBorder(None)

    def getSnapshot(self):
        url_text = self.lineEdit_url.text().strip()
        video_source = int(url_text) if url_text.isdigit() else url_text

        cap = cv2.VideoCapture(video_source)
        if not cap.isOpened():
            QMessageBox.warning(self, '错误', f'无法连接视频源: {video_source}')
            return

        success, frame = cap.read()
        cap.release()

        if not success or frame is None:
            QMessageBox.warning(self, '错误', '读取视频帧失败')
            return

        os.makedirs('./snapshot', exist_ok=True)
        timestamp_ms = int(time.time() * 1000)
        save_path = f'./snapshot/{self.beltID_str}_{timestamp_ms}.jpg'
        cv2.imwrite(save_path, frame)

        self.snapshot_file = save_path
        self.pixmap = QPixmap(save_path)
        self.label_snapshot.setPixmapT(self.pixmap)
        QMessageBox.information(self, '成功', f'快照抓取并保存至: {save_path}')

    def openSnapshot(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, '打开快照文件', './snapshot', 'Image Files (*.jpg *.png *.jpeg *.bmp)'
        )
        if file_path:
            self.snapshot_file = file_path
            self.pixmap = QPixmap(file_path)
            if not self.pixmap.isNull():
                self.label_snapshot.setPixmapT(self.pixmap)

    def saveConfig(self):
        if self.beltID_str not in self.cfg:
            self.cfg[self.beltID_str] = {}

        belt_dict = self.cfg[self.beltID_str]

        url_str = self.lineEdit_url.text().strip()
        belt_dict['url'] = int(url_str) if url_str.isdigit() else url_str

        if self.snapshot_file:
            belt_dict['snapshot'] = self.snapshot_file

        if self.pixmap and not self.pixmap.isNull():
            belt_dict['size'] = {
                'width': int(self.pixmap.width()),
                'height': int(self.pixmap.height()),
            }

        try:
            belt_dict['belt_width'] = int(float(self.lineEdit_beltwidth.text() or 180))
            belt_dict['angle_alarm'] = float(self.lineEdit_angle.text() or 5.0)
            belt_dict['dist_alarm'] = float(self.lineEdit_dist.text() or 5.0)
        except ValueError as err:
            QMessageBox.warning(self, '格式错误', f'请输入合法数值: {err}')
            return

        l_str = self.lineEdit_leftborder.text().strip()
        r_str = self.lineEdit_rightborder.text().strip()

        try:
            if l_str:
                belt_dict['border_left'] = ast.literal_eval(l_str)
            if r_str:
                belt_dict['border_right'] = ast.literal_eval(r_str)
        except Exception as err:
            QMessageBox.warning(self, '边界格式错误', f'坐标格式解析失败: {err}')
            return

        os.makedirs(os.path.dirname(os.path.abspath(self.cfgfile)), exist_ok=True)
        with open(self.cfgfile, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self.cfg, f, allow_unicode=True)

        self.accept()
