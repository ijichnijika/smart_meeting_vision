import os
import sys
import xml.etree.ElementTree as ET
import pytest
import numpy as np

os.environ["QT_QPA_PLATFORM"] = "offscreen"

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PySide6.QtWidgets import QApplication, QLabel, QLCDNumber, QPushButton
from signal_thread import MyBeltMonitorForm, MyBeltProcess
from signal_thread_truck import MyTruckMonitorForm
from alg import calculate_angle, get_border, mid_line, calculate_dist


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_ui_xml_structure():
    xml_dir = os.path.join(current_dir, "xml")
    ui_files = [
        "BeltMonitor.ui",
        "AnguiMonitor.ui",
        "TruckMonitor.ui",
        "FmatterMonitor.ui",
        "SmokeMonitor.ui",
    ]

    for ui_name in ui_files:
        ui_path = os.path.join(xml_dir, ui_name)
        assert os.path.exists(ui_path), f"UI file {ui_name} not found in {xml_dir}"

        tree = ET.parse(ui_path)
        root = tree.getroot()
        assert root.tag == "ui"
        assert root.attrib.get("version") == "4.0"

        widget_names = [w.attrib.get("name") for w in root.iter("widget")]
        assert "label_img" in widget_names
        assert "pushButton_open_video" in widget_names
        assert "pushButton_snapshot" in widget_names
        assert "pushButton_save_video" in widget_names

    belt_tree = ET.parse(os.path.join(xml_dir, "BeltMonitor.ui"))
    belt_names = [w.attrib.get("name") for w in belt_tree.getroot().iter("widget")]
    assert "lcdNumber_angle" in belt_names
    assert "lcdNumber_distance" in belt_names

    angui_tree = ET.parse(os.path.join(xml_dir, "AnguiMonitor.ui"))
    angui_names = [w.attrib.get("name") for w in angui_tree.getroot().iter("widget")]
    assert "lcdNumber_helmet" in angui_names
    assert "lcdNumber_no_helmet" in angui_names

    truck_tree = ET.parse(os.path.join(xml_dir, "TruckMonitor.ui"))
    truck_names = [w.attrib.get("name") for w in truck_tree.getroot().iter("widget")]
    assert "lcdNumber_crane" in truck_names
    assert "lcdNumber_tower_crane" in truck_names

    fmatter_tree = ET.parse(os.path.join(xml_dir, "FmatterMonitor.ui"))
    fmatter_names = [w.attrib.get("name") for w in fmatter_tree.getroot().iter("widget")]
    assert "lcdNumber_nest" in fmatter_names
    assert "lcdNumber_kite" in fmatter_names
    assert "lcdNumber_plastic" in fmatter_names
    assert "lcdNumber_balloon" in fmatter_names

    smoke_tree = ET.parse(os.path.join(xml_dir, "SmokeMonitor.ui"))
    smoke_names = [w.attrib.get("name") for w in smoke_tree.getroot().iter("widget")]
    assert "lcdNumber_smoke" in smoke_names
    assert "lcdNumber_fire" in smoke_names


def test_compiled_py_modules():
    try:
        from docx.studyrecord.W3D1.ui import BeltMonitor, AnguiMonitor, TruckMonitor, FmatterMonitor, SmokeMonitor
    except (ModuleNotFoundError, ImportError):
        try:
            from ui import BeltMonitor, AnguiMonitor, TruckMonitor, FmatterMonitor, SmokeMonitor
        except (ModuleNotFoundError, ImportError):
            import BeltMonitor, AnguiMonitor, TruckMonitor, FmatterMonitor, SmokeMonitor

    assert hasattr(BeltMonitor, "Ui_BeltMonitorForm")
    assert hasattr(AnguiMonitor, "Ui_AnguiMonitorForm")
    assert hasattr(TruckMonitor, "Ui_TruckMonitorForm")
    assert hasattr(FmatterMonitor, "Ui_FmatterMonitorForm")
    assert hasattr(SmokeMonitor, "Ui_SmokeMonitorForm")


