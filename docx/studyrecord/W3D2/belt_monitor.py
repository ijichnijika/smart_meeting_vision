import os
import sys
import time
import queue
import base64
import logging
from enum import Enum
from typing import Optional, Dict, Any

import cv2
import numpy as np
import yaml
import requests
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLCDNumber,
    QPushButton,
    QFileDialog,
    QMessageBox,
)

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from alg import calculate_angle, get_border, mid_line, calculate_dist

logger = logging.getLogger('belt_logger')


class VideoSourceType(Enum):
    FILE = 0
    RTSP = 1
    USB = 2


def parse_video_source_type(url: Any) -> VideoSourceType:
    if isinstance(url, int):
        return VideoSourceType.USB
    url_str = str(url).strip()
    if url_str.isdigit():
        return VideoSourceType.USB
    if url_str.lower().startswith(('rtsp://', 'http://', 'https://')):
        return VideoSourceType.RTSP
    return VideoSourceType.FILE


class VideoEncodeProcess(QThread):
    def __init__(self, videoWriter: cv2.VideoWriter):
        super().__init__()
        self.videoWriter = videoWriter
        self.frame_queue: queue.Queue = queue.Queue(maxsize=120)
        self.running = True

    def run(self):
        logger.info('VideoEncodeProcess started.')
        while self.running:
            try:
                frame = self.frame_queue.get_nowait()
                self.videoWriter.write(frame)
            except queue.Empty:
                self.msleep(5)
            except Exception as e:
                logger.error(f'Video encode error: {e}')
                break

        try:
            while not self.frame_queue.empty():
                frame = self.frame_queue.get_nowait()
                self.videoWriter.write(frame)
        except Exception:
            pass

        self.videoWriter.release()
        logger.info('VideoEncodeProcess finished and writer released.')

    def stop(self):
        self.running = False
        self.wait()

    def put(self, frame: np.ndarray):
        try:
            self.frame_queue.put_nowait(frame)
        except queue.Full:
            logger.warning('Video encode frame queue full, frame dropped.')


class AlarmSenderThread(QThread):
    def __init__(self, target_url: str = 'http://localhost:5000/alarm/do'):
        super().__init__()
        self.target_url = target_url
        self.alarm_queue: queue.Queue = queue.Queue(maxsize=100)
        self.running = True

    def put_alarm(self, alarm_data: dict):
        try:
            self.alarm_queue.put_nowait(alarm_data)
        except queue.Full:
            logger.warning('Alarm queue full, alarm dropped.')

    def run(self):
        logger.info('AlarmSenderThread started.')
        while self.running:
            try:
                data = self.alarm_queue.get_nowait()
                self._send_http(data)
            except queue.Empty:
                self.msleep(50)
            except Exception as e:
                logger.error(f'Alarm sender exception: {e}')
        logger.info('AlarmSenderThread stopped.')

    def _send_http(self, data: dict):
        try:
            resp = requests.post(
                self.target_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=1.5,
            )
            logger.info(f'Alarm sent. Status: {resp.status_code}')
        except Exception as err:
            logger.warning(f'Failed to report alarm to server: {err}')

    def stop(self):
        self.running = False
        self.wait()


