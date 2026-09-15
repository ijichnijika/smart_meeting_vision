import os
import sys
import time
import pytest
import yaml
import numpy as np
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QApplication

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from zimage_label import ZImageLabel, Status, DrawShape
from monitor_setup_dialog import MyMonitorSetupDialog
from belt_monitor import (
    VideoSourceType,
    parse_video_source_type,
    VideoEncodeProcess,
    AlarmSenderThread,
    MyBeltProcess,
    MyBeltMonitorForm,
)
from main import MainWindow, setup_logger

os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_yaml_config_structure():
    cfg_path = os.path.join(current_dir, "conf", "config.yaml")
    assert os.path.exists(cfg_path), "config.yaml must exist"

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    for belt_name in ["belt_0", "belt_1", "belt_2"]:
        assert belt_name in cfg, f"{belt_name} must be defined in config.yaml"
        b = cfg[belt_name]
        assert "url" in b
        assert "belt_width" in b and isinstance(b["belt_width"], (int, float))
        assert "angle_alarm" in b and isinstance(b["angle_alarm"], (int, float))
        assert "dist_alarm" in b and isinstance(b["dist_alarm"], (int, float))
        assert "border_left" in b and len(b["border_left"]) == 2
        assert "border_right" in b and len(b["border_right"]) == 2


def test_zimage_label_state_and_coordinates(qapp):
    label = ZImageLabel()
    pix = QPixmap(640, 480)
    pix.fill(Qt.GlobalColor.black)
    label.setPixmapT(pix)
    label.resize(640, 480)

    label.setShape(DrawShape.LEFT_BORDER)
    assert label.shape == DrawShape.LEFT_BORDER

    label.setShape(DrawShape.RIGHT_BORDER)
    assert label.shape == DrawShape.RIGHT_BORDER

    coords = [[100, 200], [300, 400]]
    label.setLeftBorder(coords)
    assert label.getLeftBorder() == coords

    label.setRightBorder(coords)
    assert label.getRightBorder() == coords

    mapped_pt = label._widget_to_image(100, 100)
    assert isinstance(mapped_pt, QPoint)


def test_monitor_setup_dialog(qapp):
    cfg_path = os.path.join(current_dir, "conf", "config.yaml")
    dialog = MyMonitorSetupDialog(0, cfgfile=cfg_path)

    assert dialog.beltID == 0
    assert dialog.lineEdit_url.text() != ""
    assert dialog.lineEdit_beltwidth.text() != ""
    assert float(dialog.lineEdit_angle.text()) > 0
    assert float(dialog.lineEdit_dist.text()) > 0

    dialog.borderDrew(True, [[10, 20], [30, 40]])
    assert dialog.lineEdit_leftborder.text() == "[[10, 20], [30, 40]]"

    dialog.borderDrew(False, [[50, 60], [70, 80]])
    assert dialog.lineEdit_rightborder.text() == "[[50, 60], [70, 80]]"

    dialog.clearBorder()
    assert dialog.lineEdit_leftborder.text() == ""
    assert dialog.lineEdit_rightborder.text() == ""
    dialog.close()


def test_video_source_parsing():
    assert parse_video_source_type(0) == VideoSourceType.USB
    assert parse_video_source_type("1") == VideoSourceType.USB
    assert parse_video_source_type("rtsp://admin:pass@192.168.1.100/stream") == VideoSourceType.RTSP
    assert parse_video_source_type("http://live.camera.com/test") == VideoSourceType.RTSP
    assert parse_video_source_type("./video/test.mp4") == VideoSourceType.FILE
    assert parse_video_source_type("/tmp/clip.avi") == VideoSourceType.FILE


def test_video_encode_process_queue(qapp):
    class MockWriter:
        def __init__(self):
            self.frames = []
            self.released = False

        def write(self, frame):
            self.frames.append(frame)

        def release(self):
            self.released = True

    mock_writer = MockWriter()
    encoder = VideoEncodeProcess(mock_writer)
    encoder.start()

    dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    encoder.put(dummy_frame)
    encoder.put(dummy_frame)

    time.sleep(0.05)
    encoder.stop()

    assert mock_writer.released is True
    assert len(mock_writer.frames) >= 1


def test_alarm_sender_thread_queue(qapp):
    sender = AlarmSenderThread(target_url="http://127.0.0.1:59999/alarm/do")
    sender.start()

    alarm_payload = {
        "timestamp": int(time.time() * 1000),
        "beltID": 0,
        "distance": 6.2,
        "angle": 7.5,
        "picture": "base64string",
    }
    sender.put_alarm(alarm_payload)
    time.sleep(0.05)
    sender.stop()
    assert sender.alarm_queue.empty() or sender.isRunning() is False


def test_belt_monitor_alarm_display(qapp):
    cfg_path = os.path.join(current_dir, "conf", "config.yaml")
    form = MyBeltMonitorForm(0, cfgfile=cfg_path)
    form.processThread.stop()
    form.alarmSenderThread.stop()

    dummy_frame = np.zeros((200, 200, 3), dtype=np.uint8)
    org_frame = np.zeros((200, 200, 3), dtype=np.uint8)

    form.angle_alarm = 5.0
    form.dist_alarm = 5.0

    form.refresh_frame(dummy_frame, distance=1.0, degree=1.0, org_frame=org_frame)
    assert "正常" in form.label_tip.text()

    form.refresh_frame(dummy_frame, distance=6.0, degree=1.0, org_frame=org_frame)
    assert "偏移距离超限" in form.label_tip.text()

    form.refresh_frame(dummy_frame, distance=1.0, degree=6.0, org_frame=org_frame)
    assert "偏移角度超限" in form.label_tip.text()

    form.refresh_frame(dummy_frame, distance=6.0, degree=6.0, org_frame=org_frame)
    assert "偏移角度超限 偏移距离超限" in form.label_tip.text()

    form.stop_all()
    form.close()


def test_main_window_mdi_actions(qapp):
    logger = setup_logger()
    assert logger is not None
    assert os.path.exists("./log/belt_monitor.log")

    cfg_path = os.path.join(current_dir, "conf", "config.yaml")
    main_win = MainWindow(cfgfile=cfg_path)

    assert hasattr(main_win, "belt1_action")
    assert hasattr(main_win, "belt2_action")
    assert hasattr(main_win, "belt3_action")
    assert hasattr(main_win, "confBelt1Action")
    assert hasattr(main_win, "confBelt2Action")
    assert hasattr(main_win, "confBelt3Action")

    main_win.close()