def test_alg_calculate_angle():
    line_h1 = ((0, 0), (10, 0))
    line_h2 = ((2, 5), (12, 5))
    assert calculate_angle(line_h1, line_h2) == pytest.approx(0.0, abs=1e-3)

    line_v = ((0, 0), (0, 10))
    assert calculate_angle(line_h1, line_v) == pytest.approx(90.0, abs=1e-3)

    line_diag = ((0, 0), (10, 10))
    assert calculate_angle(line_h1, line_diag) == pytest.approx(45.0, abs=1e-3)

    line_zero = ((5, 5), (5, 5))
    assert calculate_angle(line_h1, line_zero) == 0.0


def test_alg_get_border():
    keypts = np.array([[[570, 447]], [[309, 1074]], [[1179, 1074]], [[939, 447]]])
    p_l0, p_l1 = (580, 422), (342, 967)
    p_r0, p_r1 = (929, 438), (1152, 1009)

    left_border, right_border = get_border(keypts, p_l0, p_l1, p_r0, p_r1, min_length=200)
    assert left_border == ((570, 447), (309, 1074))
    assert right_border == ((1179, 1074), (939, 447))

    empty_left, empty_right = get_border(np.array([]), p_l0, p_l1, p_r0, p_r1)
    assert empty_left is None
    assert empty_right is None


def test_alg_mid_line_and_calculate_dist():
    p_l0, p_l1 = (580, 422), (342, 967)
    p_r0, p_r1 = (929, 438), (1152, 1009)
    r_l = ((570, 447), (309, 1074))
    r_r = ((1179, 1074), (939, 447))

    org_mid = mid_line((p_l0, p_l1), (p_r0, p_r1))
    reco_mid = mid_line(r_l, r_r)

    assert org_mid is not None
    assert reco_mid is not None
    assert len(org_mid) == 2
    assert len(reco_mid) == 2

    deg = calculate_angle(org_mid, reco_mid)
    assert isinstance(deg, float)
    assert 0.0 <= deg <= 90.0

    dist = calculate_dist(org_mid, reco_mid, (p_l0, p_l1), (p_r0, p_r1), belt_width=200)
    assert isinstance(dist, float)
    assert dist >= 0.0


def test_belt_monitor_form(qapp):
    win = MyBeltMonitorForm(belt_name="测试皮带", video_path="")
    assert isinstance(win.label_img, QLabel)
    assert isinstance(win.lcdNumber_angle, QLCDNumber)
    assert isinstance(win.lcdNumber_distance, QLCDNumber)
    assert isinstance(win.pushButton_open_video, QPushButton)
    assert isinstance(win.pushButton_snapshot, QPushButton)
    assert isinstance(win.pushButton_save_video, QPushButton)

    dummy_frame = np.zeros((240, 320, 3), dtype=np.uint8)
    win.refresh_frame(dummy_frame, distance=2.45, degree=1.82)

    assert win.lcdNumber_distance.value() == 2.45
    assert win.lcdNumber_angle.value() == 1.82
    assert "偏转超限告警" in win.label_tip.text()

    win.startWriteVideo()
    assert win.is_recording is True
    assert win.pushButton_save_video.text() == "停止录制"
    win.startWriteVideo()
    assert win.is_recording is False
    assert win.pushButton_save_video.text() == "保存视频"

    win.stop()
    win.close()


def test_truck_monitor_form(qapp):
    win = MyTruckMonitorForm(monitor_name="测试工程车", video_path="")
    assert isinstance(win.label_img, QLabel)
    assert isinstance(win.lcdNumber_crane, QLCDNumber)
    assert isinstance(win.lcdNumber_tower_crane, QLCDNumber)
    assert isinstance(win.pushButton_open_video, QPushButton)
    assert isinstance(win.pushButton_snapshot, QPushButton)
    assert isinstance(win.pushButton_save_video, QPushButton)

    dummy_frame = np.zeros((240, 320, 3), dtype=np.uint8)
    win.refresh_frame(dummy_frame, crane_count=3, tower_crane_count=2)

    assert win.lcdNumber_crane.value() == 3
    assert win.lcdNumber_tower_crane.value() == 2
    assert "施工机械共 5 台" in win.label_tip.text()

    win.startWriteVideo()
    assert win.is_recording is True
    assert win.pushButton_save_video.text() == "停止录制"
    win.startWriteVideo()
    assert win.is_recording is False

    win.stop()
    win.close()


def test_belt_process_yolo_inference():
    process = MyBeltProcess(video_path="", model_path="W2D1/models/best.pt")
    assert hasattr(process, "done_signal")
    assert process.model is not None or not os.path.exists(process.model_path)
