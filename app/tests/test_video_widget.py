import os
from PySide6.QtGui import QImage, QColor

from app.src.model import DetectionBox

os.environ["QT_QPA_PLATFORM"] = "offscreen"


def test_video_widget_set_frame_and_render():
    """测试 VideoWidget 能够正常接收帧数据并维护边界框"""
    from app.src.ui.components.video_widget import VideoWidget

    widget = VideoWidget()
    assert widget.current_frame is None

    # 创建一个 640x480 的测试 QImage
    img = QImage(640, 480, QImage.Format_RGB888)
    img.fill(QColor(255, 255, 255))

    det = DetectionBox(
        x1=100, y1=100, x2=200, y2=250,
        confidence=0.92, class_id=0, class_name="person",
        track_id=1, behavior_label="look_forward"
    )

    widget.update_frame(img, [det], fps=30.0)
    assert widget.current_frame is not None
    assert len(widget.detections) == 1
    assert widget.current_fps == 30.0


def test_control_bar_signals(qapp):
    """测试 ControlBar 的按钮与下拉框信号触发"""
    from app.src.ui.components.control_bar import ControlBar

    bar = ControlBar()
    
    play_states = []
    bar.play_toggled.connect(lambda s: play_states.append(s))
    
    # 模拟点击播放/暂停
    bar.btn_play.click()
    assert len(play_states) == 1
    assert play_states[0] is False  # 默认由 True -> False (暂停)
