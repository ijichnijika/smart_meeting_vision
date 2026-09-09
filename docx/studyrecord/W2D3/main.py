import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMdiArea,
    QMdiSubWindow,
    QMessageBox,
    QVBoxLayout,
)

from signal_thread import BeltMonitorWidget


class BeltConfigDialog(QDialog):
    def __init__(self, title="参数配置", config_dict=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(360, 220)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.inputs = {}
        defaults = config_dict or {
            "偏移报警上限 (mm)": "2.5",
            "偏移报警下限 (mm)": "-2.5",
            "偏转角度阈值 (°)": "3.0",
            "视频流接入地址": "./video/test.mp4",
        }

        for label_text, default_val in defaults.items():
            edit = QLineEdit(str(default_val), self)
            form_layout.addRow(QLabel(label_text), edit)
            self.inputs[label_text] = edit

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self):
        return {k: v.text() for k, v in self.inputs.items()}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("皮带监控系统")
        self.resize(1180, 800)

        self.mdi = QMdiArea()
        self.mdi.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdi.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setCentralWidget(self.mdi)

        self.sub_windows = {}
        self.monitor_widgets = {}

        self.belt_configs = {
            "皮带1": {"video": "./video/test.mp4", "base_dist": 1.2, "base_deg": 1.8},
            "皮带2": {"video": "./video/test.mp4", "base_dist": -0.9, "base_deg": -1.4},
            "皮带3": {"video": "./video/test.mp4", "base_dist": 2.1, "base_deg": 2.6},
        }

        self._init_actions()
        self._init_menus()
        self._init_toolbars()
        self._init_statusbar()

    def _init_actions(self):
        self.exit_action = QAction("退出(&Q)", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.setStatusTip("退出监控系统")
        self.exit_action.triggered.connect(self.close)

        icon_belt1 = QIcon("./icons/camera_belt1.png") if os.path.exists("./icons/camera_belt1.png") else QIcon()
        self.belt1_action = QAction(icon_belt1, "皮带1", self, checkable=True)
        self.belt1_action.setToolTip("打开/关闭皮带1摄像头监控")
        self.belt1_action.setStatusTip("皮带1视频流")
        self.belt1_action.triggered.connect(lambda state: self._toggle_monitor("皮带1", state, self.belt1_action))

        icon_belt2 = QIcon("./icons/camera_belt2.png") if os.path.exists("./icons/camera_belt2.png") else QIcon()
        self.belt2_action = QAction(icon_belt2, "皮带2", self, checkable=True)
        self.belt2_action.setToolTip("打开/关闭皮带2摄像头监控")
        self.belt2_action.setStatusTip("皮带2视频流")
        self.belt2_action.triggered.connect(lambda state: self._toggle_monitor("皮带2", state, self.belt2_action))

        icon_belt3 = QIcon("./icons/camera_belt3.png") if os.path.exists("./icons/camera_belt3.png") else QIcon()
        self.belt3_action = QAction(icon_belt3, "皮带3", self, checkable=True)
        self.belt3_action.setToolTip("打开/关闭皮带3摄像头监控")
        self.belt3_action.setStatusTip("皮带3视频流")
        self.belt3_action.triggered.connect(lambda state: self._toggle_monitor("皮带3", state, self.belt3_action))

        self.tile_action = QAction("平铺窗口(&T)", self)
        self.tile_action.setStatusTip("平铺子窗口")
        self.tile_action.triggered.connect(self.mdi.tileSubWindows)

        self.cascade_action = QAction("层叠窗口(&C)", self)
        self.cascade_action.setStatusTip("层叠子窗口")
        self.cascade_action.triggered.connect(self.mdi.cascadeSubWindows)

        self.cfg_belt1_action = QAction("皮带1配置", self)
        self.cfg_belt1_action.setStatusTip("配置皮带1参数")
        self.cfg_belt1_action.triggered.connect(lambda: self._open_config_dialog("皮带1配置"))

        self.cfg_belt2_action = QAction("皮带2配置", self)
        self.cfg_belt2_action.setStatusTip("配置皮带2参数")
        self.cfg_belt2_action.triggered.connect(lambda: self._open_config_dialog("皮带2配置"))

        self.cfg_belt3_action = QAction("皮带3配置", self)
        self.cfg_belt3_action.setStatusTip("配置皮带3参数")
        self.cfg_belt3_action.triggered.connect(lambda: self._open_config_dialog("皮带3配置"))

        self.cfg_alarm_action = QAction("报警阈值配置", self)
        self.cfg_alarm_action.setStatusTip("配置报警阈值")
        self.cfg_alarm_action.triggered.connect(lambda: self._open_config_dialog("报警阈值配置"))

        self.cfg_camera_action = QAction("摄像头通讯配置", self)
        self.cfg_camera_action.setStatusTip("配置摄像头参数")
        self.cfg_camera_action.triggered.connect(lambda: self._open_config_dialog("摄像头通讯配置"))

        self.about_action = QAction("关于(&A)", self)
        self.about_action.setStatusTip("查看关于信息")
        self.about_action.triggered.connect(self._show_about_dialog)

    def _init_menus(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("文件")
        file_menu.addAction(self.exit_action)

        monitor_menu = menu_bar.addMenu("监控窗口")
        monitor_menu.addAction(self.belt1_action)
        monitor_menu.addAction(self.belt2_action)
        monitor_menu.addAction(self.belt3_action)
        monitor_menu.addSeparator()
        monitor_menu.addAction(self.tile_action)
        monitor_menu.addAction(self.cascade_action)

        config_menu = menu_bar.addMenu("系统配置")
        config_menu.addAction(self.cfg_belt1_action)
        config_menu.addAction(self.cfg_belt2_action)
        config_menu.addAction(self.cfg_belt3_action)
        config_menu.addSeparator()
        config_menu.addAction(self.cfg_alarm_action)
        config_menu.addAction(self.cfg_camera_action)

        help_menu = menu_bar.addMenu("帮助")
        help_menu.addAction(self.about_action)

    def _init_toolbars(self):
        self.tool_monitor = self.addToolBar("监控")
        self.tool_monitor.setObjectName("MonitorToolBar")
        self.tool_monitor.addAction(self.belt1_action)
        self.tool_monitor.addAction(self.belt2_action)
        self.tool_monitor.addAction(self.belt3_action)

        self.tool_config = self.addToolBar("配置")
        self.tool_config.setObjectName("ConfigToolBar")
        self.tool_config.addAction(self.cfg_alarm_action)
        self.tool_config.addAction(self.cfg_camera_action)

        self.tool_window = self.addToolBar("视窗")
        self.tool_window.setObjectName("WindowToolBar")
        self.tool_window.addAction(self.tile_action)
        self.tool_window.addAction(self.cascade_action)

    def _init_statusbar(self):
        self.statusBar().showMessage("系统就绪")

    def _toggle_monitor(self, name: str, state: bool, action: QAction):
        if state:
            if name not in self.sub_windows:
                cfg = self.belt_configs.get(name, {"video": "./video/test.mp4", "base_dist": 1.5, "base_deg": 2.0})

                sub = QMdiSubWindow()
                sub.setWindowTitle(f"{name} 实时监控")
                sub.resize(520, 400)

                monitor_widget = BeltMonitorWidget(
                    belt_name=name,
                    video_path=cfg["video"],
                    base_distance=cfg["base_dist"],
                    base_degree=cfg["base_deg"],
                )
                sub.setWidget(monitor_widget)
                sub.destroyed.connect(lambda: self._on_subwindow_closed(name, action))

                self.mdi.addSubWindow(sub)
                self.sub_windows[name] = sub
                self.monitor_widgets[name] = monitor_widget

            self.sub_windows[name].show()
            self.statusBar().showMessage(f"已打开 {name} 监控画面", 3000)
        else:
            if name in self.sub_windows:
                self._stop_and_remove_subwindow(name)
            self.statusBar().showMessage(f"已关闭 {name} 监控画面", 3000)
        action.setChecked(state)

    def _on_subwindow_closed(self, name: str, action: QAction):
        if name in self.monitor_widgets:
            self.monitor_widgets[name].stop()
            del self.monitor_widgets[name]
        if name in self.sub_windows:
            del self.sub_windows[name]
        action.setChecked(False)

    def _stop_and_remove_subwindow(self, name: str):
        if name in self.monitor_widgets:
            self.monitor_widgets[name].stop()
            del self.monitor_widgets[name]
        if name in self.sub_windows:
            sub = self.sub_windows[name]
            del self.sub_windows[name]
            sub.close()

    def _open_config_dialog(self, title: str):
        dlg = BeltConfigDialog(title=title, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.statusBar().showMessage(f"{title} 已保存", 3000)

    def _show_about_dialog(self):
        QMessageBox.about(
            self,
            "关于",
            "皮带监控系统\n基于 PySide6 实现",
        )

    def closeEvent(self, event):
        for widget in list(self.monitor_widgets.values()):
            widget.stop()
        self.monitor_widgets.clear()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_window = MainWindow()
    my_window.show()
    sys.exit(app.exec())