class MyBeltProcess(QThread):
    done_signal = Signal(np.ndarray, float, float, np.ndarray)
    error_signal = Signal(str)

    def __init__(self, beltID: int, cfg: dict, alarm_sender: Optional[AlarmSenderThread] = None):
        super().__init__()
        self.beltID = beltID
        self.beltID_str = f'belt_{beltID}'
        self.cfg = cfg
        self.alarm_sender = alarm_sender
        self.runFlag = True

        self.logger = logging.getLogger('belt_logger')

        belt_conf = self.cfg.get(self.beltID_str, {})
        self.url = belt_conf.get('url', './video/test.mp4')
        self.source_type = parse_video_source_type(self.url)

        self.border_left = belt_conf.get('border_left', [[580, 422], [342, 967]])
        self.border_right = belt_conf.get('border_right', [[929, 438], [1152, 1009]])
        self.belt_width = float(belt_conf.get('belt_width', 180))
        self.angle_alarm = float(belt_conf.get('angle_alarm', 5.0))
        self.dist_alarm = float(belt_conf.get('dist_alarm', 5.0))

        self.model = None
        self._init_model()

        self._last_alarm_report_time = 0.0

    def _init_model(self):
        model_paths = [
            'W2D1/models/best.pt',
            os.path.join(current_dir, '..', '..', 'W2D1', 'models', 'best.pt'),
            os.path.join(current_dir, '..', 'W2D1', 'models', 'best.pt'),
        ]
        for mp in model_paths:
            if os.path.exists(mp):
                try:
                    from ultralytics import YOLO
                    self.logger.info(f'Loading YOLO model from {mp}...')
                    self.model = YOLO(mp)
                    self.logger.info('YOLO model loaded successfully.')
                    return
                except Exception as e:
                    self.logger.warning(f'Could not load YOLO model: {e}')
                    break

    def stop(self):
        self.runFlag = False
        self.wait()

    def _open_capture(self) -> Optional[cv2.VideoCapture]:
        actual_source = int(self.url) if self.source_type == VideoSourceType.USB else self.url
        cap = cv2.VideoCapture(actual_source)
        return cap if cap.isOpened() else None

    def run(self):
        self.logger.info(f'MyBeltProcess started for {self.beltID_str}, source: {self.url}')
        cap = self._open_capture()

        sim_step = 0.0

        while self.runFlag:
            frame = None
            if cap is not None and cap.isOpened():
                success, frame = cap.read()
                if not success:
                    if self.source_type == VideoSourceType.FILE:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        success, frame = cap.read()
                    else:
                        self.error_signal.emit(f'{self.beltID_str} 视频流中断，尝试重连...')
                        self.logger.error(f'Read frame error on {self.beltID_str}, reconnecting...')
                        cap.release()
                        time.sleep(1.0)
                        cap = self._open_capture()
                        continue

            if frame is None:
                frame = np.full((480, 640, 3), 35, dtype=np.uint8)
                cx = int(320 + np.sin(sim_step) * 35)
                cv2.rectangle(frame, (cx - 120, 80), (cx + 120, 400), (60, 60, 60), -1)
                cv2.line(frame, (cx - 120, 80), (cx - 120, 400), (0, 255, 0), 2)
                cv2.line(frame, (cx + 120, 80), (cx + 120, 400), (0, 255, 0), 2)
                sim_step += 0.08
                distance = round(self.dist_alarm * 0.5 + float(np.sin(sim_step)) * 3.5, 2)
                degree = round(self.angle_alarm * 0.4 + float(np.cos(sim_step)) * 3.0, 2)
                org_frame = frame.copy()
            else:
                org_frame = frame.copy()
                distance, degree = 0.0, 0.0
                if self.model is not None:
                    try:
                        results = self.model.predict(frame, conf=0.25, verbose=False)
                        if results and results[0].masks is not None and len(results[0].masks.xy) > 0:
                            pixel_coords = results[0].masks.xy[0]
                            pts = np.asarray(pixel_coords, dtype=np.int32)
                            keypts = cv2.approxPolyDP(pts, 10, True)
                            cv2.drawContours(frame, [keypts], 0, (0, 0, 255), 1)

                            p_l0 = tuple(self.border_left[0])
                            p_l1 = tuple(self.border_left[1])
                            p_r0 = tuple(self.border_right[0])
                            p_r1 = tuple(self.border_right[1])

                            r_left, r_right = get_border(keypts, p_l0, p_l1, p_r0, p_r1, min_length=150)
                            if r_left is not None and r_right is not None:
                                reco_mid = mid_line(r_left, r_right)
                                org_mid = mid_line((p_l0, p_l1), (p_r0, p_r1))
                                if reco_mid[0] and reco_mid[1] and org_mid[0] and org_mid[1]:
                                    degree = round(float(calculate_angle(org_mid, reco_mid)), 2)
                                    distance = round(float(calculate_dist(org_mid, reco_mid, (p_l0, p_l1), (p_r0, p_r1), self.belt_width)), 2)
                    except Exception as err:
                        self.logger.warning(f'YOLO infer exception: {err}')
                else:
                    sim_step += 0.05
                    distance = round(float(np.sin(sim_step)) * 6.0, 2)
                    degree = round(float(np.cos(sim_step)) * 6.5, 2)

            is_alarm = (abs(distance) > self.dist_alarm) or (abs(degree) > self.angle_alarm)
            if is_alarm:
                now = time.time()
                if now - self._last_alarm_report_time > 2.0 and self.alarm_sender is not None:
                    self._last_alarm_report_time = now
                    _, encoded_buf = cv2.imencode('.jpg', org_frame)
                    pic_b64 = base64.b64encode(encoded_buf).decode('utf-8')
                    alarm_dict = {
                        'timestamp': int(now * 1000),
                        'beltID': self.beltID,
                        'distance': distance,
                        'angle': degree,
                        'picture': pic_b64,
                    }
                    self.alarm_sender.put_alarm(alarm_dict)

            cv2.putText(
                frame,
                f'Dist: {distance:+.2f}mm  Deg: {degree:+.2f}deg',
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255) if is_alarm else (0, 255, 0),
                2,
            )

            self.done_signal.emit(frame, distance, degree, org_frame)
            self.msleep(40)

        if cap is not None:
            cap.release()
        self.logger.info(f'MyBeltProcess terminated for {self.beltID_str}')


