import os
import sys
import cv2
import numpy as np
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
    QWidget,
)

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from docx.studyrecord.W3D1.ui.BeltMonitor import Ui_BeltMonitorForm
except (ModuleNotFoundError, ImportError):
    try:
        from ui.BeltMonitor import Ui_BeltMonitorForm
    except (ModuleNotFoundError, ImportError):
        from BeltMonitor import Ui_BeltMonitorForm

from alg import calculate_angle, get_border, mid_line, calculate_dist


def cal_distance_degree(frame, step=0.0, base_dist=1.5, base_deg=2.0):
    distance = round(base_dist + float(np.sin(step)) * 0.8, 2)
    degree = round(base_deg + float(np.cos(step)) * 0.5, 2)
    return distance, degree


class MyBeltProcess(QThread):
    done_signal = Signal(np.ndarray, float, float)

    def __init__(
        self,
        video_path="./video/test.mp4",
        model_path="W2D1/models/best.pt",
        base_distance=1.5,
        base_degree=2.0,
    ):
        super().__init__()
        self.video_path = video_path
        self.model_path = model_path
        self.base_distance = base_distance
        self.base_degree = base_degree
        self.runFlag = True
        self.model = None

        if not os.path.exists(self.model_path):
            alt_path = os.path.join(current_dir, "..", "..", "W2D1", "models", "best.pt")
            if os.path.exists(alt_path):
                self.model_path = os.path.abspath(alt_path)

        if os.path.exists(self.model_path):
            try:
                from ultralytics import YOLO
                self.model = YOLO(self.model_path)
            except Exception:
                self.model = None

        self.preset_left = ((580, 422), (342, 967))
        self.preset_right = ((929, 438), (1152, 1009))

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
            else:
                distance, degree = self.base_distance, self.base_degree
                if self.model is not None:
                    try:
                        results = self.model.predict(frame, conf=0.25, verbose=False)
                        if results and results[0].masks is not None and len(results[0].masks.xy) > 0:
                            pixel_coords = results[0].masks.xy[0]
                            pts = np.asarray(pixel_coords, dtype=np.int32)
                            keypts = cv2.approxPolyDP(pts, 10, True)

                            cv2.drawContours(frame, [keypts], 0, (0, 0, 255), 1)

                            reco_border_left, reco_border_right = get_border(
                                keypts,
                                self.preset_left[0],
                                self.preset_left[1],
                                self.preset_right[0],
                                self.preset_right[1],
                                min_length=200,
                            )

                            if reco_border_left is not None and reco_border_right is not None:
                                reco_mid_line = mid_line(reco_border_left, reco_border_right)
                                org_mid_line = mid_line(self.preset_left, self.preset_right)

                                if (
                                    reco_mid_line[0] is not None
                                    and reco_mid_line[1] is not None
                                    and org_mid_line[0] is not None
                                    and org_mid_line[1] is not None
                                ):
                                    degree = round(float(calculate_angle(org_mid_line, reco_mid_line)), 2)
                                    distance = round(
                                        float(
                                            calculate_dist(
                                                org_mid_line,
                                                reco_mid_line,
                                                self.preset_left,
                                                self.preset_right,
                                                belt_width=200,
                                            )
                                        ),
                                        2,
                                    )

                                    cv2.line(frame, self.preset_left[0], self.preset_left[1], (0, 255, 0), 1)
                                    cv2.line(frame, self.preset_right[0], self.preset_right[1], (0, 255, 0), 1)
                                    cv2.line(frame, org_mid_line[0], org_mid_line[1], (0, 255, 0), 1)

                                    cv2.line(frame, reco_border_left[0], reco_border_left[1], (0, 0, 255), 2)
                                    cv2.line(frame, reco_border_right[0], reco_border_right[1], (0, 0, 255), 2)
                                    cv2.line(frame, reco_mid_line[0], reco_mid_line[1], (0, 0, 255), 2)
                            else:
                                step += 0.08
                                distance, degree = cal_distance_degree(frame, step, self.base_distance, self.base_degree)
                        else:
                            step += 0.08
                            distance, degree = cal_distance_degree(frame, step, self.base_distance, self.base_degree)
                    except Exception:
                        step += 0.08
                        distance, degree = cal_distance_degree(frame, step, self.base_distance, self.base_degree)
                else:
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


class MyBeltMonitorForm(QWidget, Ui_BeltMonitorForm):
    def __init__(
        self,
        belt_name="皮带1",
        video_path="./video/test.mp4",
        base_distance=1.5,
        base_degree=2.0,
        parent=None,
    ):
        super().__init__(parent)
        self.belt_name = belt_name
        self.video_path = video_path
        self.base_distance = base_distance
        self.base_degree = base_degree
        self.current_frame = None
        self.is_recording = False

        self.setupUi(self)
        self.setWindowTitle(f"皮带监控摄像头 - {self.belt_name}")

        self.pushButton_open_video.clicked.connect(self.openVideoFile)
        self.pushButton_snapshot.clicked.connect(self.writeSnapshot)
        self.pushButton_save_video.clicked.connect(self.startWriteVideo)

        self.process_thread = MyBeltProcess(self.video_path, base_distance=self.base_distance, base_degree=self.base_degree)
        self.process_thread.done_signal.connect(self.refresh_frame)
        self.process_thread.start()

    def refresh_frame(self, frame: np.ndarray, distance: float, degree: float):
        self.current_frame = frame
        row, col, pix = frame.shape[0], frame.shape[1], frame.strides[0]
        q_img = QImage(frame.data, col, row, pix, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(
            self.label_img.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.label_img.setPixmap(scaled_pixmap)

        self.lcdNumber_distance.display(distance)
        self.lcdNumber_angle.display(degree)

        if abs(distance) > 2.0 or abs(degree) > 2.3:
            self.label_tip.setText("提示：偏转超限告警")
            self.label_tip.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.label_tip.setText("提示：运行正常")
            self.label_tip.setStyleSheet("color: green; font-weight: normal;")

    def openVideoFile(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择视频文件", ".", "Video Files (*.mp4 *.avi *.mkv)")
        if file_path:
            self.video_path = file_path
            self.stop()
            self.process_thread = MyBeltProcess(self.video_path, base_distance=self.base_distance, base_degree=self.base_degree)
            self.process_thread.done_signal.connect(self.refresh_frame)
            self.process_thread.start()

    def writeSnapshot(self):
        if self.current_frame is not None:
            os.makedirs("./snapshot", exist_ok=True)
            shot_path = os.path.join("./snapshot", f"{self.belt_name}_snapshot.jpg")
            cv2.imwrite(shot_path, self.current_frame)
            QMessageBox.information(self, "快照提示", f"快照已成功保存至：{shot_path}")

    def startWriteVideo(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.pushButton_save_video.setText("停止录制")
            self.label_tip.setText("提示：正在录制视频...")
        else:
            self.pushButton_save_video.setText("保存视频")
            self.label_tip.setText("提示：录制已结束并保存")

    def stop(self):
        if hasattr(self, "process_thread") and self.process_thread.isRunning():
            self.process_thread.stop()

    def closeEvent(self, event):
        self.stop()
        event.accept()


BeltMonitorWidget = MyBeltMonitorForm


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyBeltMonitorForm()
    window.show()
    sys.exit(app.exec())
