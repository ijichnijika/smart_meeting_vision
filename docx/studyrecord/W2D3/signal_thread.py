import os
import sys
import cv2
import numpy as np
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)


def cal_distance_degree(frame, step=0.0, base_dist=1.5, base_deg=2.0):
    distance = round(base_dist + float(np.sin(step)) * 0.8, 2)
    degree = round(base_deg + float(np.cos(step)) * 0.5, 2)
    return distance, degree


class MyBeltProcess(QThread):
    done_signal = Signal(np.ndarray, float, float)

    def __init__(self, video_path="./video/test.mp4", base_distance=1.5, base_degree=2.0):
        super().__init__()
        self.video_path = video_path
        self.base_distance = base_distance
        self.base_degree = base_degree
        self.runFlag = True

    def stop(self):
        self.runFlag = False
        self.wait()

    def run(self):
        cap = None
        if os.path.exists(self.video_path):
            cap = cv2.VideoCapture(self.video_path)

        step = 0.0
        while self.runFlag:
            frame = None
            if cap is not None and cap.isOpened():
                success, frame = cap.read()
                if not success:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    success, frame = cap.read()

            if frame is None:
                frame = np.full((480, 640, 3), 40, dtype=np.uint8)
                cx = int(320 + np.sin(step) * 40)
                cv2.rectangle(frame, (cx - 120, 80), (cx + 120, 400), (70, 70, 70), -1)
                cv2.line(frame, (cx - 120, 80), (cx - 120, 400), (0, 255, 0), 2)
                cv2.line(frame, (cx + 120, 80), (cx + 120, 400), (0, 255, 0), 2)

            step += 0.08
            distance, degree = cal_distance_degree(frame, step, self.base_distance, self.base_degree)

            cv2.putText(
                frame,
                f"Dist: {distance:+.2f}mm  Deg: {degree:+.2f}deg",
                (30, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

            self.done_signal.emit(frame, distance, degree)
            QThread.msleep(int(1000 / 25))

        if cap is not None:
            cap.release()


class BeltMonitorWidget(QWidget):
    def __init__(self, belt_name="皮带1", video_path="./video/test.mp4", base_distance=1.5, base_degree=2.0, parent=None):
        super().__init__(parent)
        self.belt_name = belt_name
        self.video_path = video_path

        self.label_img = QLabel("等待视频流接入...", self)
        self.label_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_img.setStyleSheet("background-color: #1a1a1a; color: #888888; border: 1px solid #333333;")
        self.label_img.setMinimumSize(480, 320)

        self.label_distance_tip = QLabel("偏移距离:", self)
        self.label_distance_tip.setStyleSheet("font-weight: bold; font-size: 13px;")

        self.edit_distance = QLineEdit(self)
        self.edit_distance.setReadOnly(True)
        self.edit_distance.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_distance.setPlaceholderText("0.00 mm")
        self.edit_distance.setStyleSheet("font-size: 13px; font-weight: bold; padding: 3px;")

        self.label_degree_tip = QLabel("偏移角度:", self)
        self.label_degree_tip.setStyleSheet("font-weight: bold; font-size: 13px;")

        self.edit_degree = QLineEdit(self)
        self.edit_degree.setReadOnly(True)
        self.edit_degree.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_degree.setPlaceholderText("0.00 °")
        self.edit_degree.setStyleSheet("font-size: 13px; font-weight: bold; padding: 3px;")

        param_layout = QHBoxLayout()
        param_layout.addWidget(self.label_distance_tip)
        param_layout.addWidget(self.edit_distance)
        param_layout.addSpacing(20)
        param_layout.addWidget(self.label_degree_tip)
        param_layout.addWidget(self.edit_degree)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.addWidget(self.label_img, stretch=1)
        main_layout.addLayout(param_layout)

        self.process_thread = MyBeltProcess(self.video_path, base_distance, base_degree)
        self.process_thread.done_signal.connect(self.refresh_frame)
        self.process_thread.start()

    def refresh_frame(self, frame: np.ndarray, distance: float, angle: float):
        row, col, pix = frame.shape[0], frame.shape[1], frame.strides[0]
        q_img = QImage(frame.data, col, row, pix, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(
            self.label_img.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.label_img.setPixmap(scaled_pixmap)

        self.edit_distance.setText(f"{distance:+.2f} mm")
        self.edit_degree.setText(f"{angle:+.2f} °")

    def stop(self):
        if hasattr(self, "process_thread") and self.process_thread.isRunning():
            self.process_thread.stop()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("皮带偏移识别监控")
        self.resize(800, 600)

        self.monitor_widget = BeltMonitorWidget("皮带1", "./video/test.mp4")
        self.setCentralWidget(self.monitor_widget)

        self.label_img = self.monitor_widget.label_img
        self.label_distance_tip = self.monitor_widget.label_distance_tip
        self.edit_distance = self.monitor_widget.edit_distance
        self.label_degree_tip = self.monitor_widget.label_degree_tip
        self.edit_degree = self.monitor_widget.edit_degree
        self.processThread = self.monitor_widget.process_thread

    def refreshFrame(self, frame: np.ndarray, distance: float, angle: float):
        self.monitor_widget.refresh_frame(frame, distance, angle)

    def closeEvent(self, event):
        self.monitor_widget.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