class MyBeltMonitorForm(QWidget):
    def __init__(self, beltID: int, cfgfile: str = './conf/config.yaml', parent=None):
        super().__init__(parent)
        self.beltID = beltID
        self.beltID_str = f'belt_{beltID}'
        self.cfgfile = cfgfile
        self.cfg = {}
        self._load_config()

        self.org_frame: Optional[np.ndarray] = None
        self.writeVideo = False
        self.videoEncodeThread: Optional[VideoEncodeProcess] = None
        self.alarmSenderThread: Optional[AlarmSenderThread] = None

        self._init_ui()
        self._start_threads()

    def _load_config(self):
        if os.path.exists(self.cfgfile):
            with open(self.cfgfile, 'r', encoding='utf-8') as f:
                self.cfg = yaml.safe_load(f) or {}

        belt_conf = self.cfg.get(self.beltID_str, {})
        self.angle_alarm = float(belt_conf.get('angle_alarm', 5.0))
        self.dist_alarm = float(belt_conf.get('dist_alarm', 5.0))

    def _init_ui(self):
        self.setWindowTitle(f'皮带监控 - {self.beltID_str}')
        self.resize(760, 560)

        main_layout = QVBoxLayout(self)

        self.label_img = QLabel('视频监控画面', self)
        self.label_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_img.setStyleSheet('background-color: #000; color: #aaa; border: 1px solid #333;')
        self.label_img.setMinimumSize(480, 320)
        main_layout.addWidget(self.label_img, 1)

        data_layout = QHBoxLayout()
        data_layout.addWidget(QLabel('偏移角度:'))
        self.lcdNumber_angle = QLCDNumber(self)
        self.lcdNumber_angle.setDigitCount(5)
        data_layout.addWidget(self.lcdNumber_angle)

        data_layout.addWidget(QLabel('偏移距离:'))
        self.lcdNumber_distance = QLCDNumber(self)
        self.lcdNumber_distance.setDigitCount(5)
        data_layout.addWidget(self.lcdNumber_distance)

        self.label_tip = QLabel('提示：运行正常', self)
        self.label_tip.setStyleSheet('color: green; font-weight: bold;')
        data_layout.addWidget(self.label_tip)
        data_layout.addStretch()
        main_layout.addLayout(data_layout)

        btn_layout = QHBoxLayout()
        self.pushButton_savevideo = QPushButton('保存视频', self)
        self.pushButton_snapshot = QPushButton('保存快照', self)
        self.pushButton_openvideo = QPushButton('打开视频', self)

        btn_layout.addWidget(self.pushButton_savevideo)
        btn_layout.addWidget(self.pushButton_snapshot)
        btn_layout.addWidget(self.pushButton_openvideo)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.pushButton_savevideo.clicked.connect(self.startWriteVideo)
        self.pushButton_snapshot.clicked.connect(self.writeSnapshot)
        self.pushButton_openvideo.clicked.connect(self.openVideoFile)

    def _start_threads(self):
        self.alarmSenderThread = AlarmSenderThread()
        self.alarmSenderThread.start()

        self.processThread = MyBeltProcess(self.beltID, self.cfg, self.alarmSenderThread)
        self.processThread.done_signal.connect(self.refresh_frame)
        self.processThread.error_signal.connect(self.on_process_error)
        self.processThread.start()

    def refresh_frame(self, frame: np.ndarray, distance: float, degree: float, org_frame: np.ndarray):
        self.org_frame = org_frame.copy()

        if self.writeVideo and self.videoEncodeThread:
            self.videoEncodeThread.put(self.org_frame)

        h, w, ch = frame.shape
        q_img = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(
            self.label_img.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.label_img.setPixmap(scaled_pixmap)

        self.lcdNumber_angle.display(f'{degree:.2f}')
        self.lcdNumber_distance.display(f'{distance:.2f}')

        is_angle_exceed = abs(degree) > self.angle_alarm
        is_dist_exceed = abs(distance) > self.dist_alarm

        if is_angle_exceed and is_dist_exceed:
            self.label_tip.setText('提示：偏移角度超限 偏移距离超限')
            self.label_tip.setStyleSheet('color: red; font-weight: bold;')
        elif is_angle_exceed:
            self.label_tip.setText('提示：偏移角度超限')
            self.label_tip.setStyleSheet('color: red; font-weight: bold;')
        elif is_dist_exceed:
            self.label_tip.setText('提示：偏移距离超限')
            self.label_tip.setStyleSheet('color: red; font-weight: bold;')
        else:
            self.label_tip.setText('提示：运行正常')
            self.label_tip.setStyleSheet('color: green; font-weight: bold;')

    def writeSnapshot(self):
        if self.org_frame is None:
            QMessageBox.warning(self, '提示', '暂无有效图像帧可保存')
            return

        os.makedirs('./snapshot', exist_ok=True)
        timestamp_ms = int(time.time() * 1000)
        save_path = f'./snapshot/belt_{self.beltID}_{timestamp_ms}.jpg'
        cv2.imwrite(save_path, self.org_frame)
        logger.info(f'Snapshot saved: {save_path}')
        QMessageBox.information(self, '快照提示', f'快照已保存至: {save_path}')

    def startWriteVideo(self):
        if self.writeVideo:
            self.writeVideo = False
            if self.videoEncodeThread is not None:
                self.videoEncodeThread.stop()
                self.videoEncodeThread = None
            self.pushButton_savevideo.setText('保存视频')
            logger.info(f'{self.beltID_str} 视频录制结束')
            return

        path, _ = QFileDialog.getSaveFileName(self, '保存视频', './video/', 'Video Files (*.avi);;All Files (*.*)')
        if not path:
            return

        h, w = (self.org_frame.shape[0], self.org_frame.shape[1]) if self.org_frame is not None else (720, 1280)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        cap_writer = cv2.VideoWriter(path, fourcc, 20.0, (w, h))

        if not cap_writer.isOpened():
            QMessageBox.warning(self, '错误', '无法创建视频写入器')
            return

        self.videoEncodeThread = VideoEncodeProcess(cap_writer)
        self.videoEncodeThread.start()
        self.writeVideo = True
        self.pushButton_savevideo.setText('停止保存')
        logger.info(f'{self.beltID_str} 开始保存视频: {path}')

    def openVideoFile(self):
        path, _ = QFileDialog.getOpenFileName(self, '打开视频文件', './video', 'Video Files (*.mp4 *.avi *.mkv)')
        if not path:
            return

        logger.info(f'Switching video source to: {path}')
        if hasattr(self, 'processThread') and self.processThread.isRunning():
            self.processThread.stop()

        self.cfg[self.beltID_str]['url'] = path
        self.processThread = MyBeltProcess(self.beltID, self.cfg, self.alarmSenderThread)
        self.processThread.done_signal.connect(self.refresh_frame)
        self.processThread.error_signal.connect(self.on_process_error)
        self.processThread.start()

    def on_process_error(self, err_msg: str):
        logger.error(err_msg)
        self.label_tip.setText(f'异常：{err_msg}')
        self.label_tip.setStyleSheet('color: orange; font-weight: bold;')

    def stop_all(self):
        if self.writeVideo and self.videoEncodeThread:
            self.writeVideo = False
            self.videoEncodeThread.stop()
        if hasattr(self, 'processThread') and self.processThread.isRunning():
            self.processThread.stop()
        if self.alarmSenderThread and self.alarmSenderThread.isRunning():
            self.alarmSenderThread.stop()

    def closeEvent(self, event):
        self.stop_all()
        event.accept()
