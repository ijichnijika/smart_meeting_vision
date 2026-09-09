import os
import sys
import importlib.util
import pytest
import numpy as np

os.environ["QT_QPA_PLATFORM"] = "offscreen"

# 确保当前目录位于 sys.path 前列
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from signal_thread import BeltMonitorWidget, MainWindow as ThreadAppWindow
from main import MainWindow as MainAppWindow, BeltConfigDialog

def load_signal_app():
    spec = importlib.util.spec_from_file_location("local_signal", os.path.join(current_dir, "signal.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.MainWindow

SignalAppWindow = load_signal_app()

from PySide6.QtWidgets import QApplication, QLabel, QLineEdit


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_main_window_menus_toolbars_and_real_monitors(qapp):
    win = MainAppWindow()

    # 1. 验证菜单
    menubar = win.menuBar()
    actions = menubar.actions()
    menu_titles = [a.text() for a in actions]
    assert "文件" in menu_titles
    assert "监控窗口" in menu_titles
    assert "系统配置" in menu_titles
    assert "帮助" in menu_titles

    # 2. 验证皮带专属配置菜单项
    assert win.cfg_belt1_action.text() == "皮带1配置"
    assert win.cfg_belt2_action.text() == "皮带2配置"
    assert win.cfg_belt3_action.text() == "皮带3配置"
    assert win.cfg_alarm_action.text() == "报警阈值配置"
    assert win.cfg_camera_action.text() == "摄像头通讯配置"

    # 3. 验证工具条
    toolbars = win.findChildren(type(win.tool_monitor))
    tb_names = [tb.objectName() for tb in toolbars]
    assert "MonitorToolBar" in tb_names
    assert "ConfigToolBar" in tb_names
    assert "WindowToolBar" in tb_names

    # 4. 验证真实监控窗口挂载（非文本占位）
    win._toggle_monitor("皮带1", True, win.belt1_action)
    assert "皮带1" in win.sub_windows
    sub = win.sub_windows["皮带1"]
    monitor = sub.widget()
    assert isinstance(monitor, BeltMonitorWidget)
    assert isinstance(monitor.label_img, QLabel)
    assert isinstance(monitor.edit_distance, QLineEdit)
    assert isinstance(monitor.edit_degree, QLineEdit)

    # 模拟接收视频与数据流
    dummy_frame = np.zeros((240, 320, 3), dtype=np.uint8)
    monitor.refresh_frame(dummy_frame, 2.15, 1.34)
    assert "2.15" in monitor.edit_distance.text()
    assert "1.34" in monitor.edit_degree.text()

    # 5. 关闭监控窗口与资源回收
    win._toggle_monitor("皮带1", False, win.belt1_action)
    assert "皮带1" not in win.sub_windows

    win.close()


def test_signal_thread_five_widgets_and_layout(qapp):
    win = ThreadAppWindow()

    assert isinstance(win.label_img, QLabel)
    assert isinstance(win.label_distance_tip, QLabel)
    assert isinstance(win.edit_distance, QLineEdit)
    assert isinstance(win.label_degree_tip, QLabel)
    assert isinstance(win.edit_degree, QLineEdit)

    assert win.edit_distance.isReadOnly()
    assert win.edit_degree.isReadOnly()

    dummy_frame = np.zeros((240, 320, 3), dtype=np.uint8)
    win.refreshFrame(dummy_frame, 3.456, 1.789)

    assert "3.46" in win.edit_distance.text()
    assert "1.79" in win.edit_degree.text()
    assert not win.label_img.pixmap().isNull()

    win.close()


def test_belt_config_dialog(qapp):
    dlg = BeltConfigDialog("测试参数配置")
    vals = dlg.get_values()
    assert "偏移报警上限 (mm)" in vals
    assert "偏移报警下限 (mm)" in vals
    assert "偏转角度阈值 (°)" in vals
    dlg.close()


def test_signal_basic_window(qapp):
    win = SignalAppWindow()
    assert hasattr(win, "closeSignal")
    win.close()
