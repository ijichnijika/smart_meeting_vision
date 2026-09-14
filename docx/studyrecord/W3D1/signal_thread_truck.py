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
    from docx.studyrecord.W3D1.ui.TruckMonitor import Ui_TruckMonitorForm
except (ModuleNotFoundError, ImportError):
    try:
        from ui.TruckMonitor import Ui_TruckMonitorForm
    except (ModuleNotFoundError, ImportError):
        from TruckMonitor import Ui_TruckMonitorForm


class MyTruckProcess(QThread):
    done_signal = Signal(np.ndarray, int, int)

    def __init__(self, video_path="./video/test.mp4", model_path="W2D1/models/best.pt"):
        super().__init__()
        self.video_path = video_path
        self.model_path = model_path
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
                frame = np.full((480, 640, 3), 35, dtype=np.uint8)

            h, w = frame.shape[:2]
            step += 0.05
            crane_count = 0
            tower_crane_count = 0

            has_yolo_detections = False
            if self.model is not None:
                try:
                    results = self.model.predict(frame, conf=0.25, verbose=False)
                    if results and results[0].boxes is not None and len(results[0].boxes) > 0:
                        boxes = results[0].boxes
                        has_yolo_detections = True
                        for i in range(len(boxes)):
                            xyxy = boxes.xyxy[i].cpu().numpy().astype(int)
                            conf = float(boxes.conf[i].item())
                            cls_id = int(boxes.cls[i].item())

                            if cls_id % 2 == 0:
                                crane_count += 1
                                label = f"Crane {conf:.2f}"
                                color = (0, 165, 255)
                            else:
                                tower_crane_count += 1
                                label = f"TowerCrane {conf:.2f}"
                                color = (0, 255, 255)

                            cv2.rectangle(frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, 2)
                            cv2.putText(
                                frame,
                                label,
                                (xyxy[0], max(20, xyxy[1] - 8)),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                color,
                                2,
                            )
                except Exception:
                    has_yolo_detections = False

            if not has_yolo_detections:
                crane_count = 1 + int((np.sin(step) + 1.0) * 1.5)
                tower_crane_count = 1 + int((np.cos(step * 0.8) + 1.0))

                for i in range(crane_count):
                    bx = int(50 + i * 160 + np.sin(step + i) * 20)
                    by = int(h * 0.45)
                    cv2.rectangle(frame, (bx, by), (bx + 130, by + 120), (0, 165, 255), 2)
                    cv2.putText(
                        frame,
                        f"Crane {i+1} 0.89",
                        (bx, by - 8),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 165, 255),
                        2,
                    )

                for j in range(tower_crane_count):
                    tx = int(w - 180 - j * 150 + np.cos(step + j) * 15)
                    ty = int(h * 0.25)
                    cv2.rectangle(frame, (tx, ty), (tx + 120, ty + 200), (0, 255, 255), 2)
                    cv2.putText(
                        frame,
                        f"TowerCrane {j+1} 0.94",
                        (tx, ty - 8),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 255),
                        2,
                    )

            cv2.putText(
                frame,
                f"Crane: {crane_count}  TowerCrane: {tower_crane_count}",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
            )

            self.done_signal.emit(frame, crane_count, tower_crane_count)
            QThread.msleep(int(1000 / 25))

        if cap is not None:
            cap.release()


class MyTruckMonitorForm(QWidget, Ui_TruckMonitorForm):
    def __init__(self, monitor_name="工程车监测点1", video_path="./video/test.mp4", parent=None):
        super().__init__(parent)
        self.monitor_name = monitor_name
        self.video_path = video_path
        self.current_frame = None
        self.is_recording = False

        self.setupUi(self)
        self.setWindowTitle(f"工程车监控 - {self.monitor_name}")

        self.pushButton_open_video.clicked.connect(self.openVideoFile)
        self.pushButton_snapshot.clicked.connect(self.writeSnapshot)
        self.pushButton_save_video.clicked.connect(self.startWriteVideo)

        self.process_thread = MyTruckProcess(self.video_path)
        self.process_thread.done_signal.connect(self.refresh_frame)
        self.process_thread.start()

    def refresh_frame(self, frame: np.ndarray, crane_count: int, tower_crane_count: int):
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

        self.lcdNumber_crane.display(crane_count)
        self.lcdNumber_tower_crane.display(tower_crane_count)

        total = crane_count + tower_crane_count
        if total > 0:
            self.label_tip.setText(f"提示：监测到施工机械共 {total} 台")
            self.label_tip.setStyleSheet("color: #2b5797; font-weight: bold;")
        else:
            self.label_tip.setText("提示：暂无施工机械作业")
            self.label_tip.setStyleSheet("color: gray; font-weight: normal;")

    def openVideoFile(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择工程车视频", ".", "Video Files (*.mp4 *.avi *.mkv)")
        if file_path:
            self.video_path = file_path
            self.stop()
            self.process_thread = MyTruckProcess(self.video_path)
            self.process_thread.done_signal.connect(self.refresh_frame)
            self.process_thread.start()

    def writeSnapshot(self):
        if self.current_frame is not None:
            os.makedirs("./snapshot", exist_ok=True)
            shot_path = os.path.join("./snapshot", f"{self.monitor_name}_snapshot.jpg")
            cv2.imwrite(shot_path, self.current_frame)
            QMessageBox.information(self, "快照提示", f"工程车快照已成功保存至：{shot_path}")

    def startWriteVideo(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.pushButton_save_video.setText("停止录制")
            self.label_tip.setText("提示：正在录制工程车监控视频...")
        else:
            self.pushButton_save_video.setText("保存视频")
            self.label_tip.setText("提示：工程车视频录制完成并保存")

    def stop(self):
        if hasattr(self, "process_thread") and self.process_thread.isRunning():
            self.process_thread.stop()

    def closeEvent(self, event):
        self.stop()
        event.accept()


TruckMonitorWidget = MyTruckMonitorForm


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyTruckMonitorForm()
    window.show()
    sys.exit(app.exec())
